import modal
import os

app = modal.App("hermes-face-enhancer")

face_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "libgl1-mesa-glx", "libglib2.0-0", "git")
    .pip_install(
        "torch>=2.4.0",
        "torchvision",
        "opencv-python-headless",
        "gfpgan",
        "facexlib",
        "tqdm"
    )
)

@app.function(image=face_image, gpu="T4", timeout=600)
def check_enhancer():
    import gfpgan
    import facexlib
    return f"Face Enhancer ready with GFPGAN {gfpgan.__file__}"

@app.local_entrypoint()
def main():
    print(check_enhancer.remote())
