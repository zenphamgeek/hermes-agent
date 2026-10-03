# Chọn visual đúng nội dung và cấm slide-deck Manim

Áp dụng cho nghiên cứu, storyboard, thư viện component và review video Content Factory, gồm ManimCE, ManimGL, AE và SVG. Đây là tiêu chí thiết kế/nghiệm thu; không tuyên bố các kiểm tra dưới đây đã được triển khai tự động.

## Quan hệ với rule hiện có

Kế thừa yêu cầu hình trước công thức, đồng bộ lời–hình và chống hộp chữ trong [pedagogy_and_simulation_rules.md](pedagogy_and_simulation_rules.md), cùng chống motion giả và false-green trong [manim_masterclass_rules.md](manim_masterclass_rules.md).

Theo yêu cầu người dùng về visual đúng chủ đề, “hero geometry” phải được hiểu là **thực thể của nội dung**, không phải bắt buộc mọi cảnh có đồ thị/vector. Giải thích cơ thể cần cơ thể; máy nhiệt cần cơ cấu; thuật toán cần dữ liệu và phép biến đổi. Các danh sách hình học AI trong rule cũ là ví dụ trong phạm vi AI, không phải danh sách hợp lệ duy nhất cho sinh học. Giữ Roboto Regular theo yêu cầu người dùng; bold chỉ khi có lý do nhấn mạnh rõ ràng.

Tỷ lệ diện tích, số mobject, phần trăm motion, số dòng code và điểm AST trong tài liệu cũ không chứng minh sự phù hợp hay mỹ thuật. Không thêm chuyển động để đạt quota. Khoảng dừng đọc/quan sát có chủ đích phải được ghi trong beat; nếu gate hiện hành từ chối, báo xung đột để sửa gate đúng phạm vi, không dùng glow, camera sway hoặc hạt vô nghĩa để lách.

## Thiết kế từ thực thể đến phép đo

Mỗi phân đoạn giải thích phải mô tả chuỗi:

1. **Thực thể:** người xem nhận ra vật/đối tượng đang được nói tới ở đâu và trạng thái ban đầu của nó.
2. **Cơ chế:** bộ phận hoặc quan hệ nào tác động lên bộ phận nào; chiều mũi tên biểu thị tín hiệu, lực, vật chất hay dữ liệu phải xác định.
3. **Biến đổi:** cho thấy điều gì thay đổi ở cùng đối tượng; giữ neo không gian và quan hệ nhân quả qua các beat.
4. **Phép đo:** sau khi hiểu hiện tượng, hiện đại lượng cần đo, đơn vị và đồ thị liên kết trực tiếp với đối tượng. Không bắt buộc thêm số/công thức nếu không giúp trả lời câu hỏi.

Ví dụ thiết kế cho chủ đề sốt: dùng cơ thể người làm neo; chỉ rõ bộ phận được giải thích bằng cutaway hoặc highlight; trình bày thay đổi trạng thái; sau đó liên kết nhiệt kế/đồ thị với diễn tiến tương ứng. Đây là cấu trúc visual đề xuất, không phải bằng chứng sinh lý. Mọi phát biểu về điều hòa nhiệt, cơ chế phản ứng hoặc mức nhiệt cụ thể phải có nguồn chuyên môn trước khi duyệt lời thoại.

Beat phải ghi câu thoại, đối tượng được nhắc, trạng thái trước/sau, thao tác chuyển động, điều kiện bắt đầu, thời gian quan sát và cách chuyển tiếp. Timing nháp phải ghi là ước tính; bản sản xuất căn theo audio alignment thực.

## Chọn engine và tài sản

| Nhu cầu | Quyết định có điều kiện |
|---|---|
| Dữ liệu, đồ thị, phương trình, hình học định lượng | ManimCE; tham số hình và số lấy từ cùng mô hình, kiểm tra đơn vị và giới hạn |
| Mesh/camera 3D, nhiều đối tượng | Thử khả năng ManimCE/ManimGL trên chính asset và cảnh cần dùng; đo runtime/GPU trước chốt, không suy tốc độ từ tên engine |
| Cơ thể người, nội tạng, cử động khớp | Cần mesh/rig hoặc mô hình minh họa có nguồn; “Manim 3D” không đồng nghĩa có thư viện giải phẫu hay bộ rig người dựng sẵn |
| Silhouette, sơ đồ bộ phận, icon | SVG làm asset cho engine điều khiển; không gọi SVG là rig 3D |
| Compositing, typography, particles, âm thanh | AE khi host/plugin đã xác minh; không dùng VFX thay cơ chế thiếu |

Mô hình cơ thể trong suốt hoặc giản lược được phép nếu đủ nhận diện và phục vụ cơ chế. Phải ghi rõ mức giản lược; không quảng bá như mô hình lâm sàng chính xác. Nếu vị trí/tỷ lệ bộ phận có ảnh hưởng đến lời giải thích thì phải kiểm chứng, không lấy sự “đẹp” làm bằng chứng đúng. Màu/glow là mã nhấn mạnh, không được ngầm tạo ra bản đồ nhiệt hay trường vật lý thực nếu không có dữ liệu/mô hình.

Mỗi repo/asset ứng viên cần URL nguồn, phiên bản/commit, license và yêu cầu attribution, định dạng, skeleton/rig nếu có, giới hạn giải phẫu, dependency/runtime đã kiểm tra. Không gộp license mã nguồn với license của mesh/texture đi kèm. Giữ các mức **candidate → imported → rendered → reviewed → approved** riêng và kèm bằng chứng; chỉ dùng “approved” khi có review gắn đúng artifact/phiên bản. Có file hay video demo trên GitHub không chứng minh đã chạy trong engine local.

Với cơ thể người, nguồn chuẩn hiện tại là subset đã kiểm chứng của Z-Anatomy,
theo `assets/research/mathoholic_ch/human_body_3d_policy.json`. Blender xử lý
mesh và render; AE compositing; ManimCE dựng lớp định lượng. Mọi part mặc định
bị chặn cho tới khi manifest chứng minh provenance và quyền sử dụng. Atlas
không có armature nên cấm suy diễn rằng có thể tạo chuyển động khớp hoặc run cơ
chỉ bằng cách nhập mesh.

## Các mẫu bị loại

- Chuỗi tiêu đề, bullet hoặc thẻ giải thích thay nhau xuất hiện làm nội dung chính; đổi FadeIn/FadeOut thành Transform vẫn là slide deck nếu cơ chế không diễn tiến.
- Hộp đoạn văn lớn để người xem đọc lại toàn bộ lời thoại; hình nhỏ trang trí bên cạnh không chữa được lỗi này.
- Công thức, vector, mặt lưới hoặc particles không có quan hệ với điều đang nói. Cảnh sốt không đạt chỉ vì có đồ thị đẹp nhưng thiếu cơ thể và cơ chế.
- Camera trôi, scale phồng xẹp, bóng sai vật lý, particle/glow nhằm che cảnh tĩnh hoặc vượt kiểm tra freeze.
- Đổi số đo độc lập với hình; mũi tên sai hướng; khớp/bộ phận đứt rời; dùng giá trị định lượng không nguồn hoặc không ghi giả định.

Nhãn ngắn, đơn vị, chú thích bộ phận và dữ liệu so sánh cần thiết được phép khi gắn với đối tượng và hiện đúng lúc. Một card chứa số đo không tự động vi phạm; cả chuỗi chỉ dựa vào card đọc chữ thì bị loại. Opener/CTA dùng template đã được duyệt trong phạm vi của chúng; không tính chúng làm bằng chứng cảnh giải thích đạt, không tự sửa golden brand clips.

## Gate kiểm chứng bằng chuỗi thời gian

Review phải xem các đoạn chuyển động có timecode cùng audio, gồm trước–trong–sau từng biến đổi quan trọng và các đoạn chuyển cảnh. Keyframe chỉ hỗ trợ bố cục; không đủ kết luận chuyển động hay AV sync đúng. Nếu công cụ chỉ có ảnh, ghi **chưa kiểm chứng motion/audio**, không duyệt thay bằng suy đoán.

Hồ sơ review ghi artifact và hash/phiên bản, khoảng đã quan sát, người/agent review, evidence có thể truy lại, lỗi cụ thể tại timecode, quyết định và phần chưa xem. Đối chiếu:

- Người xem có nhận ra thực thể và giải thích được thay đổi từ hình, thay vì chỉ đọc chữ?
- Mỗi lời nhắc có đối tượng và hành động tương ứng đúng lúc; có thời gian quan sát trước khi thêm ý mới?
- Hình, số đo và đơn vị có nhất quán; các giản lược sinh lý/cơ học có được công khai đúng mức?
- Chữ Việt có dấu và khoảng cách đúng ở cả khung ngang/dọc; nhãn không che cơ chế; SFX không che thoại?
- Chuỗi giải thích có đang bị thay bằng slide/card, kể cả khi AST chứa nhiều hình học?

Thiếu bằng chứng thì giữ pending; sai cơ chế, sai đồng bộ hoặc slide-deck thì yêu cầu sửa. Không dùng keyword, số điểm tự khai, Python validator hoặc exit code để cấp mỹ thuật “premium”. Test phần mềm chỉ hỗ trợ kiểm tra cấu trúc, số liệu và bất biến có thể đo; approval nội dung/visual cần evidence thật và đúng phạm vi.

Nghiên cứu và cảnh thử kỹ thuật không tự cấp quyền bắt đầu episode. Series Planner vẫn phải được duyệt trước sản xuất episode theo quy tắc hiện hành.
