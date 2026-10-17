---
name: graydoom-character-and-art-logic
description: >-
  Codex-grade Character Drawing, 26-Character Tri-Lock DNA, Profile One-Eye
  Turnaround Rule, Deterministic Close-Up Source Crops, 11% Alpha Fringe
  Derivative, 72px Lanczos Building Readability, 2081-Slot Game Art Atlas Work
  Orders, Settlement Spatial Map 18-Lot Gate, and Novel gemini-2 6-Axis
  Autonomous Fleet Art QA Skill for Gray Doom.
---

# Gray Doom Character Drawing, Game Art Logic & Visual QA Skill (`graydoom-character-and-art-logic`)

Cẩm nang kỹ thuật hợp nhất toàn bộ phương pháp luận kiểm soát **Logic & Visual** cho **Characters, Units, Buildings, Landscapes (`main` / `codex/*`)** và **Novel Scene Plates / Character Dossiers (`gemini-2`)** trong dự án **Gray Doom**.

---

## 1. Hệ Thống Khóa Tam Giác 26 Nhân Vật (26-Character Tri-Lock Registry)

Codex kiểm soát tính nhất quán tuyệt đối của toàn bộ **26 nhân vật** (`zen`, `ilya`, `nahla`, `vera`, `mei`, `lucia`, `evelyn`, `mara`, `lin`, `samira`, `oren`, `nadir`, `martin`, `corin`, `hadiya`, `hessa`, `dara`, `yao`, `rasan`, `vance`, `tariq`, `custodian`, `marcos`, `rovin`, `miranda`, `chen`) thông qua 3 sổ cái JSON khóa chéo nhau (`node scripts/verify-character-dossiers.js`):

1. **`content/canonical-characters-v1.json`**: Định nghĩa `character_id`, `canonical_name`, `faction`, `role`, `dna_id`, `literary_source`, 5 góc quay chuẩn, 6 sắc thái biểu cảm và `spatial_prompt_template` 3 khối.
2. **`art/production/character-face-consistency-dna-v1.json`**: Khóa `demographics` (`age_bracket`, `ethnicity`, `height_build`), `facial_dna` (cấu trúc xương mặt, khoảng cách mắt, sống mũi, đường hàm), `clothing_silhouette`, `canonical_faction`, `canonical_reference_asset` và `canonical_weapon`.
3. **`art/production/character-face-expression-dossiers-v1.json`**: Khóa `facial_anchors`, `attire_locks`, `negative_prompt_anti_drift` và danh sách ứng viên góc mặt/biểu cảm.

### Các Quy Tắc Nhận Diện Bất Biến (Identity Locks):
- **Canonical Character Face Authority (`main` branch)**: Khuôn mặt gốc chuẩn mực thuộc về các visual masters trên nhánh `main` (`art/candidates/consorts/sunward-court-six-person-v3.png` và `art/candidates/consorts/*-identity-*.png`). Mọi tranh vẽ trên nhánh `main`, `codex/*` và `gemini-2` phải giữ nguyên cấu trúc xương mặt, kiểu tóc và trang sức đặc trưng này.
- **Director Lin Wei Identity Lock**: `Director Lin Wei` (`lin`) là phụ nữ trưởng thành (`adult woman`), tách biệt hoàn toàn với `Consort Mei` (`mei`).
- **Zen & Ilya Visual Locks**: `Zen` luôn đeo kính gọng đen mảnh hình chữ nhật (`rectangular thin black frames`), mặc áo khoác dạ dài màu xám than phi quân sự; `Ilya` mặc áo khoác da lộn cổ lông cừu (`shearling coat`).
- **5 Consorts Demilitarization Lock (`nahla`, `vera`, `mei`, `lucia`, `evelyn`)**: Tần phi mặc lụa hoàng gia theo bảng màu phe phái, **0% giáp trụ chiến đấu, 0% vũ khí, 0% mũ sắt hay rằn ri quân sự**.

---

## 2. Quy Trình 5 Giai Đoạn Vẽ Nhân Vật & Xoay Góc (5-Stage Character Turnaround Pipeline)

### Giai đoạn 1 — Cắt Nguồn Cận Cảnh Xác Định (Deterministic Close-Up Source Crops)
Trước khi đưa ảnh vào `Qwen/Qwen-Image-2.1` (`image-edit`), tuyệt đối không gửi toàn cảnh rộng khiến model làm trôi nét mặt. Phải dùng script Python cắt đúng tọa độ đầu–vai từ ảnh gốc đã duyệt và kiểm tra khớp từng byte (`--write` / `--check`):
- `scripts/export-nahla-closeup-source.py`: `(758, 0, 1672, 941)`
- `scripts/export-vera-closeup-source.py`: `(688, 0, 1536, 1024)`
- `scripts/export-lucia-closeup-source.py`: `(915, 0, 1672, 941)`
- `scripts/export-evelyn-closeup-source.py`: `(688, 0, 1536, 1024)`
- `scripts/export-mei-closeup-source.py`: `(758, 0, 1672, 941)`

### Giai đoạn 2 — 5 Góc Camera Turnaround & Luật Giải Phẫu Nghiêm Ngặt
1. `ANG_FRT_00` (`front-0`): Chính diện cân xứng, khóa tỉ lệ mắt–mũi–nhân trung–cằm.
2. `ANG_FL3_45` (`three-quarter-left` / `three-quarter-right`): Góc 3/4 thấy rõ cả 2 mắt với phối cảnh xa–gần đúng giải phẫu; đối chiếu trên bảng **Consort Right-Angle Comparison Sheet** (`1100×1460 px`, `scripts/build-consort-right-angle-comparison.py`).
3. `ANG_PRF_90` (`profile-left` / `profile-right`): **Profile One-Eye Rule (Luật Trắc Diện 1 Mắt)** — ở góc nghiêng 90°, **chỉ được phép nhìn thấy đúng 1 mắt** cùng đường sống mũi–môi–cằm sắc nét. Nếu lộ mắt thứ hai bên mặt khuất $\to$ **LOẠI NGAY LẬP TỨC (FAIL QA)**.
4. `ANG_BC3_135` (`back-three-quarter`): Góc 3/4 từ sau lưng, kiểm tra xương hàm dưới, vành tai và búi tóc.
5. `ANG_BCK_180` (`back-hair-silhouette`): **Back Silhouette Rule** — chỉ thể hiện hình khối tóc phía sau, cổ áo và độ rộng vai khớp với góc trước; tuyệt đối không tự bịa thêm phụ kiện hay vũ khí sau lưng.

### Giai đoạn 3 — 6 Sắc Thái Biểu Cảm Vi Mô (6 Micro-Expression Moods)
Giữ nguyên 100% khuôn mặt, tuổi tác, trang phục, trang sức và góc máy; chỉ thay đổi cơ mặt:
- `MOOD_NEUTRAL`, `MOOD_DETERMINED_FOCUS`, `MOOD_SUPPRESSED_TENSION`, `MOOD_CALCULATING_ASSESSMENT`, `MOOD_AUTHORITATIVE_COMMAND`, `MOOD_COLD_FURY`.

### Giai đoạn 4 — Cấu Trúc Spatial Prompt 3 Khối Bắt Buộc
Mọi prompt nhân vật và đại cảnh bắt buộc chứa đủ 3 nhãn cấu trúc:
- `[SPATIAL_ENVIRONMENT]`: Địa lý kiến trúc chuẩn phe phái (ví dụ: Tổng cục Phương Đông là hệ thống âu thuyền/kênh đào nội địa, **cấm tuyệt đối biển lớn hay tàu container hàng hải**).
- `[GAZE_DIRECTION_AND_CAMERA_BLOCKING]`: Hướng nhìn, tiêu cự ống kính, vị trí đứng tương đối giữa các nhân vật.
- `[EMOTIONAL_INTENSITY_AND_MICRO_EXPRESSIONS]`: Sắc thái tâm lý nội tâm và chi tiết cơ mặt.

---

## 3. Cổng Kiểm Soát Logic & Pixel Cho Units, Buildings & Landscapes

### 3.1. Cổng Lề Trong Suốt 11% & Khử Sương Mờ Alpha Xác Định (`alpha 1–7 -> 0`)
1. **11% Raw Alpha Margin Gate**:
   - Trên canvas `1254 × 1254 px`, 4 cạnh của hình thể có $\alpha \ge 8$ phải cách mép ảnh tối thiểu **138 px ($\ge 11\%$)**.
2. **Alpha-Fringe Derivative (`scripts/verify-derived-alpha-candidates.py`)**:
   - Nếu hình thể có $\alpha \ge 8$ đã đạt lề $\ge 11\%$ nhưng bị vướng các hạt bụi mờ $\alpha \in [1, 7]$, cho phép tạo bản phái sinh đặt $\alpha \in [1, 7] \to 0$.
   - **Bất biến**: Giữ nguyên file PNG gốc; kiểm tra từng pixel để chứng minh mọi kênh `RGB` và mọi pixel có $\alpha = 0$ hoặc $\alpha \in [8, 255]$ **không thay đổi dù chỉ 1 bit**.
3. **Centered Reframe Candidate (`scripts/verify-art-reframe-candidates.py`)**:
   - Nếu hình thể bị tràn lề 11%, thu phóng Lanczos về khung `768 px` đặt giữa canvas `1024 × 1024 px` (lề `128 px = 12.5%`), lưu kèm biên bản QA riêng.

### 3.2. Kiểm Định Độ Khả Đọc Công Trình Ở Cỡ Thực Tế 72×72 px (`In-Game 72px Readability`)
- Chạy `scripts/build-building-crop-72px-review.py` và `scripts/export-*-72px-study.py`:
  1. Lấy bounding box `alpha.getbbox()` của công trình.
  2. Thu nhỏ bằng bộ lọc **Lanczos** về kích thước tối đa **58 px** và đặt chính giữa canvas trong suốt **72 × 72 px**.
  3. Kiểm tra bằng mắt và liên kết vào bảng đối chiếu in-game (`scripts/build-building-release-crop-game-binding.js`, `scripts/build-building-release-crop-mobile-review.js`): công trình phải nhận diện được ngay lập tức vai trò (Marketplace, Residence, Reserve Cache, Trade Office, Academy) mà không bị bết màu hay lẫn với mảnh vụn công trình bên cạnh.

### 3.3. Kiến Trúc 2,081-Slot Game Art Atlas & Bản Đồ Không Gian 18 Lô (`Settlement Spatial Map`)
- **2,081-Slot Atlas Work Orders (`scripts/build-game-art-atlas-work-orders.py --check`)**:
  - Tự động biên dịch trạng thái của 26 Characters, 44 Units, 50 Buildings và 22 Landscapes thành 2,081 đơn đặt hàng (`taskId = <assetId>::<kind>::<target>`) với cổng trạng thái tường minh (`ready-for-candidate`, `blocked-identity-authority`, `runtime-source-needs-correction`, `approved-plate-needs-variant-review`).
- **Settlement Spatial Map Gate (`scripts/verify-settlement-spatial-map-candidate.py`)**:
  - Kiểm tra bản đồ không gian 18 lô tài nguyên (`observedDistinctLots <= 18`). Nếu ảnh sinh ra chưa tách bạch đủ 18 lô xây dựng (`observedDistinctLots < 18`), tự động giữ trạng thái `needs-correction` và đóng chặt cổng `gameplayReady: false`, `runtimeAllowed: false`, `releaseReady: false`.

---

## 4. Cổng Kiểm Toán Tự Động 6 Trục Trên Nhánh Novel `gemini-2` (`autonomous-fleet-art-harness.py`)

Trên nhánh `gemini-2` (`/home/zen/Downloads/Graydoom-novel`), quy trình duyệt Art thủ công được thay thế hoàn toàn bằng **6-Axis Autonomous Fleet Art QA Harness** (`scripts/autonomous-fleet-art-harness.py` & `tools/plate_tripwire.py` trên **352 Scene Plates**):

1. **Axis 1 — `spatial_geography`**: Đảm bảo bối cảnh địa lý đúng chuẩn phe phái (chặn từ khóa biển cả/tàu biển trong bối cảnh kênh đào nội địa Phương Đông).
2. **Axis 2 — `gaze_blocking`**: Kiểm tra hướng nhìn và bố cục tương tác giữa các nhân vật.
3. **Axis 3 — `facial_dna`**: Kiểm tra DNA khuôn mặt, kính gọng đen mảnh của Zen, khuôn mặt chuẩn `main` branch của 5 Tần phi.
4. **Axis 4 — `wardrobe_demilitarization`**: Đảm bảo Tần phi mặc lụa hoàng gia (0% giáp/vũ khí), Zen mặc áo khoác dạ, Ilya mặc áo khoác cổ lông cừu.
5. **Axis 5 — `style_consistency`**: Hiện thực điện ảnh tàn khốc (Brutal Technological Realism / 16:9 native aspect ratio), 0% anime/3D CGI bóng bẩy.
6. **Axis 6 — `negative_sanitization` & `plate_tripwire.py`**: Độ phân giải chuẩn ($\ge 1920$ hoặc `1672×941` / `1536×1024`), kiểm tra 352 tấm tranh chương truyện qua ngưỡng thống kê thực nghiệm (`352/352 passing`), tự động cập nhật `art/production/review-decisions-v1.json` và biên dịch cổng giao diện `scripts/build-novel-art-review-portal.py`.

---

## 5. Chuỗi Lệnh Kiểm Tra Bắt Buộc Trước Khi Commit Art

```bash
# 1. Tiền kiểm trước khi gửi job Modal (Single-in-Flight & Live Health)
npm run check:art-submission -- art/production/generation-jobs/<subpath>/<job>.json

# 2. Kiểm tra 26 Character Dossiers & Consort Identities
node scripts/verify-character-dossiers.js
npm run verify:consort-identities

# 3. Kiểm tra lề Alpha 11%, Phái sinh Alpha 1-7 và Reframe
python3 scripts/verify-derived-alpha-candidates.py
python3 scripts/verify-art-reframe-candidates.py
npm run verify:generation-jobs

# 4. Kiểm tra toàn bộ kho Art & đồng bộ chỉ mục SHA-256
npm run verify:art
npm run verify:content-sources
```
