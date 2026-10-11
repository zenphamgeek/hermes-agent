import sys, json, numpy as np, cv2, insightface

sys.path.insert(0, "/opt/seg-venv")
from segmenter import estimate_head_pose_5pts, calculate_sharpness, estimate_occlusion

VID = "/data/videos/EPORNER.COM - [nTd9aVQ8Ia1] Deep And Sloppy (720).mp4"
T0, T1 = 109.5, 111.167
SAMPLE_FPS = 6.0

app = insightface.app.FaceAnalysis(name="buffalo_l", providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
app.prepare(ctx_id=0, det_size=(640, 640))

cap = cv2.VideoCapture(VID)
fps = cap.get(cv2.CAP_PROP_FPS)
frame_step = max(1, int(round(fps / SAMPLE_FPS)))
start_frame = int(T0 * fps)
end_frame = int(T1 * fps)
cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

TH = {"max_yaw": 35.0, "max_pitch": 25.0, "max_roll": 30.0,
      "max_occlusion": 0.2, "min_sharpness": 50.0, "min_face_height": 90}

rows = []
curr = start_frame
while curr <= end_frame and cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    if (curr - start_frame) % frame_step == 0:
        t_sec = curr / fps
        faces = app.get(frame)
        cands = []
        for f in faces:
            gen = "female" if getattr(f, "gender", 0) == 0 else "male"
            if gen == "female":
                cands.append(f)
        if not cands:
            rows.append({"t": round(t_sec, 2), "faces": 0})
        else:
            df = max(cands, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
            bbox = df.bbox
            kps = df.kps
            face_h = int(bbox[3]-bbox[1])
            yaw, pitch, roll = estimate_head_pose_5pts(kps, frame.shape)
            sharp = calculate_sharpness(frame, bbox)
            occ = estimate_occlusion(frame, bbox, kps)
            det = float(getattr(df, "det_score", 1.0))
            is_ok = (abs(yaw)<=TH["max_yaw"] and abs(pitch)<=TH["max_pitch"] and
                     abs(roll)<=TH["max_roll"] and occ<=TH["max_occlusion"] and
                     sharp>=TH["min_sharpness"] and face_h>=TH["min_face_height"])
            rows.append({"t": round(t_sec,2), "det": round(det,2),
                         "yaw": round(yaw,1), "pitch": round(pitch,1), "roll": round(roll,1),
                         "occ": round(occ,2), "sharp": round(sharp,1), "face_h": face_h,
                         "OK": is_ok})
    curr += 1

cap.release()
with open("/tmp/dbg2.json", "w") as fp:
    json.dump(rows, fp, indent=1)
print("WROTE /tmp/dbg2.json", file=sys.stderr)
