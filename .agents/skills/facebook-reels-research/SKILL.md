---
name: facebook-reels-research
description: Nghiên cứu Reels Facebook bằng phiên trình duyệt của người dùng, lập danh mục có bằng chứng, phân tích cảnh và thiết kế storyboard ZenPham bằng ManimCE, ManimGL, AE hoặc SVG; hỗ trợ bàn giao các đợt nghiên cứu cho agent song song.
---

# Facebook Reels → nghiên cứu visual ZenPham

Dùng cho khảo sát video và biên soạn bản nháp có bằng chứng. Đường dẫn quy tắc/skill dùng chung là `.agents/`. Nghiên cứu không tự mở quyền xuất bản, sản xuất episode hoặc thay đổi Series Planner.

## Bắt đầu hoặc tiếp nhận bàn giao

Đọc `assets/research/mathoholic_ch/README.md`, `VISUAL_SPEC.md`, `ENGINE_AUDIT.md` và `research.py` trong cùng thư mục. Đây là ledger đang dùng; với kênh khác, xác định ledger tương ứng trước khi chạy lệnh vì script hiện gắn cứng Mathoholic.ch. Đọc trạng thái thật trong catalog và hồ sơ, không lấy số đếm từ câu trả lời cũ.

Khi chạy nhiều agent, đọc [giao thức song song](references/parallel-work.md) trước khi nhận đợt. Coordinator giữ quyền ghi danh mục/báo cáo; mỗi worker chỉ nhận một tập ID riêng. Không tự mở thêm agent khi không có yêu cầu hoặc quyền delegation phù hợp.

## Thu thập nguồn

1. Dùng browser tool thật đang có; đọc tài liệu API và inventory tab trước khi chọn tab. Tái sử dụng phiên Facebook người dùng đã đăng nhập, không yêu cầu đăng nhập lại nếu chưa kiểm tra. Không xuất cookie/token hoặc truy cập trạng thái app ẩn.
2. Xác minh tên trang và URL trong UI. Lấy nguyên `href` từ anchor DOM của Reel; cây accessibility có thể cắt ngắn ID. Không suy URL từ text bị truncate. Lưu URL nguồn, URL chuẩn hóa, thời điểm và cách thu thập; dùng Reel ID làm khóa khử trùng.
3. Cuộn lưới theo phần, thu ID mới và ghi checkpoint. Một lần không thấy ID mới không chứng minh hết kênh: kiểm tra tải, UI cuối danh sách và ít nhất một lần thử tiếp. Nếu có login wall/lỗi tải, ghi điểm dừng và giữ `channel_inventory_complete=false`.
4. Coordinator thêm URL bằng `python3 assets/research/mathoholic_ch/research.py add URL [URL ...]`. Worker gửi URL mới trong kết quả đợt; không tự chạy `add` trên ledger chung.

Chỉ thu nội dung thuộc nhiệm vụ: video, mô tả và metadata liên quan. Feed cá nhân, tin nhắn và thông tin tài khoản không phải nguồn nghiên cứu.

## Hồ sơ từng video

Giữ ba lớp tách biệt: `observations` là điều thấy/nghe trực tiếp; `inferences` là suy luận kèm độ tin cậy/giới hạn; `proposed_beats` là thiết kế mới. Không suy engine gốc từ vẻ ngoài. Tên tự đặt dùng `title_kind=descriptive`; ngày/thời lượng chưa rõ để `null`.

- **Xem đủ:** ghi đoạn đã xem, thời lượng player, bằng chứng bắt đầu/kết thúc và toàn bộ khoảng thời gian được quan sát; frame rời rạc không đủ chứng minh chuyển động liên tục. Nếu công cụ chỉ chụp được frame, ghi phân tích frame, không bật `watched_full`.
- **Âm thanh/transcript:** mô tả bài đăng hoặc OCR không phải transcript. Chỉ dùng audio nghe được hoặc phụ đề/ASR có provenance; đánh dấu phần không chắc, kiểm tra thuật ngữ. Không điền SFX/giọng/CTA cuối khi chưa nghe được. Ghi `kind=audio_transcript` chỉ khi thực sự chép từ audio, không đổi nhãn để qua validator.
- **Cảnh nguồn:** timecode, câu thoại, text, vật thể, motion, camera, transition, audio, chức năng giải thích. Timecode chưa xác minh để `null`. Ghi hook, câu hỏi trung tâm, cách triển khai cơ chế/ví dụ, kết luận và CTA; phần chưa xem để unknown.
- **Kiểm chứng:** tách từng claim được giữ, tìm nghiên cứu gốc hoặc tổ chức chuyên môn, ghi URL, nội dung nguồn hỗ trợ và quyết định giữ/sửa/loại. Phân biệt mô hình minh họa với cơ chế thực; đừng đánh dấu cả video đúng chỉ vì một claim có nguồn.
- **Bản ZenPham:** người 22–40 tuổi; một câu hỏi trung tâm và ví dụ dễ hiểu. Viết độc lập, không sao chép nguyên kịch bản nguồn. Mỗi beat có câu Việt chứa thuật ngữ Anh nguyên dạng → vật thể → trạng thái trước/sau → hành động → khoảng quan sát → chuyển cảnh. Timing draft là ước tính; timing sản xuất dựa audio alignment.

## Chọn engine và tái sử dụng

Đọc và áp dụng [quy tắc visual đúng nội dung](../../rules/content_visual_suitability.md): chọn thực thể của chủ đề → cơ chế → biến đổi → phép đo; cấm chuỗi slide-deck và hình học trang trí. Cơ thể 3D cần asset/rig đã kiểm tra, không suy Manim có sẵn giải phẫu. Phân biệt ứng viên với bản đã render/duyệt; gate cần chuỗi thời gian và audio thật, không duyệt bằng keyword hay chỉ ảnh.

Đối chiếu `assets/manim_library`, `assets/manim`, `assets/ae_library` và backlog trước khi tạo component. Đọc mã/runtime thực; có file, import được, render được và được duyệt là bốn mức khác nhau. Audit cũ phải được tái kiểm tra trước khi hứa khả năng runtime.

| Nhu cầu | Tuyến đề xuất và điều kiện |
|---|---|
| Công thức, đồ thị, mô phỏng định lượng | ManimCE; kiểm tra MathTex và tính đúng mô hình |
| Hình học 3D hoặc nhiều đối tượng | ManimGL sau cảnh thử đo hiệu năng đúng runtime; không mặc định nhanh hơn |
| Typography, camera, compositing, particles, SFX | AE khi host/plugin được xác minh; fallback phải nêu phần mất đi |
| Icon, sơ đồ, silhouette | SVG là asset; engine đích điều khiển motion |
| Giải phẫu/mesh phức tạp | Cần tài sản phù hợp và nguồn/quyền dùng; không giả định vài nét SVG thay thế được |

Roboto Regular, tiếng Việt NFC, không animation rời dấu; bỏ metadata sản xuất trên hình. Mỗi VFX/SFX phải phục vụ lời giải thích. Đo chữ bằng font render, kiểm tra nhãn và vật lý trước làm đẹp. Backlog ghi tham số, nguồn asset, engine, cảnh mẫu và tiêu chí kiểm chứng; tách designed/implemented/rendered/approved.

## Hoàn tất đợt và bàn giao

Hồ sơ chưa đủ phải có `pending_reason` cụ thể và bước tiếp theo. Evidence `supports` phải đúng trạng thái mà nó chứng minh; không tạo bằng chứng giả để validator xanh. Coordinator chạy `validate` rồi `report`; `validate --require-complete` còn lỗi là kết quả hợp lệ nếu khảo sát chưa hoàn tất. Validator chỉ kiểm tra ledger, không chứng nhận chất lượng nội dung.

Handoff ghi: phạm vi ID, file đã sửa, bằng chứng đã thu, phần chưa xem/nghe, lỗi truy cập, kết quả kiểm tra, claim chưa xác minh, bước kế tiếp và trạng thái claim của đợt. Không lưu credentials hoặc browser session secrets. Báo số đã tìm thấy/xem đủ/chép lời/kiểm chứng/thiết kế riêng; tổng kênh chưa rõ phải nói chưa rõ.

Nếu browser không đọc được audio/video, thử khả năng hợp lệ khác sẵn có và tiếp tục phần độc lập. Chỉ nhờ người dùng cung cấp clip/subtitle hoặc khôi phục đăng nhập khi thiếu khả năng đó thực sự chặn phân tích; không giả định video đang phát đồng nghĩa agent đã nghe/xem. Series Planner chưa được duyệt vẫn cho phép nghiên cứu và storyboard nháp, không cho phép bắt đầu episode hay render hàng loạt.
