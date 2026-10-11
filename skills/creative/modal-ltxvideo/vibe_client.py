"""
skills/creative/modal-ltxvideo/vibe_client.py
============================================
Hermes Agent - Vibe Client for Modal LTX-2.5 (22B) Foundation Model
Running on NVIDIA A100-80GB (Workspace: mojopham)

Supports:
1. Direct Modal Python SDK RPC (Cls.from_name)
2. Asynchronous Parallel Batch Generation (.spawn() for multi-GPU throughput)
3. Direct HTTP REST API (FastAPI Webhook)
4. Full Parameter Support: Image Referral Conditioning, Negative Prompt, STG Scale, Noise Scale
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Default App Metadata
MODAL_APP_NAME = "hermes-neural-ltxvideo"
MODAL_CLASS_NAME = "LTXVideoEngine"
MODAL_PROFILE_DEFAULT = "mojopham"
MODAL_REST_ENDPOINT = "https://mojopham--hermes-neural-ltxvideo-api.modal.run"


class VibeLTXClient:
    """
    Dedicated high-throughput client for Vibe Agents to generate 10s-15s
    cinematic videos on Modal A100-80GB GPU instances.
    """

    def __init__(self, profile: str = MODAL_PROFILE_DEFAULT):
        self.profile = os.getenv("MODAL_PROFILE", profile)
        os.environ["MODAL_PROFILE"] = self.profile
        self._engine_cls = None
        self._engine_instance = None

    def _get_engine(self):
        """Lazily connects to the remote deployed Modal class."""
        if self._engine_instance is None:
            import modal
            self._engine_cls = modal.Cls.from_name(MODAL_APP_NAME, MODAL_CLASS_NAME)
            self._engine_instance = self._engine_cls()
        return self._engine_instance

    def generate(
        self,
        prompt: str,
        image: Optional[str] = None,
        negative_prompt: str = "worst quality, blurry, distorted, jitter, low quality, artifact, watermarking, morphing, jittery movement",
        duration_sec: float = 10.0,
        fps: int = 24,
        width: int = 1280,
        height: int = 720,
        num_inference_steps: int = 35,
        guidance_scale: float = 3.5,
        stg_scale: float = 1.0,
        decode_noise_scale: float = 0.025,
        seed: Optional[int] = None,
        output_path: Optional[Union[str, Path]] = None,
    ) -> bytes:
        """
        Synchronous video generation via Modal RPC.
        Supports both text-to-video and image-to-video (referral conditioning).
        """
        engine = self._get_engine()
        video_bytes = engine.generate_video.remote(
            prompt=prompt,
            image=image,
            negative_prompt=negative_prompt,
            duration_sec=duration_sec,
            fps=fps,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            stg_scale=stg_scale,
            decode_noise_scale=decode_noise_scale,
            seed=seed,
        )

        if output_path:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(video_bytes)

        return video_bytes

    def generate_async(
        self,
        prompt: str,
        image: Optional[str] = None,
        negative_prompt: str = "worst quality, blurry, distorted, jitter, low quality, artifact, watermarking, morphing",
        duration_sec: float = 10.0,
        fps: int = 24,
        width: int = 1280,
        height: int = 720,
        num_inference_steps: int = 35,
        guidance_scale: float = 3.5,
        stg_scale: float = 1.0,
        decode_noise_scale: float = 0.025,
        seed: Optional[int] = None,
    ):
        """
        Spawns a remote generation job asynchronously on Modal cloud.
        Returns a Modal FunctionCall handle immediately.
        Use handle.get() to retrieve the resulting MP4 bytes.
        """
        engine = self._get_engine()
        handle = engine.generate_video.spawn(
            prompt=prompt,
            image=image,
            negative_prompt=negative_prompt,
            duration_sec=duration_sec,
            fps=fps,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            stg_scale=stg_scale,
            decode_noise_scale=decode_noise_scale,
            seed=seed,
        )
        return handle

    def generate_batch_parallel(
        self,
        tasks: List[Dict[str, Any]],
        output_dir: Optional[Union[str, Path]] = None,
    ) -> List[bytes]:
        """
        Parallel Vibe Coding Engine:
        Spawns multiple video generation jobs across Modal A100-80GB GPUs simultaneously!
        
        Example task dict:
        [
            {
                "prompt": "Scene 1: Drone shot over obsidian mountains",
                "image": "https://example.com/ref1.png",
                "duration_sec": 12.0
            },
            {
                "prompt": "Scene 2: Cyberpunk terminal booting in dark room",
                "duration_sec": 10.0
            }
        ]
        """
        engine = self._get_engine()
        handles = []

        print(f"[Vibe-LTX] Spawning {len(tasks)} video generation tasks in parallel on Modal GPU fleet...")
        for i, task in enumerate(tasks):
            h = engine.generate_video.spawn(
                prompt=task["prompt"],
                image=task.get("image", None),
                negative_prompt=task.get("negative_prompt", "worst quality, blurry, distorted, jitter, low quality, artifact, watermarking, morphing"),
                duration_sec=task.get("duration_sec", 10.0),
                fps=task.get("fps", 24),
                width=task.get("width", 1280),
                height=task.get("height", 720),
                num_inference_steps=task.get("num_inference_steps", 35),
                guidance_scale=task.get("guidance_scale", 3.5),
                stg_scale=task.get("stg_scale", 1.0),
                decode_noise_scale=task.get("decode_noise_scale", 0.025),
                seed=task.get("seed", None),
            )
            handles.append((i, task, h))

        results = []
        if output_dir:
            out_d = Path(output_dir)
            out_d.mkdir(parents=True, exist_ok=True)

        for i, task_data, h in handles:
            print(f"[Vibe-LTX] Awaiting result for task #{i+1}: '{task_data['prompt'][:40]}...'")
            video_bytes = h.get()
            results.append(video_bytes)

            if output_dir:
                filename = task_data.get("filename", f"vibe_video_{i+1:02d}.mp4")
                dest = out_d / filename
                dest.write_bytes(video_bytes)
                print(f"[✓] Saved task #{i+1} to {dest}")

        return results

    @staticmethod
    def generate_via_http(
        prompt: str,
        image: Optional[str] = None,
        negative_prompt: str = "worst quality, blurry, distorted, jitter, low quality, artifact, watermarking, morphing",
        duration_sec: float = 10.0,
        fps: int = 24,
        width: int = 1280,
        height: int = 720,
        num_inference_steps: int = 35,
        guidance_scale: float = 3.5,
        stg_scale: float = 1.0,
        decode_noise_scale: float = 0.025,
        seed: Optional[int] = None,
        endpoint_url: str = MODAL_REST_ENDPOINT,
        output_path: Optional[Union[str, Path]] = None,
    ) -> bytes:
        """
        Direct REST HTTP generation without requiring the `modal` Python library.
        Can be called from any lightweight agent or webhook.
        """
        import urllib.request
        import json

        payload = {
            "prompt": prompt,
            "image": image,
            "negative_prompt": negative_prompt,
            "duration_sec": duration_sec,
            "fps": fps,
            "width": width,
            "height": height,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "stg_scale": stg_scale,
            "decode_noise_scale": decode_noise_scale,
            "seed": seed,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=1800) as response:
            video_bytes = response.read()

        if output_path:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(video_bytes)

        return video_bytes


# Convenience singleton
client = VibeLTXClient()
