# 🎬 Hermes Footage Vault — API & MCP Integration Developer Guide

Tài liệu hướng dẫn tích hợp toàn diện dành cho các Agent độc lập (Hermes, Trae, Antigravity IDE, Claude Desktop, Cursor), hệ thống tự động hóa (n8n, Webhooks), và các dịch vụ microservice để truy vấn, tìm kiếm ngữ nghĩa và nạp video B-Roll chất lượng cao từ kho lưu trữ **500GB MinIO S3 Vault**.

---

## 📑 Mục Lục
1. [Tổng Quan Kiến Trúc](#1-tổng-quan-kiến-trúc)
2. [Danh Mục Chuyên Ngành (Categories)](#2-danh-mục-chuyên-ngành-categories)
3. [HTTP REST API Reference](#3-http-rest-api-reference)
4. [Model Context Protocol (MCP) Integration](#4-model-context-protocol-mcp-integration)
5. [Code Mẫu Tích Hợp (Code Examples)](#5-code-mẫu-tích-hợp-code-examples)
   - [Python](#python-client)
   - [TypeScript / JavaScript](#typescript--javascript-client)
   - [cURL Shell](#curl-shell)
   - [Hermes Agent Native Tool](#hermes-agent-native-tool)
6. [Cấu Trúc Dữ Liệu & S3 Presigned Streaming](#6-cấu-trúc-dữ-liệu--s3-presigned-streaming)

---

## 1. Tổng Quan Kiến Trúc

Footage Vault cung cấp kho tài nguyên video B-Roll 1080p/4K được phân đoạn tự động và đánh chỉ mục ngữ nghĩa bằng **Dense Vector Embeddings (128 chiều)**.

- **Storage Backend**: MinIO S3 Cluster tại `http://10.123.214.249:9000` (Bucket: `omnivoice-audio/footage/`).
- **Tìm Kiếm Ngữ Nghĩa**: Cosine Similarity Vector Search kết hợp bộ lọc Metadata đa chiều.
- **Tốc Độ Phản Hồi**: < 15ms cho mỗi truy vấn tìm kiếm.

---

## 2. Danh Mục Chuyên Ngành (Categories)

Hệ thống hỗ trợ 10 danh mục chuyên biệt:

| Category Slug | Tên Chuyên Ngành | Mô Tả & Nội Dung Minh Họa |
|---|---|---|
| `mathematics` | 📐 **Toán học** | Giải tích, Fractal Mandelbrot, 3D Torus Knot, Ma trận topo, Lissajous Curves. |
| `technology` | 💻 **Công nghệ & AI** | Server Rack Telemetry, Điện toán đám mây, AI Neural Synapses, Coding Terminal. |
| `chemistry` | 🧪 **Hóa học** | Cấu trúc phân tử 3D (Benzene C6H6), Lai hóa obitan sp2, Tinh thể hóa. |
| `biology` | 🧬 **Sinh học & Di truyền** | Chuỗi xoắn kép DNA (A-T/G-C), Trình tự gen CRISPR-Cas9, Nơ-ron thần kinh. |
| `occupational-safety` | 🦺 **An toàn lao động (HSE)** | Trang bị bảo hộ PPE Compliance, Biểu tượng hóa chất GHS, Phòng cháy PCCC. |
| `cafe` | ☕ **Cà phê & Pha chế** | Barista pha chế Espresso, Nghệ thuật Latte Art, Rang xay hạt Robusta/Arabica. |
| `food` | 🍳 **Ẩm thực & Nhà hàng** | Nghệ thuật Gourmet Plating, Chảo lửa Wok Sizzle, Nguyên liệu tươi sạch. |
| `logistics` | 📦 **Chuỗi cung ứng & Kho vận** | Robot AGV trong kho thông minh, Băng chuyền tự động, Container cảng biển. |
| `cyber-security` | 🛡️ **An ninh mạng** | Zero-Trust Shield, Tường lửa Firewall, Mã hóa Secret Vault, Laser Scan. |
| `hologram-hud` | 📊 **Giao diện Holographic HUD** | Biểu đồ sóng âm Audio Spectrum, Hologram Telemetry Dials, Cyber HUD. |

---

## 3. HTTP REST API Reference

- **Base URL**: `http://localhost:8420` (hoặc IP Workstation P15: `http://10.123.214.1:8420`)
- **Khởi chạy Server**:
  ```bash
  python3 optional-skills/creative/content-factory/footage_mcp_server.py --http --port 8420
  ```

### 3.1. Kiểm Tra Sức Khỏe Máy Chủ (`GET /health`)
```http
GET /health HTTP/1.1
Host: localhost:8420
```
**Response (200 OK):**
```json
{
  "status": "ok",
  "service": "footage-vault-api"
}
```

### 3.2. Thống Kê Kho Dữ Liệu (`GET /api/footage/stats`)
```http
GET /api/footage/stats HTTP/1.1
Host: localhost:8420
```
**Response (200 OK):**
```json
{
  "total_clips": 27,
  "s3_endpoint": "http://10.123.214.249:9000",
  "s3_bucket": "omnivoice-audio",
  "categories": {
    "mathematics": 3,
    "technology": 4,
    "chemistry": 2,
    "biology": 2,
    "occupational-safety": 2,
    "cafe": 2,
    "food": 2,
    "logistics": 2,
    "cyber-security": 8
  }
}
```

### 3.3. Tìm Kiếm Ngữ Nghĩa & Lọc Video (`GET /api/footage/search`)
**Query Parameters:**
- `query` (*string, bắt buộc*): Từ khóa hoặc ngữ cảnh cần minh họa.
- `category` (*string, tùy chọn*): Slug danh mục (VD: `cafe`, `logistics`, `biology`).
- `aspect_ratio` (*string, tùy chọn*): `16:9` (ngang), `9:16` (dọc Shorts), `1:1` (vuông).
- `min_quality` (*string, tùy chọn*): `1080p`, `4k`, `720p`.
- `top_k` (*integer, mặc định: 3*): Số lượng clip trả về.

```http
GET /api/footage/search?query=espresso+latte+art&category=cafe&aspect_ratio=16:9&min_quality=1080p&top_k=2 HTTP/1.1
Host: localhost:8420
```

**Response (200 OK):**
```json
{
  "query": "espresso latte art",
  "total_matches": 2,
  "clips": [
    {
      "id": "clip_3f8a19bc04",
      "title": "Specialty Coffee Brewing & Espresso Latte Art (Phân đoạn 1)",
      "category": "cafe",
      "tags": ["cafe", "coffee", "espresso", "latte-art", "barista"],
      "duration_sec": 6,
      "resolution": "1920x1080",
      "aspect_ratio": "16:9",
      "similarity_score": 0.8421,
      "s3_clip_key": "footage/clips/master_cafe_clip_01.mp4",
      "s3_thumb_key": "footage/thumbnails/master_cafe_thumb_01.jpg",
      "clip_stream_url": "http://10.123.214.249:9000/omnivoice-audio/footage/clips/master_cafe_clip_01.mp4?AWSAccessKeyId=...",
      "thumb_stream_url": "http://10.123.214.249:9000/omnivoice-audio/footage/thumbnails/master_cafe_thumb_01.jpg?AWSAccessKeyId=..."
    }
  ]
}
```

---

## 4. Model Context Protocol (MCP) Integration

MCP cho phép các mô hình LLM và Agent gọi trực tiếp công cụ `search_footage_vault` qua giao thức chuẩn JSON-RPC 2.0.

### Cấu hình `mcp_config.json`:
```json
{
  "mcpServers": {
    "footage-vault": {
      "command": "python3",
      "args": [
        "/home/zen/hermes-agent/optional-skills/creative/content-factory/footage_mcp_server.py",
        "--mcp"
      ]
    }
  }
}
```

### Danh sách Tool Schemas được cung cấp:
1. `search_footage_vault`: Tìm kiếm video footage theo ngữ nghĩa và ràng buộc chất lượng.
2. `get_footage_catalog_stats`: Lấy thống kê tổng quan và phân bổ chuyên ngành.
3. `ingest_footage_asset`: Nạp và phân đoạn video mới vào S3 Vault.

---

## 5. Code Mẫu Tích Hợp (Code Examples)

### Python Client
```python
import urllib.request
import urllib.parse
import json

def query_footage(query: str, category: str = None, aspect_ratio: str = "16:9", top_k: int = 3):
    params = {"query": query, "aspect_ratio": aspect_ratio, "top_k": top_k}
    if category:
        params["category"] = category
    
    url = f"http://localhost:8420/api/footage/search?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "AgentClient/2026"})
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("clips", [])

# Example usage:
clips = query_footage("Barista brewing espresso coffee", category="cafe", aspect_ratio="16:9")
for clip in clips:
    print(f"🎬 {clip['title']} (Score: {clip['similarity_score']})")
    print(f"🔗 Stream URL: {clip['clip_stream_url']}")
```

### TypeScript / JavaScript Client
```typescript
interface FootageClip {
  id: string;
  title: string;
  category: string;
  resolution: string;
  aspect_ratio: string;
  similarity_score: number;
  clip_stream_url: string;
  thumb_stream_url: string;
}

async function searchFootageVault(query: string, category?: string, aspectRatio: string = "16:9"): Promise<FootageClip[]> {
  const params = new URLSearchParams({
    query,
    aspect_ratio: aspectRatio,
    top_k: "3",
    ...(category ? { category } : {})
  });

  const response = await fetch(`http://localhost:8420/api/footage/search?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Footage API error: ${response.statusText}`);
  }
  const data = await response.json();
  return data.clips || [];
}

// Example usage:
searchFootageVault("Smart automated warehouse AGV logistics", "logistics")
  .then(clips => console.log("Found clips:", clips));
```

### cURL Shell
```bash
# 1. Tìm footage Cà phê (Cafe)
curl -s "http://localhost:8420/api/footage/search?query=espresso+latte+art&category=cafe&aspect_ratio=16:9&top_k=2" | jq .

# 2. Tìm footage Ẩm thực (Food)
curl -s "http://localhost:8420/api/footage/search?query=gourmet+culinary+wok+cooking&category=food&aspect_ratio=16:9&top_k=2" | jq .

# 3. Tìm footage Kho vận (Logistics)
curl -s "http://localhost:8420/api/footage/search?query=automated+agv+warehouse+supply+chain&category=logistics&aspect_ratio=16:9&top_k=2" | jq .
```

### Hermes Agent Native Tool
Trong mọi phiên hội thoại của Hermes Agent, bạn có thể gọi trực tiếp công cụ `search_footage_vault`:
```json
{
  "name": "search_footage_vault",
  "arguments": {
    "query": "Gourmet culinary cooking fresh ingredients",
    "category": "food",
    "aspect_ratio": "16:9",
    "min_quality": "1080p",
    "top_k": 2
  }
}
```

---

## 6. Cấu Trúc Dữ Liệu & S3 Presigned Streaming

Mỗi kết quả trả về luôn bao gồm trường **`clip_stream_url`** và **`thumb_stream_url`**. Đây là các đường dẫn **MinIO S3 Presigned URLs** có hiệu lực truy cập trong 1 giờ.

Các engine render video (như `ffmpeg` hoặc `moviepy`) có thể truyền trực tiếp URL này làm đầu vào video stream mà không cần tải thủ công về đĩa:
```bash
ffmpeg -i "<clip_stream_url>" -vf "scale=1920:1080" -c:v libx264 output_scene.mp4
```
