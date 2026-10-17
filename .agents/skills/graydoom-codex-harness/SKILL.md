---
name: graydoom-codex-harness
description: >-
  Codex-grade Reference-Driven Development Harness, TravianZ 3dbe9c71 Gameplay
  Parity Engine, 40-Slot 2.5D/WebGL Settlement Lot & Corridor Mapper, and
  Disposable PostgreSQL 390px Browser QA Gate for Gray Doom. Enforces
  gd-<slug>.json change packets, 7-lane diff coverage, SHA-256 reference rule
  pinning, 4-authority-doc synchronization, and 4-level Gemini 4 Argon Pro
  Swarm task planning.
---

# Gray Doom Codex Development Harness & Gameplay Parity Skill (`graydoom-codex-harness`)

Quy chuẩn vận hành kỹ thuật được chắt lọc trực tiếp từ cách **Codex** quản lý kiến trúc, lập kế hoạch (`config/development-harness/changes/gd-<slug>.json`), kiểm soát logic Gameplay (`TravianZ 3dbe9c71`), ánh xạ công trình lên 40 lô đất định cư 2.5D/WebGL (`f1`–`f18` & `19`–`40`), và nghiệm thu trình duyệt thực tế (`390×844` mobile & `1280px` desktop) trên nhánh `main`, `codex/gameplay-resume-20261013` và `codex/settlement-art-mapping-20261015`.

---

## 1. Năm Nguyên Tắc Điều Phối Cốt Lõi Của Codex (Why Codex Succeeds Without Drift)

1. **One Change Packet Per Coherent Decision (`config/development-harness/changes/gd-<slug>.json`)**:
   - Không bao giờ sửa code, migration SQL hay Art một cách tự phát. Trước khi viết bất kỳ dòng code nào, bắt buộc tạo gói thay đổi `gd-<slug>.json` khai báo rõ:
     - `lanes`: Một hoặc nhiều làn trong 7 làn chuẩn (`backbone`, `gameplay`, `code`, `story`, `campaign`, `dossier`, `art`).
     - `files`: Danh sách đường dẫn file chính xác tuyệt đối (không dùng thư mục chung chung để giấu thay đổi).
     - `canon`: Các tài liệu quy chuẩn bị ảnh hưởng (`docs/product-spec.md`, `docs/technical-spec.md`, `docs/implementation-tracker.md`, `docs/travianz-parity-register.md`).
     - `parityArea` & `parityEffect`: Khớp với một dòng trong bảng `docs/travianz-parity-register.md` (`none`, `preserved`, `proposed-deviation`, `approved-deviation`).
     - `factions`: Chỉ chấp nhận 3 phe người chơi (`atlantic-coalition` [1], `northern-federation` [2], `eastern-directorate` [3]) và 1 phe trung lập (`gray-zone` [5], `neutralSelectable: false`).
2. **Diff-Bound Packet Coverage (`npm run verify:harness -- --changed <base-ref>`)**:
   - Mọi file thay đổi từ `<base-ref>...HEAD` trong `migrations/`, `src/`, `content/`, `art/`, `public/`, `docs/`, `data/`, `config/`, `scripts/`, `tests/` bắt buộc phải nằm trong ít nhất một packet `gd-<slug>.json`. Nếu thiếu dù chỉ 1 file, `verify-development-harness.js` lập tức chặn (fail-closed).
3. **Cryptographic Reference Rule & Balance Table Pinning (`3dbe9c71ecf345e533dfc6381d67760d8de8d415`)**:
   - Mọi thay đổi thuộc làn `gameplay` hoặc `campaign` bắt buộc ghim:
     - `reference.rules[]`: `id`, `revision: "3dbe9c71ecf345e533dfc6381d67760d8de8d415"`, `sourcePath` (trỏ vào file PHP gốc trong `../work/travianz-reference`), `sha256` của file nguồn tham chiếu, và danh sách `cases` (các file test thực thi chứng minh công thức ở biên thấp, giữa, cao và cực hạn).
     - `balance.tables[]`: Đường dẫn và `sha256` của bảng dữ liệu cân bằng JSON (`data/travianz-*.json`).
4. **4-Doc Lockstep Synchronization**:
   - Mọi tính năng gameplay sau khi triển khai phải cập nhật đồng bộ cả 4 tài liệu:
     1. `docs/product-spec.md` (phạm vi sản phẩm & hành vi người dùng)
     2. `docs/technical-spec.md` (schema DB, API endpoints, state machine)
     3. `docs/implementation-tracker.md` (tiến độ bàn giao & bằng chứng test)
     4. `docs/travianz-parity-register.md` (trạng thái `MISSING` $\to$ `PARTIAL` $\to$ `IMPLEMENTED` $\to$ `VERIFIED`)
   - Đồng thời chạy `python3 scripts/build-content-source-index.py --write` để đồng bộ chỉ mục SHA-256 tại `content/production-source-index-v1.json`.
5. **Strict Authority Separation (UI Preview $\ne$ Server Command, Schematic Geometry $\ne$ Approved Art)**:
   - Giao diện mẫu hoặc bản vẽ 2.5D/WebGL chỉ gửi `slotId` về server; tuyệt đối không tính toán chi phí, thời gian xây dựng, sản lượng hay quyền sở hữu ở client.
   - Các nút chức năng chưa có backend xác thực bắt buộc để trạng thái `disabled` hoặc gắn nhãn `preview` rõ ràng.

---

## 2. Cấu Trúc Chuẩn Của Một Change Packet (`gd-<slug>.json`)

```json
{
  "id": "gd-registered-gm-gold-adjustment-v1",
  "state": "review",
  "intent": "Persist audited Game Master Gold adjustments with CSRF verification, immutable reason ledger, and 390px mobile browser verification.",
  "lanes": ["gameplay", "code", "backbone"],
  "files": [
    "content/production-source-index-v1.json",
    "content/release-readiness-v1.json",
    "docs/implementation-tracker.md",
    "docs/product-spec.md",
    "docs/registered-gm-gold-adjustment-parity-spec.md",
    "docs/technical-spec.md",
    "docs/travianz-parity-register.md",
    "migrations/078_world_gm_gold_adjustments.sql",
    "public/gm.css",
    "public/gm.html",
    "public/gm.js",
    "src/server.js",
    "src/world-account-store.js",
    "tests/world-gm-search.test.js"
  ],
  "canon": [
    "docs/product-spec.md",
    "docs/technical-spec.md",
    "docs/implementation-tracker.md",
    "docs/travianz-parity-register.md",
    "config/faction-scope-v1.json"
  ],
  "parityArea": "Game Master controls",
  "parityEffect": "preserved",
  "gameplayEffect": "Admin-authenticated Gold balance adjustment with non-negative floor and immutable audit history.",
  "storyEffect": "No narrative change.",
  "artEffect": "No image generation or visual authority change.",
  "factions": [],
  "neutralSelectable": false,
  "reference": {
    "rules": [
      {
        "id": "admin-gold-adjustment",
        "revision": "3dbe9c71ecf345e533dfc6381d67760d8de8d415",
        "sourcePath": "Admin/Templates/gold.tpl",
        "sha256": "<sha256-of-reference-file>",
        "cases": ["tests/world-gm-search.test.js"]
      }
    ]
  },
  "balance": {
    "status": "not-applicable",
    "tables": []
  },
  "conflictStatus": "none",
  "conflictDecision": "Game Master controls remain PARTIAL until full admin toolset is completed.",
  "tests": ["tests/world-gm-search.test.js"],
  "review": {
    "story": "passed",
    "gameplay": "passed",
    "art": "passed",
    "code": "passed"
  }
}
```

---

## 3. Kiểm Soát Logic Gameplay & 2.5D/WebGL Settlement Lot Mapping (40 Slots)

Codex thiết lập kiến trúc kết nối giữa **Server State**, **DOM/SVG Controls**, và **WebGL 2.5D Settlement View** (`public/settlement-webgl-review.js`, `public/world.js`) theo các quy tắc bất biến:

1. **Bản Đồ 40 Lô Định Cư (`f1`–`f18` & `19`–`40`)**:
   - **Resource Perimeter (`f1`–`f18`)**: 18 mỏ tài nguyên ngoại vi + 1 liên kết trung tâm vào City.
   - **City Plots (`19`–`40`)**: 22 lô nội đô và tường thành, trong đó:
     - Lô `26`: **Main Building** (Sở Chỉ Huy trung tâm).
     - Lô `39`: **Deployment Yard** (Bãi Tập Kết / Rally Point).
     - Lô `40`: **Perimeter Wall / Barrier** (Tường Thành / Chiến Lũy).
2. **Quy Tắc Hình Học & Giao Thông Nội Khu (Spatial Lot & Corridor Rules)**:
   - Mỗi lô xây dựng (`lot`) có một **Reserved Building Base** (đế đặt công trình) và một **Service Access Link** nối từ mặt tiền công trình ra trục đường chính.
   - **Hành lang an toàn 31 px (`31 px Road & Water Corridor`)**: Trục đường chính đi qua cổng thành và kênh nước bắt buộc không được cắt ngang bất kỳ mặt đế xây dựng nào trong 40 lô (`18` Resource + `22` City).
   - Khi người chơi chọn một lô (bằng chuột hoặc phím mũi tên / `Tab`), chỉ hiển thị đường tiếp cận (`access path`) của riêng lô đó, không đè lên footprint của lô khác.
3. **Ánh Xạ Cutout Art Theo Phe Phái (`Place faction building art on planned settlement lots`)**:
   - Chỉ gắn ảnh cutout runtime đã được duyệt (`public/assets/runtime/building-*/<faction>-<role>.png`) lên đế của lô khi loại công trình đó đã có trong catalog hoàn chỉnh của cả 3 phe (`Atlantic`, `Northern`, `Eastern`).
   - Các công trình chưa có cutout được duyệt hoặc đang xây dở phải hiển thị khối **Schematic Mass** (khối hình học kỹ thuật) rõ ràng, tuyệt đối không dùng nhầm ảnh của công trình khác hoặc phe khác.

---

## 4. Quy Trình Kiểm Thử Disposable PostgreSQL World & 390px Browser QA (`docs/qa/*.md`)

Mỗi khi hoàn thành một tính năng Gameplay hoặc UI, Codex thực hiện quy trình 5 bước để ghi biên bản `docs/qa/<feature>-browser-YYYY-MM-DD.md`:

1. **Khởi tạo Thế Giới PostgreSQL Tạm Thời (Disposable World)**:
   - Tạo một thế giới riêng biệt (ví dụ `gm-gold-visual-qa` hoặc bán kính `radius=3`) với tài khoản test, không chạm vào dữ liệu người chơi thật.
2. **Kiểm tra Desktop (`1280 × 800`) & Điều hướng Bàn phím**:
   - Mở trang qua headless/in-app browser (`/world.html`, `/gm.html`, `/settlement-webgl-review.html`).
   - Kiểm tra phím `Tab` (theo thứ tự số lô tài liệu) và phím mũi tên (theo hướng lưới không gian 7 cột trên desktop).
3. **Kiểm tra Mobile (`390 × 844` và `430 × 850`) — Zero Horizontal Overflow**:
   - Đo kích thước thực tế của DOM: `document.documentElement.scrollWidth <= viewportWidth` (ví dụ `375 px <= 390 px`).
   - Đảm bảo lưới Resource chuyển về 3 cột, lưới City chuyển về 4 cột, ảnh công trình và nút bấm nằm gọn trong khung `x=16..359` mà không bị tràn ngang hay bị thanh điều hướng sticky che khuất.
4. **Dọn dẹp (Teardown)**:
   - Xóa tài khoản/database tạm thời sau khi ghi nhận thông số đo đạc và SHA-256 của các ảnh runtime đã hiển thị.
5. **Chạy Chuỗi Lệnh Xác Thực Bắt Buộc**:
   ```bash
   npm test
   npm run verify:harness
   npm run verify:content-sources
   npm run verify:release-audit
   ```

---

## 5. Điều Phối Tác Vụ Qua AGY-Fleet Với Gemini 4 Argon (`tier="pro"`)

Khi sử dụng skill này trên AGY hoặc AGY-Fleet, luôn lập kế hoạch và thực thi trên cụm **17 Standard Pro Nodes (`tier="pro"`)** với **4-Level Gemini 4 Argon**:
- **Lập kế hoạch (`fleet_plan`)**:
  ```python
  call_mcp_tool(
      ServerName="agy-fleet",
      ToolName="fleet_plan",
      Arguments={
          "prompt": "Plan gd-<slug>.json packet and TravianZ 3dbe9c71 test cases for <feature>",
          "model": "gemini-4-argon-high",
          "tier": "pro"
      }
  )
  ```
- **Thực thi (`fleet_run`)**:
  - `L1_TRIVIAL` ($C < 1.2$, cập nhật manifest/doc): `model="gemini-4-argon-low"`, `tier="pro"`
  - `L2_STANDARD` ($1.2 \le C < 2.2$, viết unit test / capture script): `model="gemini-4-argon-medium"`, `tier="pro"`
  - `L3_COMPLEX` ($2.2 \le C < 3.0$, triển khai gameplay store + SQL migration + WebGL lot mapping): `model="gemini-4-argon-high"`, `tier="pro"`
  - `L4_SOVEREIGN` ($C \ge 3.0$, kiểm toán bảo mật đa vòng / đối chiếu kiến trúc liên nhánh): `model="gemini-4-argon-high"`, `tier="pro"`
