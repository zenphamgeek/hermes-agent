# THƯ VIỆN BỐ CỤC ĐIỆN ẢNH & CẤU TRÚC 2D / 3D MANIM CHUYÊN SÂU

> **Dành cho:** Kênh ZENPHAM (`@vu-minh-quang`) — Chuẩn 2K QHD (2560x1440 @ 60fps)  
> **Module chính:** `assets/scripts_video/manim_advanced_studio.py` & `components/`  
> **Theme:** Neo-Noir Obsidian `#0c0d12`, Cyan `#00e5ff`, Gold `#ffb300`, Rose `#ff2a6d`

---

## 1. HỆ THỐNG BỐ CỤC ĐIỆN ẢNH (CINEMATIC LAYOUTS)

### A. GoldenSplitLayout (Bố Cục Tỷ Lệ Vàng 62% : 38%)
Chia khung hình 16:9 thành 2 phần bất đối xứng theo chuẩn điện ảnh:
- **Phần lớn (Visual Zone, 62% diện tích):** Trực quan hóa không gian hình học, ma trận nơ-ron hoặc đồ thị 3D chuyển động.
- **Phần nhỏ (Explain / Math Zone, 38% diện tích):** Đặt công thức toán học MathTex, dòng code Python hoặc thẻ bài tóm tắt ý nghĩa triết học.
- **Vách ngăn:** Đường rãnh `DashedLine` màu `NoirPalette.GRID_LINE` tinh tế, tạo độ ngăn nắp tuyệt đối.

```python
layout = GoldenSplitLayout(mode="left_visual")
# Đặt phần tử trực quan vào visual_center: [-2.2, 0, 0]
visual_obj.move_to(layout.visual_center)
# Đặt công thức toán vào math_center: [4.2, 0, 0]
math_obj.move_to(layout.math_center)
divider = layout.attach_divider()
self.play(FadeIn(visual_obj), FadeIn(math_obj), Create(divider))
```

### B. HUDTelemetryCard (Thẻ Đo Lường HUD Thời Gian Thực)
Thẻ thông số phong cách Sci-Fi công nghệ cao, hiệu ứng kính mờ Glassmorphism mờ 85%, viền Cyan Neon:
- Hiển thị Loss $\mathcal{L}$, Tốc độ học $\eta$, Bộ nhớ VRAM, Throughput token/s.
- Thích hợp đặt ở góc trên bên phải (UR) để minh họa quá trình huấn luyện nơ-ron sống động.

```python
hud = HUDTelemetryCard(
    title="TRAINING TELEMETRY",
    metrics=[("Loss", "0.0182"), ("LR", "1e-4"), ("VRAM", "24.6 GB"), ("Tokens/s", "128k")]
)
hud.to_corner(UR, buff=0.4)
self.play(FadeIn(hud))
```

### C. QuadrantComparisonLayout (Bố Cục 4 Góc Phần Tư So Sánh)
Chia khung hình thành 4 ô trực giao bằng hồng tâm `Crosshair` nét đứt:
- So sánh song song 4 thuật toán tối ưu: SGD vs Momentum vs RMSProp vs Adam.
- So sánh 4 hàm kích hoạt: ReLU vs GELU vs SiLU vs Swish.

---

## 2. KHO CẤU TRÚC TOÁN HỌC 2D ĐA CHIỀU (ADVANCED 2D STRUCTURES)

### A. MatrixTensorGrid (Ma Trận & Tensor Động Tương Tác)
- Hiển thị lưới ma trận kích thước $M \times N$ với ngoặc vuông toán học Neon.
- Tự động tô màu độ đậm nhạt từng ô theo giá trị (0 ➔ 1).
- Hỗ trợ quét hàng/cột (Row/Column scanning) để minh họa Attention Softmax hay phép nhân ma trận.

### B. TokenRibbonStream (Băng Chuyền Token Tự Hồi Quy)
- Trực quan hóa quá trình Tokenization (BPE/SentencePiece) và cửa sổ ngữ cảnh trượt (Sliding Window Context).
- Các token quá khứ hiển thị màu vàng Gold, token hiện tại phát sáng Cyan Neon, token tương lai bị che mờ.

### C. AutogradDAGGraph (Đồ Thị Tính Toán Đạo Hàm Tự Động)
- Mô phỏng cơ chế Autograd (như trong PyTorch).
- Chiều xuôi (Forward pass): Dữ liệu truyền từ $x, w \rightarrow \text{Loss}$.
- Chiều ngược (Backward pass): Phát xung hạt ánh sáng hồng Rose chạy ngược đồ thị để minh họa Quy tắc dây chuyền (Chain Rule).

---

## 3. KHO CẤU TRÚC HÌNH HỌC 3D (CINEMATIC 3D STRUCTURES)

### A. LossLandscapeSurface3D (Bề Mặt Hàm Mất Mát 3D & Điểm Yên Ngựa)
- Vẽ bề mặt cong 3 chiều tham số hóa: $z = f(x, y)$ (Saddle surface, Paraboloid, Rastrigin).
- Cho phép thả quả cầu Gradient Descent lăn từ đỉnh núi xuống lòng thung lũng, để lại vệt sáng huỳnh quang (Glow trajectory).

```python
class LossSurfaceScene(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=65 * DEGREES, theta=-45 * DEGREES)
        landscape = LossLandscapeSurface3D()
        self.play(Create(landscape.surface), Create(landscape.axes), run_time=2.0)
        self.begin_ambient_camera_rotation(rate=0.15)
        self.wait(3.0)
```

### B. RiemannHypersphere3D (Mặt Cầu Đa Tạp Đơn Vị)
- Khung dây (Wireframe) hình cầu 3 chiều trong suốt.
- Minh họa phép chuẩn hóa L2 norm, hình học Cosine Similarity giữa các vector nhúng (Embeddings) trôi nổi trong không gian.
- Minh họa phép xoay vector phức của kỹ thuật **RoPE (Rotary Position Embedding)** trong mô hình LLaMA.

### C. TransformerTower3D (Tòa Tháp Transformer Xếp Lớp)
- Các khối Multi-Head Attention và Feed-Forward Network được tạo hình như các phiến ngọc bán trong suốt xếp tầng.
- Camera 3D bay lượn quanh tòa tháp để người xem thấy dòng chảy Residual Stream chạy xuyên suốt từ tầng 1 đến tầng $N$.
