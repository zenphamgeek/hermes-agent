# Cẩm Nang Hệ Sinh Thái Thư Viện Manim Science & Kho Mẫu Dựng Sẵn (Science Pattern Catalog)

> **Kiến trúc Hub-and-Spoke**: Tài liệu này đóng vai trò Spoke mở rộng cho Skill `manim-production`. Mọi diễn hoạt khoa học trong tài liệu này đều phải tuân thủ chuẩn **Bố cục 4 Phân Vùng** (Zone 1 Tracker, Zone 2 Visual Canvas 60%, Zone 3 Cognitive Stack 40%, Zone 4 Takeaway Card, Subtitle Zone $Y < -2.6$) và bảng màu Neo-Noir `ZenPalette`.

---

## 1. Bản Đồ Hệ Sinh Thái Khoa Học Cho Manim (Ecosystem Map)

| Lĩnh vực | Thư viện / Nguồn Mã Mẫu | Khả năng Cốt Lõi | Cài đặt / Truy cập |
| :--- | :--- | :--- | :--- |
| **Vật lý 2D & Cơ học** | `manim-physics` | Cơ học vật rắn (Pymunk), va chạm, con lắc, trọng trường, điện tích, từ trường Lorentz, quang hình học | `pip install manim-physics` |
| **Hóa học & Phân tử** | `manim-Chemistry` | Phân tử 2D/3D (`.mol`, `.sdf`, PubChem CID), bảng tuần hoàn động, orbital $s, p, d$, phản ứng bẻ liên kết | `pip install manim-chemistry` |
| **AI & Machine Learning**| `manim-ml` | Diễn hoạt lớp CNN (Feature Maps), Transformer Self-Attention, Feedforward, luồng dữ liệu tensor | `pip install manim-ml` |
| **Giải thuật & Đồ thị** | `networkx` + `Manim Graph` | Tự động tính tọa độ Spring/Kamada-Kawai cho đồ thị, đường đi ngắn nhất Dijkstra, cây nhị phân | `pip install networkx` |
| **Toán học 3B1B** | Kho mã `3b1b/videos` | Đại số tuyến tính, biến đổi ma trận không gian, tích phân vi phân, biến đổi Fourier, giải tích phức | [GitHub: 3b1b/videos](https://github.com/3b1b/videos) |
| **Kho mẫu cộng đồng** | `AnimationsWithManim` | Hơn 50+ tutorial và animation mẫu về hình học, lượng giác, vật lý sóng | [GitHub: Theorem-of-Beethoven](https://github.com/Theorem-of-Beethoven/AnimationsWithManim) |
| **Toán hình thức Python** | `sympy` | Rút gọn đại số, giải phương trình vi phân và xuất trực tiếp ra chuỗi LaTeX `MathTex(sp.latex(expr))` | `pip install sympy` |

---

## 2. Chi Tiết Từng Lĩnh Vực & Mẫu Code Chuẩn Mực

### 2.1. Vật Lý: `manim-physics` & Cơ Học Mô Phỏng

#### A. Trọng trường & Va chạm vật rắn (Rigid Mechanics)
`manim-physics` tích hợp engine 2D Pymunk, cho phép các vật thể rơi, va chạm và nảy theo định luật Newton:
```python
from manim import *
from manim_physics import *

class RigidBodyScene(SpaceScene):
    def construct(self):
        # Thiết lập mặt sàn tĩnh (StaticBody)
        ground = Line(LEFT * 4, RIGHT * 4, color=GRAY).shift(DOWN * 2)
        ground.body_type = "static"
        
        # Vật thể rơi có trọng lực (DynamicBody)
        ball = Circle(radius=0.3, fill_color=RED, fill_opacity=1.0).shift(UP * 2.5 + LEFT * 1)
        
        self.add(ground, ball)
        self.make_rigid_body(ball)
        self.make_static_body(ground)
        
        # Mô phỏng diễn ra tự động trong SpaceScene
        self.wait(3.0)
```

#### B. Điện từ học (Electromagnetism)
Vẽ đường sức từ của nhiều hạt điện tích hoặc nam châm:
```python
from manim import *
from manim_physics import *

class ElectricFieldScene(Scene):
    def construct(self):
        # Hạt điện tích dương và âm
        charge_pos = Charge(+1, point=LEFT * 2, color=RED)
        charge_neg = Charge(-1, point=RIGHT * 2, color=BLUE)
        
        # Tạo lưới vector đường sức điện
        field = ElectricField(charge_pos, charge_neg)
        
        self.play(FadeIn(charge_pos), FadeIn(charge_neg))
        self.play(Create(field), run_time=2.0)
        self.wait()
```

#### C. Quang học (Ray Optics)
Mô phỏng chùm tia sáng đi qua thấu kính hội tụ:
```python
from manim import *
from manim_physics import *

class OpticsScene(Scene):
    def construct(self):
        lens = Lens(focal_length=2.5, width=0.4, height=3.5).shift(ORIGIN)
        rays = [Ray(start=LEFT * 4 + UP * y, direction=RIGHT) for y in [-1, -0.5, 0.5, 1]]
        
        self.add(lens)
        for ray in rays:
            self.play(Create(ray), run_time=0.5)
```

---

### 2.2. Hóa Học: `manim-Chemistry` & Cấu Trúc Phân Tử

#### A. Phân tử 2D từ file hoặc PubChem
```python
from manim import *
from manim_chemistry import *

class Molecule2DScene(Scene):
    def construct(self):
        # Tải cấu trúc phân tử (ví dụ: Caffeine qua PubChem hoặc file mol)
        # manim-chemistry hỗ trợ chuyển đổi tệp .mol thành VMobject hoàn chỉnh
        caffeine = MMoleculeObject.from_pubchem("caffeine")
        caffeine.scale(0.8).shift(LEFT * 2.5)
        
        self.play(Create(caffeine), run_time=2.5)
        self.wait()
```

#### B. Mô hình Bohr & Cấu hình Electron
```python
from manim import *
from manim_chemistry import *

class BohrAtomScene(Scene):
    def construct(self):
        # Nguyên tử Carbon (Z=6, 2 electron lớp K, 4 electron lớp L)
        carbon = BohrAtom(
            protons=6,
            neutrons=6,
            electron_configuration=[2, 4],
            radius=2.0
        ).shift(LEFT * 2.5)
        
        self.play(FadeIn(carbon), run_time=1.5)
        self.play(Rotate(carbon.electrons, angle=2*PI, run_time=4, rate_func=linear))
```

---

### 2.3. Trí Tuệ Nhân Tạo & Deep Learning: `manim-ml`

`manim-ml` cung cấp các khối xây dựng cấp cao cho kiến trúc mạng nơ-ron:
```python
from manim import *
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer, Convolutional2DLayer

class MLArchitectureScene(Scene):
    def construct(self):
        nn = NeuralNetwork([
            Convolutional2DLayer(1, 28, filter_size=3, num_filters=4),
            FeedForwardLayer(16),
            FeedForwardLayer(10)
        ])
        nn.scale(0.75).shift(LEFT * 2.5)
        
        self.play(Create(nn), run_time=2.0)
        # Diễn hoạt dòng chảy dữ liệu (forward pass animation)
        forward_pass = nn.make_forward_pass_animation()
        self.play(forward_pass, run_time=3.0)
```

---

### 2.4. Cấu Trúc Dữ Liệu & Giải Thuật: `networkx` $\rightarrow$ `Manim Graph`

Sử dụng thuật toán sắp đặt tự động của `networkx` để bố trí đồ thị đẹp mắt:
```python
from manim import *
import networkx as nx

class AlgoGraphScene(Scene):
    def construct(self):
        # Tạo đồ thị bằng networkx
        G = nx.karate_club_graph()
        
        # Bố trí tọa độ bằng Kamada-Kawai hoặc Spring layout
        pos = nx.spring_layout(G, scale=2.5)
        
        # Chuyển sang Manim Graph
        vertices = list(G.nodes())
        edges = list(G.edges())
        layout_dict = {v: np.array([pos[v][0] - 2.5, pos[v][1], 0]) for v in vertices}
        
        graph = Graph(
            vertices,
            edges,
            layout=layout_dict,
            vertex_config={"radius": 0.12, "fill_color": YELLOW},
            edge_config={"stroke_width": 1.5, "stroke_color": GRAY}
        )
        
        self.play(Create(graph), run_time=2.5)
        self.wait()
```

---

### 2.5. Toán Học Cao Cấp: Tinh Hoa 3Blue1Brown

#### A. Biến đổi ma trận không gian 2D (Linear Transformation)
```python
from manim import *

class LinearTransformationScene(LinearTransformationScene):
    def __init__(self):
        LinearTransformationScene.__init__(
            self,
            show_coordinates=True,
            leave_ghost_vectors=True,
            show_basis_vectors=True
        )

    def construct(self):
        # Ma trận biến đổi xoay và kéo dãn: [[1, 2], [2, 1]]
        matrix = [[1, 2], [2, 1]]
        self.apply_matrix(matrix)
        self.wait()
```

#### B. Tích phân & Đạo hàm trực quan (Calculus Riemann Sums)
```python
from manim import *

class RiemannIntegralScene(Scene):
    def construct(self):
        ax = Axes(x_range=[0, 5], y_range=[0, 10], x_length=5, y_length=3.5).shift(LEFT * 2.5)
        curve = ax.plot(lambda x: 0.4 * x**2 + 0.5, color=YELLOW)
        
        # Tổng tích phân Riemann với số cột tăng dần
        rects_coarse = ax.get_riemann_rectangles(curve, x_range=[0.5, 4.5], dx=1.0, color=BLUE, fill_opacity=0.5)
        rects_fine = ax.get_riemann_rectangles(curve, x_range=[0.5, 4.5], dx=0.1, color=GREEN, fill_opacity=0.5)
        
        self.play(Create(ax), Create(curve))
        self.play(Create(rects_coarse))
        self.wait(1)
        self.play(Transform(rects_coarse, rects_fine), run_time=2)
        self.wait()
```

---

## 3. Quy Tắc Ráp Vào Bố Cục 4 Phân Vùng

Khi đưa bất kỳ animation khoa học nào vào video sản xuất thực tế:
1. **Sân khấu thị giác (Visual Canvas)**: Đặt toàn bộ mô hình (phân tử, mạng nơ-ron, con lắc, đồ thị) lệch sang trái:
   `mobject.scale_to_fit_width(6.0).move_to(np.array([-2.5, 0.4, 0]))`
2. **Tháp nhận thức (Cognitive Stack bên phải)**:
   - Đặt `ConceptBadge` tại $X \approx +3.8, Y \approx +2.3$.
   - Đặt `EquationBox` hoặc bảng quy tắc tại $X \approx +3.8, Y \approx +0.5$.
3. **Thanh trạng thái (StateTrackerBar trên đỉnh)**:
   - Luôn tóm tắt bài giảng thành 4-6 từ khóa ngắn đặt ở $Y \approx +3.3$.
4. **Thẻ đúc kết (BottomCalloutCard)**:
   - Đặt ở $Y \approx -2.1$, không vượt quá $-2.4$.
