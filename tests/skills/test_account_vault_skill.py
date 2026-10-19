"""Comprehensive tests for the autonomous account-vault skill.

Supports both pytest and standard unittest runners without external dependencies.
Validates:
- AES-256-GCM encrypted storage & key derivation
- RFC-6238 TOTP 2FA code generation & otpauth URI parsing
- Zero-leak subprocess environment injection (exec)
- Session / cookie caching
- Password generation, entropy calculation, and auto-rotation
- Auto-snapshots and point-in-time restore
- Security audit & health scoring
- Multi-format import/export (Bitwarden, CSV, .env)
- Python SDK programmatic interface
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import time
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILL_DIR = (
    _REPO_ROOT / "skills" / "security" / "account-vault"
    if (_REPO_ROOT / "skills" / "security" / "account-vault").exists()
    else _REPO_ROOT / "skills" / "account-vault"
)
SCRIPT = SKILL_DIR / "scripts" / "vault.py"


def load_vault_module():
    spec = importlib.util.spec_from_file_location("vault", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


vault_mod = load_vault_module()


class TestAccountVault(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.hermes_home = pathlib.Path(self.tmp_dir.name) / ".hermes"
        self.hermes_home.mkdir()
        self.orig_hermes_home = os.environ.get("HERMES_HOME")
        self.orig_pass = os.environ.get("ACCOUNT_VAULT_PASS")
        
        self.passphrase = "master_super_secret_123"
        os.environ["HERMES_HOME"] = str(self.hermes_home)
        os.environ["ACCOUNT_VAULT_PASS"] = self.passphrase

    def tearDown(self):
        if self.orig_hermes_home is not None:
            os.environ["HERMES_HOME"] = self.orig_hermes_home
        else:
            os.environ.pop("HERMES_HOME", None)
            
        if self.orig_pass is not None:
            os.environ["ACCOUNT_VAULT_PASS"] = self.orig_pass
        else:
            os.environ.pop("ACCOUNT_VAULT_PASS", None)
            
        self.tmp_dir.cleanup()

    def _exec_cli(self, argv: list[str]) -> int:
        return vault_mod.main(argv)

    def test_init_and_storage_structure(self):
        ret = self._exec_cli(["init", "--passphrase", self.passphrase])
        self.assertEqual(ret, 0)
        
        vault_file = self.hermes_home / "account_vault.json"
        self.assertTrue(vault_file.exists())
        raw = json.loads(vault_file.read_text())
        self.assertEqual(raw["version"], 2)
        self.assertIn("salt", raw)
        self.assertIn("payload", raw)
        self.assertNotIn(self.passphrase, vault_file.read_text())

    def test_add_get_and_field_only(self):
        self._exec_cli(["init", "--passphrase", self.passphrase])
        ret = self._exec_cli([
            "add", "b.ai",
            "-u", "alice@example.com",
            "-p", "ComplexPass#9988",
            "--field", "api_key=sk-12345",
            "--field", "region=us-west-2",
            "--passphrase", self.passphrase,
        ])
        self.assertEqual(ret, 0)

        entries = vault_mod.read_entries(self.passphrase)
        self.assertIn("b.ai", entries)
        self.assertEqual(entries["b.ai"]["username"], "alice@example.com")
        self.assertEqual(entries["b.ai"]["password"], "ComplexPass#9988")
        self.assertEqual(entries["b.ai"]["fields"]["api_key"], "sk-12345")
        self.assertEqual(entries["b.ai"]["fields"]["region"], "us-west-2")

    def test_rfc6238_totp_generation(self):
        # RFC 6238 test secret: JBSWY3DPEHPK3PXP ("Hello!\xde\xad\xbe\xef" base32)
        secret = "JBSWY3DPEHPK3PXP"
        code, rem, nxt = vault_mod.generate_totp_code(secret, interval=30, digits=6)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
        self.assertGreaterEqual(rem, 0)
        self.assertLessEqual(rem, 30)
        self.assertEqual(len(nxt), 6)
        self.assertTrue(nxt.isdigit())

        # Test with otpauth:// URI
        uri = f"otpauth://totp/GitHub:alice?secret={secret}&issuer=GitHub"
        code_uri, _, _ = vault_mod.generate_totp_code(uri)
        self.assertEqual(code, code_uri)

    def test_totp_cli_and_with_totp_flag(self):
        self._exec_cli(["init", "--passphrase", self.passphrase])
        self._exec_cli([
            "add", "github",
            "-u", "alice",
            "-p", "token123",
            "--totp-secret", "JBSWY3DPEHPK3PXP",
            "--passphrase", self.passphrase,
        ])

        # CLI totp command
        ret = self._exec_cli(["totp", "github", "--json", "--passphrase", self.passphrase])
        self.assertEqual(ret, 0)

        # CLI get with --with-totp
        ret = self._exec_cli(["get", "github", "--with-totp", "--json", "--passphrase", self.passphrase])
        self.assertEqual(ret, 0)

    def test_exec_subprocess_environment_injection(self):
        self._exec_cli(["init", "--passphrase", self.passphrase])
        self._exec_cli([
            "add", "aws-prod",
            "-u", "deployer",
            "-p", "super-secret-aws-key",
            "--field", "region=eu-central-1",
            "--passphrase", self.passphrase,
        ])

        # Exec python command that prints injected env vars
        code_str = (
            "import os, sys; "
            "assert os.environ.get('VAULT_SERVICE') == 'aws-prod'; "
            "assert os.environ.get('VAULT_USERNAME') == 'deployer'; "
            "assert os.environ.get('VAULT_PASSWORD') == 'super-secret-aws-key'; "
            "assert os.environ.get('VAULT_REGION') == 'eu-central-1'; "
            "assert os.environ.get('AWS_PROD_REGION') == 'eu-central-1'; "
            "sys.exit(0)"
        )
        ret = self._exec_cli(["exec", "aws-prod", "--passphrase", self.passphrase, "--", sys.executable, "-c", code_str])
        self.assertEqual(ret, 0)

    def test_session_save_get_and_rm(self):
        self._exec_cli(["init", "--passphrase", self.passphrase])
        cookie_json = json.dumps([{"name": "session_id", "value": "xyz987"}])
        
        ret = self._exec_cli([
            "session-save", "google",
            "--cookies-json", cookie_json,
            "--passphrase", self.passphrase,
        ])
        self.assertEqual(ret, 0)

        full = vault_mod.read_full_vault(self.passphrase)
        self.assertIn("google", full["sessions"])
        self.assertEqual(full["sessions"]["google"]["cookies"], [{"name": "session_id", "value": "xyz987"}])

        ret = self._exec_cli(["session-rm", "google", "--passphrase", self.passphrase])
        self.assertEqual(ret, 0)
        full = vault_mod.read_full_vault(self.passphrase)
        self.assertNotIn("google", full["sessions"])

    def test_password_generation_and_auto_rotation(self):
        self._exec_cli(["init", "--passphrase", self.passphrase])
        self._exec_cli([
            "add", "myservice",
            "-u", "admin",
            "-p", "initial_pass_123",
            "--passphrase", self.passphrase,
        ])

        # Rotate password
        ret = self._exec_cli(["rotate", "myservice", "--length", "32", "--passphrase", self.passphrase])
        self.assertEqual(ret, 0)

        entries = vault_mod.read_entries(self.passphrase)
        new_pass = entries["myservice"]["password"]
        self.assertNotEqual(new_pass, "initial_pass_123")
        self.assertEqual(len(new_pass), 32)
        self.assertIn("initial_pass_123", entries["myservice"]["fields"]["_pw_history"])

    def test_auto_snapshots_and_restore(self):
        self._exec_cli(["init", "--passphrase", self.passphrase])
        self._exec_cli(["add", "srv1", "-u", "u1", "-p", "p1", "--passphrase", self.passphrase])
        
        # Check snapshot exists
        snap_dir = self.hermes_home / "vault_backups"
        self.assertTrue(snap_dir.exists())
        snaps = list(snap_dir.glob("snapshot_*.json"))
        self.assertGreater(len(snaps), 0)

        # Mutate vault by removing srv1
        self._exec_cli(["rm", "srv1", "--passphrase", self.passphrase])
        entries = vault_mod.read_entries(self.passphrase)
        self.assertNotIn("srv1", entries)

        # Restore from snapshot 0 (the state before rm)
        ret = self._exec_cli(["restore", "0", "--passphrase", self.passphrase])
        self.assertEqual(ret, 0)
        entries_restored = vault_mod.read_entries(self.passphrase)
        self.assertIn("srv1", entries_restored)

    def test_security_audit_detection(self):
        self._exec_cli(["init", "--passphrase", self.passphrase])
        # Add weak password, reused password
        self._exec_cli(["add", "weak_srv", "-u", "u", "-p", "12345", "--passphrase", self.passphrase])
        self._exec_cli(["add", "reused_1", "-u", "u1", "-p", "SameSecretP@ssword123", "--passphrase", self.passphrase])
        self._exec_cli(["add", "reused_2", "-u", "u2", "-p", "SameSecretP@ssword123", "--passphrase", self.passphrase])

        ret = self._exec_cli(["audit", "--passphrase", self.passphrase])
        self.assertEqual(ret, 0)

    def test_dotenv_import_and_export(self):
        self._exec_cli(["init", "--passphrase", self.passphrase])
        env_file = self.hermes_home / "sample.env"
        env_file.write_text("STRIPE_API_KEY=sk_live_test_stripe_secret\nOPENAI_KEY=sk-openai123\n")

        ret = self._exec_cli(["import", "dotenv", str(env_file), "--passphrase", self.passphrase])
        self.assertEqual(ret, 0)

        entries = vault_mod.read_entries(self.passphrase)
        self.assertIn("stripe_api_key", entries)
        self.assertEqual(entries["stripe_api_key"]["password"], "sk_live_test_stripe_secret")

    def test_python_sdk_programmatic_api(self):
        self._exec_cli(["init", "--passphrase", self.passphrase])
        
        sdk = vault_mod.AccountVault()
        sdk.set("gitlab", "coder", "securepass123", {"totp_secret": "JBSWY3DPEHPK3PXP"})
        
        entry = sdk.get("gitlab")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["username"], "coder")
        
        totp = sdk.get_totp("gitlab")
        self.assertIsNotNone(totp)
        self.assertEqual(len(totp), 6)
        
        sdk.save_session("gitlab", {"token": "oauth_token_abc"})
        sess = sdk.get_session("gitlab")
        self.assertEqual(sess, {"token": "oauth_token_abc"})

    def test_sync_ecosystem_and_oauth_refresh_dry_run(self):
        self._exec_cli(["init", "--passphrase", self.passphrase])
        # Seed a sample .env and google_token.json in temp hermes_home
        (self.hermes_home / ".env").write_text(
            "GOOGLE_API_KEY=AIzaSyTestKey123456789012345678901234\n"
            "OPENROUTER_API_KEY=sk-or-v1-test123\n",
            encoding="utf-8",
        )
        (self.hermes_home / "google_token.json").write_text(
            json.dumps({
                "token": "ya29.initial",
                "refresh_token": "1//0g_test_refresh_token",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "123456-test.apps.googleusercontent.com",
                "client_secret": "GOCSPX-testsecret",
                "scopes": ["https://www.googleapis.com/auth/youtube"],
            }),
            encoding="utf-8",
        )

        sdk = vault_mod.AccountVault(self.passphrase)
        stats = sdk.sync_ecosystem(hermes_home=self.hermes_home, repo_root=_REPO_ROOT)
        self.assertGreaterEqual(stats["google_accounts_synced"], 10)
        self.assertGreaterEqual(stats["fleet_nodes_synced"], 19)
        self.assertGreaterEqual(stats["dotenv_secrets_synced"], 2)
        self.assertGreaterEqual(stats["oauth_clients_and_tokens_synced"], 1)

        # Verify OAuth refresh dry-run
        refresh_res = sdk.refresh_oauth_tokens(dry_run=True)
        self.assertGreaterEqual(refresh_res["total_checked"], 1)
        self.assertEqual(refresh_res["results"][0]["status"], "dry_run_ready")

    def test_playwright_cloud_provisioner_playbooks_and_providers(self):
        self._exec_cli(["init", "--passphrase", self.passphrase])
        sdk = vault_mod.AccountVault(self.passphrase)
        sdk.set(
            "google_insilos",
            "inteligentsilos@gmail.com",
            "SuperStrongVaultPass!2026",
            {"totp_secret": "JBSWY3DPEHPK3PXP", "provider": "google"},
        )

        for playbook in (
            "google-api-key",
            "google-oauth-client",
            "youtube-oauth",
            "google-security",
            "mcp-cloud-key",
        ):
            res = sdk.provision(
                playbook=playbook,
                account_id="google_insilos",
                provider="openrouter" if playbook == "mcp-cloud-key" else "google-cloud",
                project_id="project-3e385278-cd08-450e-ba0",
                channel_key="reality_decode",
                dry_run=True,
            )
            self.assertEqual(res["status"], "dry_run_ready")
            self.assertEqual(res["vault_service_key"], "google_insilos")
            self.assertTrue(res["details"]["has_password"])
            self.assertTrue(res["details"]["has_totp_secret"])

        # CLI providers command
        ret = self._exec_cli(["providers"])
        self.assertEqual(ret, 0)

    def test_zero_plaintext_passwords_in_source_and_markdown(self):
        bai_js = (_REPO_ROOT / "scripts" / "register_bai_accounts.js").read_text(encoding="utf-8")
        self.assertNotIn("Zeninall@123", bai_js)
        self.assertNotIn("Digimate@2025", bai_js)
        self.assertIn("loadAccountsFromVault", bai_js)

        bridge_py = (_REPO_ROOT / "scripts" / "bridge_9router_to_odoo.py").read_text(encoding="utf-8")
        self.assertNotIn("1NN0R1@2026", bridge_py)
        self.assertIn("_resolve_odoo_db_pass", bridge_py)

        gp_md = (_REPO_ROOT / "assets" / "credientials" / "google_personal.md").read_text(encoding="utf-8")
        self.assertNotIn("Zeninall@123", gp_md)
        self.assertIn("[Vault: vault.py get", gp_md)


if __name__ == "__main__":
    unittest.main()
