---
name: median-animation-director
description: Direct continuous geometry-first Manim explainers and audit their visual pedagogy.
---

# Median Animation Director — canonical migration

Nguồn chuẩn của skill này nằm trong `.agents`. Nội dung chuyên môn được hợp
nhất vào [`../manim-director/SKILL.md`](../manim-director/SKILL.md) và
[`../manim-production/SKILL.md`](../manim-production/SKILL.md). Khi áp dụng,
đọc cả hai file đó và rule
[`../../rules/content_factory_pipeline.md`](../../rules/content_factory_pipeline.md).

Các invariant được giữ từ bản `.trae`:

- câu hỏi và thao tác hình học xuất hiện trước công thức;
- một visual spine sống xuyên các beat, ưu tiên morph hơn reset;
- mọi chuyển động phải biểu diễn quan hệ, biến, nguyên nhân hoặc góc nhìn;
- chốt final audio trước semantic timing;
- kiểm chứng số liệu bằng code có seed trước render;
- automated rubric không phải audio/visual/golden approval;
- preview phải được xem không tiếng và có tiếng;
- production master 2560×1440 @ 60 fps; Short 1440×2560 @ 60 fps.

Không sao chép nhận diện Median và không khẳng định tool/kỹ thuật của họ khi
không có nguồn công khai.
