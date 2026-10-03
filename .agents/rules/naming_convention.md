# QUY CHUẨN ĐẶT TÊN VÀ CẤU TRÚC THƯ MỤC HỆ THỐNG
## (CANONICAL NAMING CONVENTION & DIRECTORY ARCHITECTURE)
================================================================================

> **QUY TẮC BẤT BIẾN (INVARIANT):**  
> Mọi dự án sản xuất nội dung, mã nguồn, tệp tài nguyên, kịch bản, âm thanh, video kết xuất và lưu trữ đám mây (Google Drive Content Factory) **BẮT BUỘC** phải tuân thủ nghiêm ngặt mô hình phân tầng 4 cấp duy nhất:
> 
> $$\mathbf{Channel} \longrightarrow \mathbf{Series} \longrightarrow \mathbf{Episode} \longrightarrow \mathbf{resources}$$
> 
> Tuyệt đối cấm:
> 1. Lưu trữ file tản mát trực tiếp ở thư mục gốc `assets/scripts_video/` hoặc `Content Factory/` mà không thuộc về một Channel/Series/Episode cụ thể.
> 2. Đặt tên file trùng lặp hoặc generic (`tap_01.mp4`, `script.md`, `thumb.jpg`, `series_02`) mà không có tiền tố nhận diện Channel và Series.
> 3. Trộn lẫn Series của kênh này sang Series của kênh khác (ví dụ: nhầm Series 02 của "Tôi Làm Việc" với Series 02 của "Biết Địa Lý Từ Ba Tôi").

---

## 1. CẤU TRÚC PHÂN TẦNG 4 CẤP (4-TIER HIERARCHY)

```
production_hub/ (hoặc Content Factory/channels/)
└── {channel_id}/
    └── {series_id}/
        └── {episode_id}/
            ├── script/       # Kịch bản Master Markdown, Episode Contract JSON, Outline
            ├── audio/        # Lời thoại WAV từng scene, Mastered Voice EBU R128, Whispers alignment
            ├── visual/       # Code Manim Python, Phosphor Duotone SVG, Clip diễn hoạt 2K
            ├── footage/      # B-roll footage, Video bed 2K ghép nối, shot list
            ├── cover/        # Thumbnail 2K Hero JPG, PSD/SVG source, text layout
            ├── exports/      # Video Master 2K final, SRT subtitles, metadata.json, description.txt
            └── audit/        # Báo cáo kiểm toán độc lập JSON & MD, QA Checklist, Certificate
```

---

## 2. BẢNG ĐỊNH DANH KÊNH (CHANNEL REGISTRY)

| Mã thư mục (`channel_id`) | Tiền tố file (`channel_prefix`) | Tên hiển thị Kênh | YouTube Handle | Định hướng nội dung |
| :--- | :--- | :--- | :--- | :--- |
| `ch_biet_dia_ly` | `geo` | **BIẾT ĐỊA LÝ TỪ BA TÔI** | `@phamtrai-dialy` | Địa lý Việt Nam, cảnh quan địa mạo, bậc thềm sinh kế, nông nghiệp bản địa, văn hóa người Việt |
| `ch_toi_lam_viec` | `tlv` | **TÔI LÀM VIỆC** | `@toilamviec` | Kỹ nghệ AI (AI Engineering), Toán học Machine Learning từ gốc, kiến trúc mô hình, code thực chiến |
| `ch_reality_decode` | `rd` | **REALITY DECODE** | `@reality-decode-officials` | Phim tài liệu trực quan công nghệ chuyên sâu (Deep-Tech Visual Documentary), hạ tầng điện toán, bán dẫn |
| `ch_zenpham` | `zen` | **ZENPHAM** | `@zenpham` | Tiểu luận xã hội, tâm lý học đám đông, triết học đời thường, phản biện công nghệ |
| `ch_toi_doc_sach` | `tds` | **TÔI ĐỌC SÁCH** | `@toidocsach` | Sách kinh điển, triết học cổ điển phương Đông, Nam Hoa Kinh, văn học trầm tư |

---

## 3. BẢNG ĐỊNH DANH SERIES (SERIES REGISTRY)

Mã Series bắt buộc dùng định dạng: `s{NN}_{series_slug}` (trong đó `{NN}` là số thứ tự 2 chữ số: `s01`, `s02`,...).

### 3.1. Kênh `ch_biet_dia_ly`
- `s01_nhung_mien_song`: Việt Nam — Những Miền Sông (10 tập)
- `s02_bac_them_dia_hinh`: Việt Nam — Những Bậc Thềm Địa Hình & Dòng Chảy Sinh Kế (10 tập)
- `s03_hai_dao_bien_dong`: Việt Nam — Những Bờ Cõi & Hải Đảo Tiền Tiêu (Kế hoạch)

### 3.2. Kênh `ch_toi_lam_viec`
- `s01_math_ai_from_scratch`: Toán Học & Nền Tảng Kỹ Nghệ AI Từ Gốc (25 tập)
- `s02_llm_internals`: Kiến Trúc Mô Hình Ngôn Ngữ Lớn Thực Chiến (Tokenization, RoPE, Attention...)
- `s03_agentic_workflow`: Xây Dựng Hệ Thống Multi-Agent Tự Hành

### 3.3. Kênh `ch_reality_decode`
- `s01_math_of_reality`: Những Nghịch Lý Toán Học Thay Đổi Vũ Trụ (Khách Sạn Vô Hạn, Liên Tục Thể...)
- `s02_compute_infrastructure`: Đại Chiến Bán Dẫn & Cỗ Máy Siêu Điện Toán

---

## 4. BẢNG ĐỊNH DANH EPISODE (EPISODE REGISTRY)

Mã Episode bắt buộc dùng định dạng: `ep{NN}_{episode_slug}` (trong đó `{NN}` là số thứ tự 2 chữ số: `ep01`, `ep02`,...).

### Ví dụ danh mục chính thức cho `ch_biet_dia_ly/s02_bac_them_dia_hinh`:
- `ep01_dong_van_karst_1500m`: Cao Nguyên Đá Đồng Văn — Bậc Thềm 1.500m & Kỳ Tích Cây Ngô Hốc Đá
- `ep02_muong_thanh_basin_450m`: Thung Lũng Mường Thanh & Mường Lò — Vựa Lúa Giữa Lòng Chảo Tây Bắc 450m
- `ep03_moc_chau_plateau_1050m`: Cao Nguyên Mộc Châu — Bậc Thềm Ôn Đới & Thảo Nguyên Xanh 1.050m
- `ep04_ban_gioc_waterfall_400m`: Thác Bản Giốc & Trầm Tích Karst Biên Cương 400m
- `ep05_tam_dao_cloud_island_900m`: Đảo Mây Tam Đảo — Bậc Thềm Rừng Lạnh Giữa Châu Thổ Bắc Bộ
- `ep06_hai_van_climate_divide_500m`: Đèo Hải Vân — Ranh Giới Khí Hậu & Bức Bình Phong Hoa Cương
- `ep07_lam_vien_dalat_1500m`: Cao Nguyên Lâm Viên — Thủ Phủ Rau Hoa & Khí Hậu Ôn Đới Miền Nam
- `ep08_dak_lak_basalt_500m`: Bán Bình Nguyên Đắk Lắk — Đất Đỏ Bazan & Dòng Chảy Cà Phê
- `ep09_di_linh_tea_hills_1000m`: Bậc Thềm Di Linh — Sương Mù Bảo Lộc & Cây Trà B'Lao
- `ep10_that_son_delta_mountains`: Thất Sơn An Giang — Những Hòn Đảo Đá Nổi Giữa Biển Lúa Tây Nam Bộ

---

## 5. CẤU TRÚC THƯ MỤC TÀI NGUYÊN NỘI BỘ (`resources`)

Mỗi tập phim là một đơn vị độc lập hoàn chỉnh chứa 7 thư mục chuẩn:

```
{episode_id}/
├── script/
│   ├── {prefix}_{sXX}_{epXX}_script_master.md       # Kịch bản 11 phân đoạn hoàn chỉnh
│   ├── {prefix}_{sXX}_{epXX}_contract.json          # Episode contract (beats, voice anchors)
│   └── {prefix}_{sXX}_{epXX}_outline.md             # Đề cương sư phạm & đối chiếu thực địa
│
├── audio/
│   ├── scenes/                                      # WAV thu âm từng phân cảnh (scene_01 -> scene_11)
│   │   ├── scene_01.wav, scene_01.txt, scene_01.meta.json
│   │   └── ...
│   ├── {prefix}_{sXX}_{epXX}_voice_master_48k.wav   # Voice Mastered 48kHz Stereo EBU R128 (-14.5 LUFS)
│   └── {prefix}_{sXX}_{epXX}_alignment.json         # Timestamp đồng bộ từng từ (Whisper word-level)
│
├── visual/
│   ├── src/                                         # Mã nguồn Manim Python
│   │   └── {prefix}_{sXX}_{epXX}_manim_scenes.py
│   ├── duotone_icons/                               # Các icon Phosphor Duotone SVG dùng riêng
│   └── clips/                                       # Video render Manim 2K QHD (2560x1440 @ 30fps)
│       ├── {prefix}_{sXX}_{epXX}_manim_sc02_elevation_2k.mp4
│       ├── {prefix}_{sXX}_{epXX}_manim_sc05_biology_2k.mp4
│       └── {prefix}_{sXX}_{epXX}_manim_sc09_economy_2k.mp4
│
├── footage/
│   ├── selects/                                     # Các đoạn video B-roll chất lượng cao đã chọn lọc
│   ├── shots/                                       # 30-40 shots cắt gọt 2K theo timeline kịch bản
│   └── {prefix}_{sXX}_{epXX}_video_bed_2k.mp4       # Video bed hoàn chỉnh ghép nối từ footage + manim
│
├── cover/
│   ├── {prefix}_{sXX}_{epXX}_thumb_hero_2k.jpg      # Thumbnail chính thức 2560x1440 (<2MB)
│   ├── {prefix}_{sXX}_{epXX}_thumb_preview.jpg      # Bản preview 1280x720 cho QA
│   └── generator.py                                 # Script tái lập thumbnail tự động
│
├── exports/
│   ├── {prefix}_{sXX}_{epXX}_final_master_2k.mp4    # BẢN MASTER XUẤT XƯỞNG (2560x1440, audio ducking)
│   ├── {prefix}_{sXX}_{epXX}_subtitles.srt          # Phụ đề chuẩn SRT (đầy đủ cue <14 từ, ngắt câu tự nhiên)
│   ├── {prefix}_{sXX}_{epXX}_metadata.json          # Manifest phát hành (title, tags, category, chapters)
│   └── {prefix}_{sXX}_{epXX}_description.txt        # Mô tả hoàn chỉnh 4 phần sẵn sàng upload
│
└── audit/
    ├── {prefix}_{sXX}_{epXX}_audit_report.json      # Báo cáo kết quả kiểm toán 7 trục độc lập
    ├── {prefix}_{sXX}_{epXX}_audit_report.md        # Bản báo cáo markdown kèm biểu đồ & checklist
    └── audit_runner.py                              # Script chạy kiểm toán độc lập cho tập
```

---

## 6. QUY CHUẨN ĐẶT TÊN FILE NGUYÊN TỬ (ATOMIC FILE NAMING CONVENTION)

Tất cả các tệp sinh ra phải tuân thủ nghiêm ngặt định dạng nhận diện 5 thành phần:

$$\mathbf{\{channel\_prefix\}\_\{series\_id\}\_\{episode\_id\}\_\{component\}\_\{spec\}.\{ext\}}$$

Trong đó:
1. `{channel_prefix}`: Tiền tố kênh (`geo`, `tlv`, `rd`, `zen`, `tds`).
2. `{series_id}`: Mã series ngắn gọn (`s01`, `s02`,...).
3. `{episode_id}`: Mã tập ngắn gọn (`ep01`, `ep02`,...).
4. `{component}`: Thành phần tài nguyên (`script`, `voice`, `manim`, `video_bed`, `thumb`, `final`, `srt`, `meta`, `audit`).
5. `{spec}`: Quy cách kỹ thuật (`master`, `48k`, `2k`, `hero`,...).
6. `{ext}`: Phần mở rộng tệp (`.md`, `.json`, `.wav`, `.mp4`, `.jpg`, `.srt`).

### Bảng tra cứu tên file mẫu cho `ch_biet_dia_ly / s02 / ep02`:
- Kịch bản: `geo_s02_ep02_script_master.md`
- Episode Contract: `geo_s02_ep02_contract.json`
- Voice Master: `geo_s02_ep02_voice_master_48k.wav`
- Clip Manim Lát cắt: `geo_s02_ep02_manim_sc02_elevation_2k.mp4`
- Video Bed nền: `geo_s02_ep02_video_bed_2k.mp4`
- Thumbnail Hero 2K: `geo_s02_ep02_thumb_hero_2k.jpg`
- Video Master Xuất xưởng: `geo_s02_ep02_final_master_2k.mp4`
- Phụ đề YouTube CC: `geo_s02_ep02_subtitles.srt`
- Manifest Xuất bản: `geo_s02_ep02_metadata.json`
- Báo cáo kiểm toán: `geo_s02_ep02_audit_report.json`

---

## 7. CẤU TRÚC ĐỒNG BỘ LÊN GOOGLE DRIVE CONTENT FACTORY

Trên remote `phamvuthang@gmail.com:Content Factory`, tài nguyên được phân bổ trực tiếp theo cây phả hệ Kênh:

```
Content Factory/
├── channels/
│   ├── ch_biet_dia_ly/
│   │   ├── s01_nhung_mien_song/
│   │   └── s02_bac_them_dia_hinh/
│   │       ├── ep01_dong_van_karst_1500m/
│   │       ├── ep02_muong_thanh_basin_450m/
│   │       └── ep03_moc_chau_plateau_1050m/
│   ├── ch_toi_lam_viec/
│   │   └── s01_math_ai_from_scratch/
│   ├── ch_reality_decode/
│   │   └── s01_math_of_reality/
│   └── ch_zenpham/
│       └── s01_triet_hoc_doi_thuong/
│
└── global_resources/               # Tài nguyên dùng chung toàn nhà máy
    ├── duotone_icons/              # Bộ Phosphor Duotone SVG icons
    ├── background_music/           # Kho nhạc bản quyền đã kiểm định
    ├── sound_effects/              # Thư viện SFX 48kHz
    ├── typography_fonts/           # Bộ font Roboto, Inter, Be Vietnam Pro
    └── reference_portraits/        # Khuôn mặt người mẫu bản quyền
```

---

## 8. NGUYÊN TẮC CHUYỂN TIẾP & BẢO TOÀN (MIGRATION & COMPATIBILITY)

1. **Thư mục trung tâm mới:** Tạo thư mục `production_hub/channels/` tại gốc workspace làm trung tâm lưu trữ theo chuẩn mới.
2. **Bảo tồn tương thích (Symlink & Aliases):** Các pipeline cũ đang trỏ tới `assets/scripts_video/` hoặc `output/youtube_staging/` sẽ được kết nối qua symlink hoặc đường dẫn chuẩn hóa thông qua module trợ lý `canonical_path.py`.
3. **Áp dụng ngay lập tức:** Toàn bộ các tập của Series 2 Địa lý (`s02_bac_them_dia_hinh`) từ Tập 01, Tập 02, Tập 03 trở đi được quy hoạch và đóng gói 100% theo đúng quy chuẩn phân tầng này.
