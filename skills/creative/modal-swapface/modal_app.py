"""
Modal Serverless App for Face Swap
==================================
Deployable to Modal Workspaces (motion, mojopham, etc.)
Runs on GPU (NVIDIA T4 / A10G / L4).
"""

from pathlib import Path
import modal

app = modal.App("hermes-faceswap")

# GPU Image definition with FaceFusion / Onnx / InsightFace dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "git", "libgl1-mesa-glx", "libglib2.0-0")
    .pip_install(
        "numpy==1.26.4",
        "opencv-python-headless==4.9.0.80",
        "onnxruntime-gpu==1.17.1",
        "pillow==10.3.0",
        "tqdm==4.66.4"
    )
)

@app.function(
    image=image,
    gpu="T4",
    timeout=600,
)
def swap_face_core(source_bytes: bytes, target_bytes: bytes, is_video: bool = True) -> bytes:
    """Reject the unvalidated Modal implementation instead of returning unchanged input."""
    raise RuntimeError("Modal SwapFace is disabled until output validation passes")

@app.local_entrypoint()
def main(source: str, target: str, output: str):
    """Local CLI entrypoint for modal run."""
    with open(source, "rb") as sf:
        src_data = sf.read()
    with open(target, "rb") as tf:
        tgt_data = tf.read()

    is_vid = target.endswith(".mp4") or target.endswith(".mov") or target.endswith(".mkv")
    result_bytes = swap_face_core.remote(src_data, tgt_data, is_video=is_vid)

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as of:
        of.write(result_bytes)
    print(f"[Modal] Saved swapped output to {out_path}")
