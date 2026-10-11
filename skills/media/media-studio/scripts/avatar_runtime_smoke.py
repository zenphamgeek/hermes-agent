#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

CONFIG = Path(__file__).parents[1] / "avatar_runtime.json"


def run(*command):
    return subprocess.run(command, text=True, capture_output=True, timeout=10)


def check(config):
    results = {}
    omni = config["omnivoice"]
    try:
        with urllib.request.urlopen(omni["base_url"] + omni["health_path"], timeout=5) as response:
            health = json.load(response)
        ok = health.get("engines", {}).get(omni["required_engine"], {}).get("status") == "ok"
        results["omnivoice"] = {"ok": ok, "status": health.get("overall")}
    except Exception as error:
        results["omnivoice"] = {"ok": False, "error": str(error)}

    face = config["facefusion"]
    state = run("lxc", "exec", face["container"], "--", "systemctl", "is-active", face["service"])
    root = run("lxc", "exec", face["container"], "--", "test", "-d", face["root"])
    results["facefusion"] = {"ok": state.stdout.strip() == "active" and root.returncode == 0, "service": state.stdout.strip() or state.stderr.strip()}

    for name, model in config["models"].items():
        root = Path(model["root"])
        checkpoint = Path(model["checkpoint"])
        results[name] = {"ok": root.is_dir() and checkpoint.exists(), "root": str(root), "checkpoint": str(checkpoint)}

    gpu = run("nvidia-smi", "--query-gpu=name,memory.free", "--format=csv,noheader,nounits")
    free = None
    if gpu.returncode == 0 and gpu.stdout.strip():
        free = int(gpu.stdout.strip().rsplit(",", 1)[1])
    results["gpu"] = {"ok": free is not None and free >= config["gpu"]["minimum_free_mib"], "free_mib": free, "lock_path": config["gpu"]["lock_path"]}
    results["output_root"] = {"ok": Path(config["output_root"]).parent.is_dir(), "path": config["output_root"]}
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG)
    args = parser.parse_args()
    results = check(json.loads(args.config.read_text()))
    print(json.dumps(results, indent=2))
    return 0 if all(item["ok"] for item in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
