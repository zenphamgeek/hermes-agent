# Drift audit: `.codex`, `.trae` → `.agents`

Ngày kiểm tra: 2026-09-16.

## Kết quả

- `.codex`: không có file rule, skill hoặc spec trong repository.
- `.trae/skills/median-animation-director/SKILL.md`: nội dung riêng, SHA-256
  `4ae42bd2487ac3447a455ba0e0d488be3cbc0b318774ae704fdfbab70f338d5b`.
  Các invariant production đã được đưa vào skill canonical
  `.agents/skills/median-animation-director/SKILL.md`; chi tiết trùng lặp được
  dùng qua `manim-director` và `manim-production` để tránh ba bản lệch nhau.
- `.trae/specs/build-vietnamese-live-avatar/checklist.md`:
  `29af571dd93628a61ce71849b78d44df6887903b9989e33cbf93699e9eb54a8d`;
  `spec.md`: `16069e8dcbaf547bd819f5d0f60bdae0ed56f7ff2c428646f70091f4b58e49e4`;
  `tasks.md`: `bee7c271b729d47baa85e2f8c4480adc315a5583fb93e8e087585322cb672b6c`.
  Đây là tài liệu công việc cũ, không phải rule/skill Content Factory.
- `.trae/specs/centralize-modal-gpu-apis/checklist.md`:
  `712c0a854c716b6079c36825acbef0226e2b8817d33fac06679906a3a3e089b6`;
  `spec.md`: `5fe34ec56439c445e65c7a10d77c0a2a0a7b123f53177c1494a4ee91ee433586`;
  `tasks.md`: `b444a80344fd8648cf1787fd23f6026b29d79aceb0291d54cf97f16f0168455e`.
  Đây là tài liệu công việc cũ, không phải rule/skill Content Factory.

## Quyết định

Không xóa `.trae` trong migration này để bảo toàn lịch sử và tránh phá công
việc đang dở. Mọi thay đổi mới chỉ ghi vào `.agents`; pipeline không đọc
`.trae` hoặc `.codex`.
