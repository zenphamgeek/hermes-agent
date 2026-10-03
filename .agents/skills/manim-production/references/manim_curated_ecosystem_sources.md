# Manim Curated Ecosystem & External Sources Knowledge Base

> **Hermes Agent Production Standard**: Xây dựng Content Factory tự động hóa hoạt họa toán học & vật lý (STEM) bằng việc kết hợp **Manim Community Edition (ManimCE)** và kiến trúc thư viện thành phần được chuẩn hóa (Curated Component Library).

---

## 1. Bản Đồ 7 Nguồn Tài Nguyên Manim Toàn Cầu

| Nguồn | Giấy phép | Commercial Safe? | Đánh giá | Vai trò trong Pipeline |
| :--- | :--- | :---: | :---: | :--- |
| **Manim Community Example Gallery** | MIT | ✅ CÓ | ⭐⭐⭐⭐⭐ | **Thư viện nền tảng**: Toàn bộ code mẫu đã render kiểm chứng, có thể tái sử dụng trực tiếp trong sản xuất. |
| **ManimCE Official Core Repo** | MIT | ✅ CÓ | ⭐⭐⭐⭐⭐ | **Quy chuẩn kỹ thuật**: Nguồn tham chiếu primitive chuẩn (`example_scenes`, tests đồ họa). |
| **Manim Plugin Gallery** | MIT / Apache | ✅ CÓ | ⭐⭐⭐⭐⭐ | **Hệ sinh thái mở rộng**: Convention `manim-*` cho các module vật lý, hóa học, audio-sync. |
| **manim-physics** | MIT | ✅ CÓ | ⭐⭐⭐⭐⭐ | **Mô phỏng vật lý chuyên sâu**: Cơ học vật rắn, tĩnh điện, quang hình tia sáng, sóng lan truyền, con lắc. |
| **Awesome Manim** | Public / CC0 | ✅ CÓ | ⭐⭐⭐⭐ | **Chỉ mục khám phá (Discovery Index)**: Danh bạ creator, plugin và công cụ mới nhất 2026. |
| **Manim Kindergarten (`manim_sandbox`)** | Community Custom | ⚠️ HẠN CHẾ | ⭐⭐⭐ | **Tham chiếu thuật toán (Reference Only)**: Bị hạn chế thương mại trong README. Nghiêm cấm copy code trực tiếp; chỉ học ý tưởng và viết lại dưới MIT. |
| **3Blue1Brown Source Code (`3b1b/videos`)** | CC BY-NC-SA 4.0 | ❌ KHÔNG | ⭐⭐⭐⭐⭐ (Storytelling) | **Tham chiếu sư phạm & hình học hóa**: Bản quyền phi thương mại (NonCommercial) + viết bằng ManimGL. Dùng để học trực giác hình học và ẩn dụ thị giác, chuyển ngữ sang ManimCE MIT. |

---

## 2. Chiến Lược "Curated Component Library" Thay Vì Ad-hoc Search

Thay vì để Agent tìm kiếm GitHub một cách ngẫu nhiên mỗi khi viết kịch bản (gây bất ổn định, lỗi phiên bản ManimGL/CE cũ, hoặc vướng bản quyền):

Hệ thống triển khai thư viện thành phần đóng gói tại:
📁 `assets/manim_library/`

### Cấu Trúc Thư Mục:
```
assets/manim_library/
├── registry.json             # Danh mục JSON đặc tả metadata, tham số và tag
├── harvester/
│   ├── sources.yaml          # Ma trận nguồn, URL, và trạng thái giấy phép
│   └── harvest_engine.py     # CLI engine tìm kiếm và thu hoạch component
├── math/
│   ├── calculus.py           # DerivativeTangent, RiemannSum, GradientDescent3D
│   ├── probability.py        # BayesianScaleBalance, SoftmaxDistribution, GaussianBellCurve
│   └── linear_algebra.py     # VectorTransformation, OrthogonalProjection
├── physics/
│   └── kinematics.py         # ProjectileMotion, VelocityVector
├── charts/
│   └── charts_2d.py          # CalibrationECERoc, AnimatedBarChart
└── teaching/
    └── primitives.py         # KineticHologramHUD, ComparisonDuelSplit, CalloutBoxCard
```

---

## 3. Chuẩn Hóa API Thành Phần (Declarative Primitives)

Mỗi hoạt họa toán học trở thành một component có tham số rõ ràng:

```python
# Ví dụ: Ném xiên vật lý với phân rã vector
from assets.manim_library.physics.kinematics import ProjectileMotion

proj = ProjectileMotion(v0=5.0, theta_deg=50, g=9.81)
curve = proj.get_trajectory_curve(color=COLOR_CYAN)
vectors = proj.get_vectors_at_t(t=0.4)
```

Agent khi lập kịch bản phân cảnh chỉ cần đặc tả cấu hình:
```json
{
  "component": "bayesian_scale_balance",
  "prior_weight": 0.85,
  "likelihood_droplets": 4,
  "tilt_angle": 14.0,
  "theme": "amber_gold"
}
```

---

## 4. Công Cụ Thu Hoạch & Tra Cứu (Harvester Tool)

Hermes Agent có thể tra cứu thư viện qua CLI:

```bash
# Xem danh sách tất cả các component sẵn sàng
python3 assets/manim_library/harvester/harvest_engine.py list

# Tìm kiếm thành phần theo từ khóa toán/vật lý
python3 assets/manim_library/harvester/harvest_engine.py search "bayes"
python3 assets/manim_library/harvester/harvest_engine.py search "derivative"

# Tra cứu trạng thái nguồn và giấy phép
python3 assets/manim_library/harvester/harvest_engine.py sources
```
