# Content Factory — Pipeline & Architecture Specification

## 1. P15 Infrastructure Microservices Map

| Service Name | Network Location | Purpose |
|---|---|---|
| **LM Studio** | `http://10.123.214.1:1234/v1` | Storyboard, prompt generation, text copywriting |
| **ComfyUI** | `http://10.123.214.153:8188` | Image generation, SDXL / FLUX visual workflows |
| **FaceFusion** | `http://10.123.214.208:7860` | High-fidelity face swapping & face enhancement |
| **OmniVoice TTS** | `http://10.123.214.178:8080` | Vietnamese / English voice synthesis |
| **MinIO S3** | `http://10.123.214.249:9000` | Asset storage (`shared-assets`, `comfyui-outputs`) |
| **Redis** | `10.123.214.184:6379` | Task queues, job states, session cache |
| **n8n Automation** | `http://10.123.214.64:5678` | Scheduled publishing webhooks & multi-channel syndication |

## 2. Directory Conventions

- Raw Footage: `~/workspace/footage/`
- Source Faces: `~/workspace/faces/`
- Segmented Clips: `~/workspace/output/segments/`
- Final Production: `~/workspace/output/factory/`
- S3 Cloud Backup: `s3://shared-assets/factory/`

## 3. Telegram Command Mapping

| Telegram Command | Target Action |
|---|---|
| `/factory plan <topic>` | Generates script, storyboard, and voice prompts via LM Studio |
| `/factory tts <text>` | Generates voiceover WAV file via OmniVoice container |
| `/factory comfy <prompt>` | Dispatches render job to ComfyUI |
| `/factory swap <face> <target>` | Runs FaceFusion swap on footage |
| `/factory publish <all|yt|fb|x>` | Posts rendered video to configured channels |
| `/factory status` | Reports status of active render jobs |
