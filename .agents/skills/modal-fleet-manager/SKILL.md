---
name: modal-fleet-manager
description: Quản trị và giám sát Modal.com Multi-GPU Fleet, kiểm kê 15 Workspace Profiles, điều phối chạy song song 9x T4 GPU, giám sát chi phí MTD và xử lý dừng khẩn cấp worker zombie.
---

# Modal Fleet Manager Skill

Kỹ năng chuyên trách quản lý cụm máy chủ đám mây GPU Modal.com cho Hermes Agent và Content Factory.

## 1. Năng lực chính

- **Kiểm kê 15 Workspace Profiles**: Giám sát phân bổ token trên 2 tài khoản Pro (`just.ask.mr.zen@gmail.com` và `nhatrophamvu@gmail.com`).
- **Giám sát viễn trắc thời gian thực**: Đo lường apps deployed, running containers (workers), và chi phí MTD (USD) qua `scripts/modal_fleet_monitor.py`.
- **Điều phối tác vụ đa luồng**: Phân bổ job round-robin qua 9 profiles active trong `~/.modal.toml` đạt hiệu năng 9x T4 GPU.
- **Bảo vệ chi phí & Dọn dẹp Zombie Workers**: Kiểm tra và chấm dứt các container chạy quá hạn qua `scripts/kill_modal.sh`.

---

## 2. Quy trình thao tác chuẩn

### Bước 1: Quét trạng thái Fleet toàn diện
Chạy công cụ thu thập dữ liệu song song (9 worker threads):
```bash
python3 scripts/modal_fleet_monitor.py
```
Dữ liệu sẽ được lưu tự động tại `output/modal_fleet_status.json`.

### Bước 2: Kiểm tra Workers và Chi phí theo Profile
Chạy với một profile cụ thể:
```bash
# Kiểm tra containers đang chạy trên profile diatts
MODAL_PROFILE=diatts modal container list

# Kiểm tra báo cáo chi phí tháng hiện tại
MODAL_PROFILE=r2rgraph modal billing report --for "this month"
```

### Bước 3: Điều phối SwapFace / Video Pipeline song song
```bash
python3 assets/video-pipeline/dispatch_modal_multiface.py --quality standard
```

### Bước 4: Dừng khẩn cấp khi phát hiện Worker bị treo
```bash
# Dừng các ứng dụng hermes-agent
bash scripts/kill_modal.sh

# Dừng toàn bộ các ứng dụng Modal đang chạy
bash scripts/kill_modal.sh --all
```

---

## 3. Danh mục 15 Workspace Profiles Tham chiếu

Tham khảo tài liệu đầy đủ tại `modal_token_profile.md` và artifact `modal_tokens_inventory.md`.
Tuyệt đối tuân thủ **Rule 05**: Không tự ý xóa hoặc thay đổi (rotate) master token của tác giả.
