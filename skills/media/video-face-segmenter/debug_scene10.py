import sys, cv2, numpy as np, insightface, json

VID = "/data/videos/EPORNER.COM - [nTd9aVQ8Ia1] Deep And Sloppy (720).mp4"
T0, T1 = 109.0, 111.8
app = insightface.app.FaceAnalysis(name="buffalo_l", providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
app.prepare(ctx_id=0, det_size=(640, 640))

cap = cv2.VideoCapture(VID)
fps = cap.get(cv2.CAP_PROP_FPS)
cap.set(cv2.CAP_PROP_POS_MSEC, T0 * 1000)
print(f"fps={fps}", file=sys.stderr)
frame_i = 0
out = []
while True:
    ts = T0 + frame_i / fps
    if ts > T1:
        break
    ok, frame = cap.read()
    if not ok:
        break
    faces = app.get(frame)
    rec = {"t": round(ts, 2)}
    if faces:
        f = faces[0]
        e = f.embedding
        norm = float(np.linalg.norm(e))
        attrs = {k: str(v)[:30] for k, v in vars(f).items() if not k.startswith('_')}
        rec["attrs"] = attrs
        rec.update({
            "det": round(float(f.det_score), 3),
            "gender": f.sex if hasattr(f, "sex") else None,
            "age": int(f.age) if hasattr(f, "age") else None,
            "yaw": round(float(f.pose[0]), 1),
            "pitch": round(float(f.pose[1]), 1),
            "roll": round(float(f.pose[2]), 1),
            "emb_norm": round(norm, 1),
            "emb_valid": bool(np.isfinite(e).all() and norm > 1e-6),
        })
        if f.landmark is not None and f.landmark.shape[0] >= 5:
            h = float(f.landmark[:, 1].max() - f.landmark[:, 1].min())
            rec["face_h"] = round(h, 0)
    else:
        rec["faces"] = 0
    out.append(rec)
    frame_i += 1

with open("/tmp/dbg.json", "w") as fp:
    json.dump(out, fp, indent=1)
print("WROTE /tmp/dbg.json", file=sys.stderr)
