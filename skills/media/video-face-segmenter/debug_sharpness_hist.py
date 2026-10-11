import sys, json, numpy as np, cv2, insightface

sys.path.insert(0, "/opt/seg-venv")
from segmenter import calculate_sharpness

VID = "/data/videos/EPORNER.COM - [nTd9aVQ8Ia1] Deep And Sloppy (720).mp4"
app = insightface.app.FaceAnalysis(name="buffalo_l", providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
app.prepare(ctx_id=0, det_size=(640, 640))

cap = cv2.VideoCapture(VID)
fps = cap.get(cv2.CAP_PROP_FPS)
n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
dur = n_frames / fps
print(f"dur={dur:.0f}s frames={n_frames} fps={fps}", file=sys.stderr)

# sample every ~5s
step = int(fps * 5)
sharp_vals = []
frame_i = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    if frame_i % step == 0:
        faces = app.get(frame)
        if faces:
            df = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
            s = calculate_sharpness(frame, df.bbox)
            sharp_vals.append(round(float(s), 1))
    frame_i += 1
cap.release()

arr = np.array(sharp_vals)
print("n=", len(arr))
print("min/median/p75/max:", round(arr.min(),1), round(np.median(arr),1), round(np.percentile(arr,75),1), round(arr.max(),1))
print("pct <40:", round(100*np.mean(arr<40),1), "%")
print("pct <50:", round(100*np.mean(arr<50),1), "%")
print("deciles:", [round(float(np.percentile(arr, q)),1) for q in range(0,101,10)])
