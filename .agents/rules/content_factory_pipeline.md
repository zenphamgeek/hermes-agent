# Content Factory Pipeline — nguồn chuẩn

`.agents` là nguồn chuẩn duy nhất cho rule và skill của Content Factory trong
repository này. Không tạo hoặc cập nhật rule sản xuất trong `.codex` hay
`.trae`. Tài liệu cũ ở các thư mục đó chỉ là nguồn migration và không được
pipeline nạp.

## Hợp đồng bắt buộc

1. Chưa có `SERIES_CONTRACT_V1.json` được human-approve đúng SHA-256 thì không
   được bắt đầu Episode Contract, TTS, alignment, Manim, mix hoặc render của
   bất kỳ tập nào trong series. Research và audit read-only vẫn được phép.
2. Mỗi tập dùng episode contract `1.0`; mỗi beat ghép một claim, lời thoại,
   voice anchor, trạng thái visual trước/sau, operation, continuity object,
   duration range, LaTeX/spoken math và check cụ thể.
3. Final audio phải tồn tại trước khi compile timeline. Alignment chỉ chấp
   nhận word có nguồn `recognized` hoặc `manual`; cấm timestamp nội suy.
4. Voice anchor phải xuất hiện đúng một lần và đúng thứ tự. Timeline dùng frame
   nguyên ở 60 fps; không có duration fallback.
5. Evidence hash bao phủ contract, final audio, alignment, scene source,
   helper, font, model/data và các asset khai báo.
6. Automated checks chỉ trả `PASS/ERROR/UNKNOWN`; không được tạo human approval.
   Audio, visual và golden approval phải gắn artifact hash và dependency closure
   hash chính xác. Artifact hoặc dependency đổi thì approval hết hiệu lực.
7. Thiếu media, ffmpeg/ffprobe, alignment, dependency hoặc approval là
   `ERROR/UNKNOWN` và `releasable=false`, tuyệt đối không pass mềm.
8. Manim tiếng Việt dùng `assets.manim_library.typography.vi_text`; mặc định
   Roboto Regular. Bold chỉ dùng cho emphasis được khai báo trong beat.
9. Short có thời lượng 45–60 giây. Longform theo series profile của tập.
10. Mọi storyboard và scene source phải qua
    `.agents/rules/content_visual_suitability.md`: visual phải biểu diễn đúng
    thực thể, cơ chế, biến đổi và phép đo của claim. Slide-deck Manim, chuỗi
    card/bullet thay nhau và chuyển động trang trí không mang thông tin đều là
    lỗi chặn preview approval.

## Lệnh chuẩn

```bash
python3 assets/scripts_video/content_factory_pipeline.py preflight \
  --contract path/to/episode_contract.json \
  --media path/to/final.mp4 \
  --approvals-dir path/to/approvals \
  --report path/to/PREFLIGHT_REPORT.json
```

Exit `0` chỉ khi mọi gate đều `PASS`. `UNKNOWN` cũng chặn release.

Pipeline stage runner dùng manifest `pipeline_version: 1.0` với đúng thứ tự:
`research → episode_contract → voice → alignment → timeline → preview_render →
visual_review → production_render → mix → final_qc`. Mỗi stage khai báo `command`
dạng argv array, `inputs`, `outputs`. Chạy và kiểm tra bằng:

```bash
python3 assets/scripts_video/content_factory_pipeline.py status --pipeline PIPELINE.json
python3 assets/scripts_video/content_factory_pipeline.py run-stage \
  --pipeline PIPELINE.json --stage research
```

Runner từ chối chạy lệch thứ tự, hash input/output mỗi stage, ghi log, và xóa
evidence downstream khi stage upstream được chạy lại.

Sau khi người duyệt đã thực sự nghe/xem đúng artifact, ghi nhận approval bằng
`record-approval --confirmed-reviewed`. Flag này là lời xác nhận của người chạy,
không được agent tự thêm để giả lập việc duyệt.
