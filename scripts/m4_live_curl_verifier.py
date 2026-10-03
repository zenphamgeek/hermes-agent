"""
Live Curl Verification & Evidence Collector for Milestone 4 Phase 1.
Executes live terminal-equivalent HTTP requests against:
- Direct Gateway (:8099)
- 9Router Proxy (:20128)
- Smart Harness & Stealth Endpoints (:8099)

Measures:
- Latencies (including CPU dry-run validation latency <= 1.0ms)
- Audio properties & EBU R128 integrated loudness via ffmpeg (-14.5 LUFS)
- PNG Base64 magic headers
- Probe quota constraints (probes_used_today <= 5)
- Template version registry SHA-256 hashes

Outputs: /home/zen/hermes-agent/output/m4_live_curl_evidence.json
"""

import os
import sys
import time
import json
import base64
import urllib.request
import urllib.error
import subprocess
import wave

OUTPUT_JSON = "/home/zen/hermes-agent/output/m4_live_curl_evidence.json"
GATEWAY_URL = "http://localhost:8099"
NINEROUTER_URL = "http://localhost:20128"
GATEWAY_KEY = "sk-modal-sovereign-local"
NINEROUTER_KEY = "sk-2cf84041b445dfaf-dzzetv-8159ccdf"

evidence = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "worker_id": "m4_worker_1",
    "project": "Modal Fleet x 9Router UAT, Onboarding Quality Gate & Stealth Harness Architecture",
    "milestone": "Milestone 4 Phase 1 (100% E2E Pass & Live Terminal Curl Evidence)",
    "verification_mode": "Opaque-Box Live Network & Binary Verification",
    "test_suite_execution": {},
    "direct_gateway_evidence": {},
    "ninerouter_evidence": {},
    "smart_harness_stealth_evidence": {}
}

# 1. Run pytest suite summary check
print("Running full pytest suite...")
test_files = [
    "tests/test_image_generation_uat.py",
    "tests/test_template_lifecycle.py",
    "tests/test_9router_modal_fleet_integration.py",
    "tests/test_smart_harness_and_stealth_uat.py",
    "tests/test_hot_pluggable_extensibility.py"
]

t0 = time.time()
res = subprocess.run(
    [sys.executable, "-m", "pytest"] + test_files + ["-v"],
    cwd="/home/zen/hermes-agent",
    capture_output=True,
    text=True
)
test_duration = time.time() - t0
print(f"Pytest exit code: {res.returncode} in {test_duration:.2f}s")

evidence["test_suite_execution"] = {
    "exit_code": res.returncode,
    "duration_seconds": round(test_duration, 2),
    "all_passed": res.returncode == 0,
    "test_files": test_files,
    "stdout_summary": [line for line in res.stdout.splitlines() if "passed in" in line or "collected" in line]
}

# Helper to do HTTP requests
def http_call(url, method="GET", headers=None, body=None, timeout=60):
    if headers is None:
        headers = {}
    data = None
    if body is not None:
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif isinstance(body, bytes):
            data = body
        else:
            data = str(body).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    t_start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            t_elapsed = time.perf_counter() - t_start
            resp_body = resp.read()
            return {
                "status": resp.status,
                "headers": dict(resp.headers),
                "elapsed_seconds": round(t_elapsed, 4),
                "body": resp_body
            }
    except urllib.error.HTTPError as e:
        t_elapsed = time.perf_counter() - t_start
        resp_body = e.read()
        return {
            "status": e.code,
            "headers": dict(e.headers),
            "elapsed_seconds": round(t_elapsed, 4),
            "body": resp_body,
            "error": str(e)
        }

def measure_ebur128(wav_path):
    cmd = [
        "ffmpeg", "-nostats", "-i", wav_path,
        "-af", "ebur128=framelog=quiet", "-f", "null", "-"
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = p.stderr
    lufs = None
    lra = None
    for line in out.splitlines():
        if "I:" in line and "LUFS" in line:
            parts = line.strip().split()
            for i, part in enumerate(parts):
                if part == "I:":
                    try:
                        lufs = float(parts[i+1])
                    except (ValueError, IndexError):
                        pass
        if "LRA:" in line and "LU" in line:
            parts = line.strip().split()
            for i, part in enumerate(parts):
                if part == "LRA:":
                    try:
                        lra = float(parts[i+1])
                    except (ValueError, IndexError):
                        pass
    return lufs, lra, out

# 2. Direct Gateway (:8099)
print("\n--- Verifying Direct Gateway (:8099) ---")

# 2.1 Chat Completions
chat_req = {
    "model": "modal/wan2.2-s2v",
    "messages": [{"role": "user", "content": "Tạo video Wan 2.2 S2V 16:9 học giả diễn giải thuyết entropy"}]
}
chat_resp = http_call(
    f"{GATEWAY_URL}/v1/chat/completions",
    method="POST",
    headers={"Authorization": f"Bearer {GATEWAY_KEY}"},
    body=chat_req
)
chat_json = json.loads(chat_resp["body"].decode("utf-8"))
print(f"Direct Chat: status {chat_resp['status']}, elapsed {chat_resp['elapsed_seconds']}s")
evidence["direct_gateway_evidence"]["chat_completions"] = {
    "endpoint": f"{GATEWAY_URL}/v1/chat/completions",
    "method": "POST",
    "auth_header": f"Bearer {GATEWAY_KEY[:8]}...{GATEWAY_KEY[-4:]}",
    "status": chat_resp["status"],
    "elapsed_seconds": chat_resp["elapsed_seconds"],
    "request_payload": chat_req,
    "response_payload": chat_json
}

# 2.2 Audio Speech
audio_req = {
    "model": "vieneu-tts-v3",
    "input": "Chào mừng bạn đến với hệ thống sovereign modal fleet",
    "voice": "vietnamese-studio"
}
print("Direct Speech synthesis...")
audio_resp = http_call(
    f"{GATEWAY_URL}/v1/audio/speech",
    method="POST",
    headers={"Authorization": f"Bearer {GATEWAY_KEY}"},
    body=audio_req
)
wav_path = "/home/zen/hermes-agent/output/direct_gateway_speech_verified.wav"
with open(wav_path, "wb") as f:
    f.write(audio_resp["body"])

with wave.open(wav_path, "rb") as w:
    channels = w.getnchannels()
    rate = w.getframerate()
    sampwidth = w.getsampwidth()
    frames = w.getnframes()
    duration = frames / float(rate)

lufs, lra, _ = measure_ebur128(wav_path)
print(f"Direct Speech: status {audio_resp['status']}, {rate}Hz, {channels}ch, {sampwidth*8}-bit, duration {duration:.2f}s, I: {lufs} LUFS, LRA: {lra} LU")
evidence["direct_gateway_evidence"]["audio_speech"] = {
    "endpoint": f"{GATEWAY_URL}/v1/audio/speech",
    "method": "POST",
    "auth_header": f"Bearer {GATEWAY_KEY[:8]}...{GATEWAY_KEY[-4:]}",
    "status": audio_resp["status"],
    "elapsed_seconds": audio_resp["elapsed_seconds"],
    "request_payload": audio_req,
    "audio_file": wav_path,
    "audio_properties": {
        "channels": channels,
        "sample_rate_hz": rate,
        "bit_depth": sampwidth * 8,
        "duration_seconds": round(duration, 2),
        "total_bytes": len(audio_resp["body"])
    },
    "ebu_r128_metrics": {
        "integrated_loudness_lufs": lufs,
        "loudness_range_lu": lra,
        "target_spec_lufs": -14.5,
        "tolerance_lu": 0.5,
        "conforms": -15.0 <= lufs <= -14.0 if lufs is not None else False
    }
}

# 2.3 Images Generations (URL)
img_url_req = {
    "model": "modal/qwen-image-2.1",
    "prompt": "Cyber-minimalist architectural diagram of a neural engine",
    "n": 1,
    "size": "1024x1024",
    "response_format": "url"
}
img_url_resp = http_call(
    f"{GATEWAY_URL}/v1/images/generations",
    method="POST",
    headers={"Authorization": f"Bearer {GATEWAY_KEY}"},
    body=img_url_req
)
img_url_json = json.loads(img_url_resp["body"].decode("utf-8"))
print(f"Direct Image (URL): status {img_url_resp['status']}, elapsed {img_url_resp['elapsed_seconds']}s")
evidence["direct_gateway_evidence"]["images_generations_url"] = {
    "endpoint": f"{GATEWAY_URL}/v1/images/generations",
    "method": "POST",
    "auth_header": f"Bearer {GATEWAY_KEY[:8]}...{GATEWAY_KEY[-4:]}",
    "status": img_url_resp["status"],
    "elapsed_seconds": img_url_resp["elapsed_seconds"],
    "request_payload": img_url_req,
    "response_payload": img_url_json
}

# 2.4 Images Generations (b64_json)
img_b64_req = {
    "model": "modal/qwen-image-2.1",
    "prompt": "Cyber-minimalist architectural diagram of a neural engine",
    "n": 1,
    "size": "1024x1024",
    "response_format": "b64_json"
}
img_b64_resp = http_call(
    f"{GATEWAY_URL}/v1/images/generations",
    method="POST",
    headers={"Authorization": f"Bearer {GATEWAY_KEY}"},
    body=img_b64_req
)
img_b64_json = json.loads(img_b64_resp["body"].decode("utf-8"))
raw_b64 = img_b64_json["data"][0]["b64_json"]
raw_png = base64.b64decode(raw_b64)
png_magic_valid = raw_png.startswith(b"\x89PNG\r\n\x1a\n")
print(f"Direct Image (b64_json): status {img_b64_resp['status']}, decoded bytes {len(raw_png)}, magic valid: {png_magic_valid}")

# We omit the full huge b64 string in json evidence to keep it clean, but keep verification metadata
evidence["direct_gateway_evidence"]["images_generations_b64_json"] = {
    "endpoint": f"{GATEWAY_URL}/v1/images/generations",
    "method": "POST",
    "auth_header": f"Bearer {GATEWAY_KEY[:8]}...{GATEWAY_KEY[-4:]}",
    "status": img_b64_resp["status"],
    "elapsed_seconds": img_b64_resp["elapsed_seconds"],
    "request_payload": img_b64_req,
    "png_verification": {
        "raw_png_bytes": len(raw_png),
        "png_magic_header_valid": png_magic_valid,
        "first_16_bytes_hex": raw_png[:16].hex()
    },
    "response_metadata": {
        "created": img_b64_json.get("created"),
        "model": img_b64_json.get("model"),
        "template": img_b64_json.get("template"),
        "dag_integrity": img_b64_json.get("dag_integrity")
    }
}


# 3. 9Router (:20128)
print("\n--- Verifying 9Router (:20128) ---")

# 3.1 Chat Completions
r9_chat_req = {
    "model": "modal/wan2.2-s2v",
    "messages": [{"role": "user", "content": "Tạo video Wan 2.2 S2V 16:9 qua 9Router"}]
}
r9_chat_resp = http_call(
    f"{NINEROUTER_URL}/v1/chat/completions",
    method="POST",
    headers={"Authorization": f"Bearer {NINEROUTER_KEY}"},
    body=r9_chat_req
)
r9_chat_text = r9_chat_resp["body"].decode("utf-8")
r9_chat_json = json.loads(r9_chat_text.replace("data: [DONE]", "").strip())
print(f"9Router Chat: status {r9_chat_resp['status']}, elapsed {r9_chat_resp['elapsed_seconds']}s")
evidence["ninerouter_evidence"]["chat_completions"] = {
    "endpoint": f"{NINEROUTER_URL}/v1/chat/completions",
    "method": "POST",
    "auth_header": f"Bearer {NINEROUTER_KEY[:8]}...{NINEROUTER_KEY[-4:]}",
    "status": r9_chat_resp["status"],
    "elapsed_seconds": r9_chat_resp["elapsed_seconds"],
    "request_payload": r9_chat_req,
    "response_payload": r9_chat_json
}

# 3.2 Audio Speech
r9_audio_req = {
    "model": "modal/vieneu-tts-v3",
    "input": "Kiểm thử âm thanh tiếng Việt qua proxy 9Router chuẩn studio",
    "voice": "vietnamese-studio"
}
print("9Router Speech synthesis...")
r9_audio_resp = http_call(
    f"{NINEROUTER_URL}/v1/audio/speech",
    method="POST",
    headers={"Authorization": f"Bearer {NINEROUTER_KEY}"},
    body=r9_audio_req
)
r9_wav_path = "/home/zen/hermes-agent/output/9router_speech_verified.wav"
with open(r9_wav_path, "wb") as f:
    f.write(r9_audio_resp["body"])

with wave.open(r9_wav_path, "rb") as w:
    channels = w.getnchannels()
    rate = w.getframerate()
    sampwidth = w.getsampwidth()
    frames = w.getnframes()
    duration = frames / float(rate)

lufs, lra, _ = measure_ebur128(r9_wav_path)
print(f"9Router Speech: status {r9_audio_resp['status']}, {rate}Hz, {channels}ch, duration {duration:.2f}s, I: {lufs} LUFS")
evidence["ninerouter_evidence"]["audio_speech"] = {
    "endpoint": f"{NINEROUTER_URL}/v1/audio/speech",
    "method": "POST",
    "auth_header": f"Bearer {NINEROUTER_KEY[:8]}...{NINEROUTER_KEY[-4:]}",
    "status": r9_audio_resp["status"],
    "elapsed_seconds": r9_audio_resp["elapsed_seconds"],
    "request_payload": r9_audio_req,
    "audio_file": r9_wav_path,
    "audio_properties": {
        "channels": channels,
        "sample_rate_hz": rate,
        "bit_depth": sampwidth * 8,
        "duration_seconds": round(duration, 2),
        "total_bytes": len(r9_audio_resp["body"])
    },
    "ebu_r128_metrics": {
        "integrated_loudness_lufs": lufs,
        "loudness_range_lu": lra,
        "target_spec_lufs": -14.5,
        "tolerance_lu": 0.5,
        "conforms": -15.0 <= lufs <= -14.0 if lufs is not None else False
    }
}

# 3.3 Images Generations (URL)
r9_img_url_req = {
    "model": "modal/qwen-image-2.1",
    "prompt": "Cyber-minimalist architectural diagram via 9Router",
    "n": 1,
    "size": "1024x1024",
    "response_format": "url"
}
r9_img_url_resp = http_call(
    f"{NINEROUTER_URL}/v1/images/generations",
    method="POST",
    headers={"Authorization": f"Bearer {NINEROUTER_KEY}"},
    body=r9_img_url_req
)
r9_img_url_json = json.loads(r9_img_url_resp["body"].decode("utf-8"))
print(f"9Router Image (URL): status {r9_img_url_resp['status']}, elapsed {r9_img_url_resp['elapsed_seconds']}s")
evidence["ninerouter_evidence"]["images_generations_url"] = {
    "endpoint": f"{NINEROUTER_URL}/v1/images/generations",
    "method": "POST",
    "auth_header": f"Bearer {NINEROUTER_KEY[:8]}...{NINEROUTER_KEY[-4:]}",
    "status": r9_img_url_resp["status"],
    "elapsed_seconds": r9_img_url_resp["elapsed_seconds"],
    "request_payload": r9_img_url_req,
    "response_payload": r9_img_url_json
}

# 3.4 Images Generations (b64_json)
r9_img_b64_req = {
    "model": "modal/qwen-image-2.1",
    "prompt": "Cyber-minimalist architectural diagram via 9Router",
    "n": 1,
    "size": "1024x1024",
    "response_format": "b64_json"
}
r9_img_b64_resp = http_call(
    f"{NINEROUTER_URL}/v1/images/generations",
    method="POST",
    headers={"Authorization": f"Bearer {NINEROUTER_KEY}"},
    body=r9_img_b64_req
)
r9_img_b64_json = json.loads(r9_img_b64_resp["body"].decode("utf-8"))
r9_raw_b64 = r9_img_b64_json["data"][0]["b64_json"]
r9_raw_png = base64.b64decode(r9_raw_b64)
r9_png_magic_valid = r9_raw_png.startswith(b"\x89PNG\r\n\x1a\n")
print(f"9Router Image (b64_json): status {r9_img_b64_resp['status']}, decoded bytes {len(r9_raw_png)}, magic valid: {r9_png_magic_valid}")
evidence["ninerouter_evidence"]["images_generations_b64_json"] = {
    "endpoint": f"{NINEROUTER_URL}/v1/images/generations",
    "method": "POST",
    "auth_header": f"Bearer {NINEROUTER_KEY[:8]}...{NINEROUTER_KEY[-4:]}",
    "status": r9_img_b64_resp["status"],
    "elapsed_seconds": r9_img_b64_resp["elapsed_seconds"],
    "request_payload": r9_img_b64_req,
    "png_verification": {
        "raw_png_bytes": len(r9_raw_png),
        "png_magic_header_valid": r9_png_magic_valid,
        "first_16_bytes_hex": r9_raw_png[:16].hex()
    },
    "response_metadata": {
        "created": r9_img_b64_json.get("created"),
        "model": r9_img_b64_json.get("model"),
        "template": r9_img_b64_json.get("template"),
        "dag_integrity": r9_img_b64_json.get("dag_integrity")
    }
}


# 4. Smart Harness & Stealth Endpoints (:8099)
print("\n--- Verifying Smart Harness & Stealth Endpoints (:8099) ---")

# 4.1 GET /api/agent/catalog
catalog_resp = http_call(f"{GATEWAY_URL}/api/agent/catalog")
catalog_json = json.loads(catalog_resp["body"].decode("utf-8"))
print(f"Catalog: status {catalog_resp['status']}, {len(catalog_json.get('templates', []))} templates, {len(catalog_json.get('services', []))} services")
evidence["smart_harness_stealth_evidence"]["agent_catalog"] = {
    "endpoint": f"{GATEWAY_URL}/api/agent/catalog",
    "method": "GET",
    "status": catalog_resp["status"],
    "elapsed_seconds": catalog_resp["elapsed_seconds"],
    "total_services": len(catalog_json.get("services", [])),
    "total_templates": len(catalog_json.get("templates", [])),
    "services_list": [s.get("id") for s in catalog_json.get("services", [])],
    "templates_sample": [
        {
            "id": t.get("id"),
            "title": t.get("title"),
            "sha256": t.get("sha256"),
            "nodes_count": t.get("nodes_count"),
            "parameters_count": t.get("parameters_count")
        } for t in catalog_json.get("templates", [])[:5]
    ]
}

# 4.2 POST /api/agent/dispatch (execute: false)
dispatch_req = {
    "template": "wan22_s2v_talking_avatar_production",
    "params": {
        "prompt": "Cyber-minimalist talking avatar",
        "seed": 1337
    },
    "execute": False
}
dispatch_resp = http_call(
    f"{GATEWAY_URL}/api/agent/dispatch",
    method="POST",
    headers={"Authorization": f"Bearer {GATEWAY_KEY}"},
    body=dispatch_req
)
dispatch_json = json.loads(dispatch_resp["body"].decode("utf-8"))
val_time = dispatch_json.get("validation_time_ms")
print(f"Dispatch dry-run: status {dispatch_resp['status']}, CPU validation time: {val_time}ms (ceiling <= 1.0ms: {val_time <= 1.0})")
evidence["smart_harness_stealth_evidence"]["agent_dispatch_dry_run"] = {
    "endpoint": f"{GATEWAY_URL}/api/agent/dispatch",
    "method": "POST",
    "auth_header": f"Bearer {GATEWAY_KEY[:8]}...{GATEWAY_KEY[-4:]}",
    "status": dispatch_resp["status"],
    "elapsed_seconds": dispatch_resp["elapsed_seconds"],
    "request_payload": dispatch_req,
    "response_payload": {
        "success": dispatch_json.get("success"),
        "template": dispatch_json.get("template"),
        "sha256": dispatch_json.get("sha256"),
        "dag_valid": dispatch_json.get("dag_valid"),
        "cycles": dispatch_json.get("cycles"),
        "dangling_links": dispatch_json.get("dangling_links"),
        "validation_time_ms": val_time,
        "latency_compliance_under_1ms": val_time <= 1.0 if val_time is not None else False,
        "checks": dispatch_json.get("checks"),
        "injected_parameters": dispatch_json.get("injected_parameters")
    }
}

# 4.3 GET /api/probe_quota
quota_resp = http_call(f"{GATEWAY_URL}/api/probe_quota")
quota_json = json.loads(quota_resp["body"].decode("utf-8"))
used = quota_json.get("probes_used_today", 0)
max_d = quota_json.get("max_daily", 5)
print(f"Probe Quota: status {quota_resp['status']}, used: {used}, max: {max_d}, compliant: {used <= 5}")
evidence["smart_harness_stealth_evidence"]["probe_quota"] = {
    "endpoint": f"{GATEWAY_URL}/api/probe_quota",
    "method": "GET",
    "status": quota_resp["status"],
    "elapsed_seconds": quota_resp["elapsed_seconds"],
    "response_payload": quota_json,
    "compliance": {
        "probes_used_today": used,
        "max_daily_limit": max_d,
        "conforms_under_or_equal_5": used <= 5
    }
}

# 4.4 GET /api/templates/versions
versions_resp = http_call(f"{GATEWAY_URL}/api/templates/versions")
versions_json = json.loads(versions_resp["body"].decode("utf-8"))
tracked = versions_json.get("total_templates_tracked", 0)
print(f"Templates Versions: status {versions_resp['status']}, tracked: {tracked}")
evidence["smart_harness_stealth_evidence"]["templates_versions"] = {
    "endpoint": f"{GATEWAY_URL}/api/templates/versions",
    "method": "GET",
    "status": versions_resp["status"],
    "elapsed_seconds": versions_resp["elapsed_seconds"],
    "total_templates_tracked": tracked,
    "versions_sample": {
        k: versions_json["versions"][k] for k in list(versions_json.get("versions", {}).keys())[:6]
    }
}

# Write final evidence JSON
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(evidence, f, indent=2, ensure_ascii=False)

print(f"\n[SUCCESS] Structured evidence saved to {OUTPUT_JSON}")
