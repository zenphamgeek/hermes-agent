#!/usr/bin/env python3
"""
YouTube SEO Metadata Engine & Multi-Channel Token Resolver
==========================================================
Generates high-ranking YouTube SEO metadata for 'TÔI ĐỌC SÁCH' & 'ZENPHAM':
1. Mobile-First Title: [Hook / Câu hỏi cảm xúc] - [Tác giả/Chủ đề] | [Tên Kênh] (< 70 chars)
2. 3-Tier Keyword Taxonomy: Brand + Niche/Entity + Long-Tail Intent (~450 chars)
3. Rich 4-Part Description with auto-calculated Timestamps / Video Chapters
4. Multi-Channel OAuth Token Resolution
"""

import os
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))


def detect_channel(md_path: Path, content: str = "") -> str:
    """Detect channel: 'TOI_DOC_SACH', 'PHAMTRAI_DIALY', 'REALITY_DECODE', or 'ZENPHAM'."""
    stem = md_path.stem.lower()
    c_lower = content.lower()
    if (
        "reality_decode" in stem
        or "realitydecode" in stem
        or "reality decode" in c_lower
        or "giải mã thực tại" in c_lower
    ):
        return "REALITY_DECODE"
    if (
        "vietnam_nhung_mien_song" in stem
        or "phamtrai" in stem
        or "biết địa lý" in c_lower
        or "những miền sống" in c_lower
        or "phạm trãi" in c_lower
    ):
        return "PHAMTRAI_DIALY"
    if "toi_doc_sach" in stem or "tôi đọc sách" in c_lower:
        return "TOI_DOC_SACH"
    return "ZENPHAM"


def resolve_channel_token(channel: str, override_path: Optional[str] = None) -> Tuple[Path, bool]:
    """
    Resolve OAuth2 token path for the target channel.
    Returns (token_path, is_channel_specific).
    """
    if override_path:
        p = Path(override_path)
        if p.exists():
            return p, True

    ch_clean = channel.lower().replace("-", "_").strip()

    # Check channel-specific token first
    specific_name = f"google_token_{ch_clean}.json"
    specific_path = HERMES_HOME / specific_name
    if specific_path.exists():
        return specific_path, True

    # Check known aliases for PHAMTRAI_DIALY
    if channel.upper() in ("PHAMTRAI_DIALY", "BIET_DIA_LY_TU_BA_TOI", "VIETNAM_MIEN_SONG"):
        for alias in [
            "google_token_phamtrai_dialy.json",
            "google_token_vietnam_mien_song.json",
            "google_token_biet_dia_ly_tu_ba_toi.json",
        ]:
            if (HERMES_HOME / alias).exists():
                return HERMES_HOME / alias, True

    # Check known aliases for REALITY_DECODE
    if channel.upper() in ("REALITY_DECODE", "REALITYDECODE", "REALITY"):
        for alias in [
            "google_token_reality_decode.json",
            "google_token_realitydecode.json",
        ]:
            if (HERMES_HOME / alias).exists():
                return HERMES_HOME / alias, True

    # Fallbacks
    for fallback in ["google_token.json", "youtube_token.json"]:
        fb_path = HERMES_HOME / fallback
        if fb_path.exists():
            return fb_path, False

    return HERMES_HOME / f"google_token_{ch_clean}.json", False


def extract_script_info(content: str) -> Dict:
    """Extract raw title, author, main concept, scenes, quotes, tags, and frontmatter links from script markdown."""
    frontmatter = {}
    fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.S)
    if fm_match:
        fm_text = fm_match.group(1)
        for line in fm_text.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                frontmatter[k.strip().lower()] = v.strip().strip('"“”\'')

    # Find raw title skipping frontmatter
    # Check canonical # Heading first (to avoid thumbnail Cover_Title overrides with linebreaks/slashes)
    raw_title = ""
    m_head = re.search(r'^#\s+(?:TẬP\s*\d+:\s*)?(.+)$', content, re.M)
    if m_head:
        raw_title = m_head.group(1).strip()
    if not raw_title:
        raw_title = frontmatter.get("title", "")
    if not raw_title:
        m_theme = re.search(r'^(?:Chủ đề|Title):\s*(.+)$', content, re.M | re.I)
        if m_theme:
            raw_title = m_theme.group(1).strip()
    if not raw_title:
        raw_title = frontmatter.get("cover_title", "").replace("/", " - ")
    if not raw_title:
        for line in content.splitlines():
            line_s = line.strip("# \t\n-")
            if line_s and not line.strip().startswith("---") and not line.strip().startswith("SERIES:") and not line.strip().startswith("Tập:"):
                raw_title = line_s
                break

    # Clean raw title from script artifact prefixes
    raw_title = re.sub(r"^(?:KỊCH BẢN\s+(?:SHORT(?:S)?(?:\s*\d+S)?|VIDEO|CHI TIẾT)\s*[:—–\-]\s*)", "", raw_title, flags=re.I).strip()
    raw_title = raw_title.replace("/", " — ")
    m_title = re.search(
        r"^(?:(?:Kịch bản video\s+)?(?:ZENPHAM|TÔI ĐỌC SÁCH|BIẾT ĐỊA LÝ TỪ BA TÔI)\s*[—–\-:]\s*)?[\"“”]?(.+?)[\"”]?$",
        raw_title,
        re.I,
    )
    raw_title = m_title.group(1).strip().strip('"“”') if m_title else raw_title.strip('"“”')

    # Extract author / source
    m_source = re.search(r"Nguồn chính:\s*(.+)", content, re.I)
    source = frontmatter.get("source", "") or (m_source.group(1).strip() if m_source else "")

    # Extract central question
    m_q = re.search(r"Câu hỏi trung tâm:\s*(.+)", content, re.I)
    central_question = frontmatter.get("central_question", "") or (m_q.group(1).strip() if m_q else "")

    # Extract Series (e.g. SERIES: TÔI LÀM VIỆC)
    m_series = re.search(r'SERIES:\s*["“”]?(.+?)["”]?$', content, re.M | re.I)
    series = frontmatter.get("series", "") or (m_series.group(1).strip() if m_series else "")

    # Extract Episode
    episode = frontmatter.get("episode", "") or frontmatter.get("tập", "")

    # Extract Format & Duration
    format_val = frontmatter.get("format", "") or frontmatter.get("định dạng", "")
    duration_val = frontmatter.get("duration", "") or frontmatter.get("thời lượng", "")

    # Extract Bidirectional Links
    related_longform_script = frontmatter.get("related_longform_script", "")
    related_longform_id = frontmatter.get("related_longform_id", "")
    related_short_script = frontmatter.get("related_short_script", "")
    related_short_id = frontmatter.get("related_short_id", "")

    # Extract Frontmatter Tags
    fm_tags_raw = frontmatter.get("tags", "")
    fm_tags = [t.strip() for t in fm_tags_raw.split(",") if t.strip()] if fm_tags_raw else []

    # Detect if short
    is_short = (
        "short" in format_val.lower()
        or "9:16" in format_val.lower()
        or "portrait" in format_val.lower()
        or (duration_val.endswith("s") and duration_val[:-1].isdigit() and int(duration_val[:-1]) <= 60)
        or "short" in raw_title.lower()
    )

    # Extract scenes
    scene_blocks = re.split(r"\n(?:\*\*)?(?:Đoạn|Scene|Phần|Chapter)\s+\d+[^:\n]*:", content, flags=re.I)[1:]
    scenes = []
    for i, block in enumerate(scene_blocks, 1):
        m_dialogue = re.search(r'(?:\*\*)?Lời thoại:(?:\*\*)?[^"“”\n]*["“”](.+?)["”]', block, re.S)
        dialogue = re.sub(r"\s+", " ", re.sub(r"\([^)]*\)", "", m_dialogue.group(1))).strip() if m_dialogue else ""
        
        m_scene_title = re.search(r"^\s*([^\n•\(\)]+)", block)
        scene_heading = m_scene_title.group(1).strip() if m_scene_title else f"Phần {i}"
        # Clean timestamps from heading
        scene_heading = re.sub(r"\b\d+s[–\-]\d+s\b", "", scene_heading).strip()
        scene_heading = re.sub(r"\b\d{2}:\d{2}[–\-]\d{2}:\d{2}\b", "", scene_heading).strip()

        # If heading matched metadata keys (e.g. Cảm xúc:, Hình ảnh:), search for explicit Topic or default to Phần i
        if any(scene_heading.lower().startswith(k) for k in ["cảm xúc", "hình ảnh", "từ khóa", "footage", "lời thoại", "emotion", "visual", "keywords"]):
            m_topic = re.search(r"(?:Chủ đề|Tiêu đề|Topic|Title):\s*([^\n]+)", block, re.I)
            if m_topic:
                scene_heading = m_topic.group(1).strip()
            else:
                scene_heading = f"Phần {i}"

        scenes.append({"index": i, "heading": scene_heading or f"Cảnh {i}", "dialogue": dialogue})

    if not central_question and scenes:
        first_d = scenes[0].get("dialogue", "")
        qm = re.search(r"([^.!?\n]+[\?])", first_d)
        if qm:
            central_question = qm.group(1).strip()

    return {
        "raw_title": raw_title,
        "source": source,
        "series": series,
        "episode": episode,
        "format": format_val,
        "duration": duration_val,
        "is_short": is_short,
        "related_longform_script": related_longform_script,
        "related_longform_id": related_longform_id,
        "related_short_script": related_short_script,
        "related_short_id": related_short_id,
        "frontmatter_tags": fm_tags,
        "central_question": central_question,
        "scenes": scenes,
    }


def build_seo_title(raw_title: str, channel: str, source: str = "", series: str = "", is_short: bool = False, episode: str = "") -> str:
    """
    Mobile-First SEO Title Formula:
    - Longform: [Câu hỏi / Hook cảm xúc] - [Tác giả/Chủ đề] | [Tên Kênh] (< 70 chars)
    - Shorts: [Hook cảm xúc ngắn] #Shorts (hoặc [Hook] #Shorts | ZenPham) (< 60 chars)
    """
    if channel == "PHAMTRAI_DIALY":
        channel_brand = "Biết Địa lý từ Ba tôi"
    elif channel == "TOI_DOC_SACH":
        channel_brand = "Tôi Đọc Sách"
    elif channel == "REALITY_DECODE":
        channel_brand = "REALITY DECODE"
    else:
        channel_brand = "ZenPham"

    # Clean hook
    hook = raw_title.strip('"“”\'')
    hook = re.sub(r"^(?:KỊCH BẢN\s+(?:SHORT(?:S)?(?:\s*\d+S)?|VIDEO|CHI TIẾT)\s*[:—–\-]\s*)", "", hook, flags=re.I).strip()
    hook = re.sub(rf"^(?:TÔI ĐỌC SÁCH|ZENPHAM|BIẾT ĐỊA LÝ TỪ BA TÔI|VIỆT NAM\s*[-–—]\s*NHỮNG MIỀN SỐNG(?:\s*NƯỚC)?)\s*[—–\-:]\s*", "", hook, flags=re.I).strip().strip('"“”\'')
    hook = re.sub(r"\s*\|\s*.*$", "", hook).strip()

    if is_short:
        # Shorts title formula: punchy hook + #Shorts
        # Strip #Shorts if already present to avoid duplication
        hook_clean = re.sub(r"#shorts\b", "", hook, flags=re.I).strip()
        if len(hook_clean) <= 55:
            candidate = f"{hook_clean} #Shorts"
        else:
            # If removing parenthetical note fits nicely, do that
            hook_no_paren = re.sub(r"\s*\([^)]*\)", "", hook_clean).strip()
            if len(hook_no_paren) <= 50:
                candidate = f"{hook_no_paren} #Shorts"
            else:
                candidate = f"{hook_clean[:52].rsplit(' ', 1)[0]} #Shorts"
        return unicodedata.normalize("NFC", candidate)
    
    # Identify subject / author for longform
    subject = ""
    if channel == "PHAMTRAI_DIALY":
        if "sông nước" in raw_title.lower() or "mê kông" in raw_title.lower():
            subject = "Miền Tây Sông Nước"
        elif "chợ nổi" in raw_title.lower():
            subject = "Chợ Nổi Miền Tây"
        elif "đất" in raw_title.lower() or "phù sa" in raw_title.lower():
            subject = "Địa Lý Đất Đai"
        else:
            subject = "Những Miền Sống"
    elif "nam hoa kinh" in raw_title.lower() or "nam hoa kinh" in source.lower():
        subject = "Trang Tử"
    elif "người xa lạ" in raw_title.lower() or "camus" in source.lower():
        subject = "Albert Camus"
    elif "bình thường" in raw_title.lower():
        subject = "Triết Học Sống"
    elif "thấu hiểu" in raw_title.lower():
        subject = "Tâm Lý Học"
    elif "biết" in raw_title.lower():
        subject = "Nam Hoa Kinh"
    elif series.upper() == "TÔI LÀM VIỆC":
        subject = ""
    elif "ai agency" in raw_title.lower() or "ai" in raw_title.lower():
        subject = "Thời Đại AI"
    elif "quản lý" in raw_title.lower():
        subject = "Bài Học Quản Trị"
    elif "riêng tư" in raw_title.lower():
        subject = "Xã Hội Số"
    elif "thế hệ" in raw_title.lower() or "generational" in raw_title.lower():
        subject = "Khủng Hoảng Gen Y"

    if subject and len(hook) <= 35 and subject.lower() not in hook.lower():
        candidate = f"{hook} - {subject} | {channel_brand}"
    else:
        candidate = f"{hook} | {channel_brand}"

    # Mobile target: keep full title if under 80 chars, otherwise truncate cleanly without cutting channel brand
    if len(candidate) > 85:
        max_hook_len = 80 - len(f" | {channel_brand}")
        clean_hook = hook[:max_hook_len].rsplit(" ", 1)[0]
        candidate = f"{clean_hook} | {channel_brand}"

    return unicodedata.normalize("NFC", candidate)


def build_seo_tags(channel: str, content: str, raw_title: str, frontmatter_tags: Optional[List[str]] = None, is_short: bool = False) -> List[str]:
    """
    Build 3-Tier Keyword Taxonomy:
    - Tier 1: Brand & Broad (Biết Địa lý từ Ba tôi / Tôi Đọc Sách / ZenPham)
    - Tier 2: Niche / Subject / Author entities & Frontmatter tags
    - Tier 3: High-intent long-tail search queries
    Max YouTube limit is 500 chars; budget target ~430-480 chars.
    """
    tags = []
    text_lower = (content + " " + raw_title).lower()

    # Tier 1: Brand & Broad
    if channel == "PHAMTRAI_DIALY":
        tier_1 = [
            "Biết Địa lý từ Ba tôi", "Biet Dia Ly Tu Ba Toi", "Phạm Trãi",
            "Địa Lý Việt Nam", "Việt Nam Những Miền Sống", "Phim Tài Liệu",
            "Khám Phá Việt Nam", "Địa Lý Nhân Văn"
        ]
        if any(w in text_lower for w in ["sông nước", "miền tây", "mê kông", "cửu long"]):
            tier_1.append("Văn Hóa Sông Nước")
    elif channel == "TOI_DOC_SACH":
        tier_1 = ["Tôi Đọc Sách", "Toi Doc Sach", "Review Sách", "Triết Học", "Podcast Tiếng Việt", "Sách Hay Mỗi Ngày"]
    elif channel == "REALITY_DECODE":
        tier_1 = [
            "REALITY DECODE", "Reality Decode", "Giải Mã Thực Tại", "RealityDecode",
            "Khoa Học", "Công Nghệ", "Trí Tuệ Nhân Tạo", "Tư Duy Phản Biện", "Khám Phá"
        ]
        if is_short:
            tier_1.extend(["Shorts", "YouTubeShorts"])
    else:
        tier_1 = ["ZenPham", "Tôi Làm Việc", "Triết Học Đời Thường", "Công Nghệ", "Toán Học AI", "Machine Learning"]
        if is_short:
            tier_1.extend(["Shorts", "YouTubeShorts"])
    tags.extend(tier_1)

    # Inject frontmatter tags if present
    if frontmatter_tags:
        for fmt in frontmatter_tags:
            fmt_clean = fmt.strip()
            if fmt_clean and fmt_clean not in tags:
                tags.append(fmt_clean)

    # Tier 2: Specific Entities
    entity_map = {
        "mê kông": ["Sông Mê Kông", "Mekong River", "Đồng Bằng Sông Cửu Long", "Phù Sa"],
        "cửu long": ["Đồng Bằng Sông Cửu Long", "Miền Tây", "Sông Tiền", "Sông Hậu"],
        "sông nước": ["Văn Hóa Sông Nước", "Ghe Xuồng", "Kênh Rạch", "Miền Tây Nam Bộ"],
        "chợ nổi": ["Chợ Nổi", "Chợ Nổi Cái Răng", "Thương Hồ", "Giao Thương Đường Thủy"],
        "hà nội": ["Hà Nội", "Thăng Long", "Hồ Gươm", "Cầu Long Biên", "Phố Cổ Hà Nội", "Sông Hồng"],
        "huế": ["Huế", "Cố Đô Huế", "Sông Hương", "Núi Ngự Bình", "Kinh Thành Huế", "Đại Nội Huế", "Lăng Khải Định", "Lăng Tự Đức", "Cầu Trường Tiền", "Đầm Phá Tam Giang", "Chùa Thiên Mụ"],
        "hội an": ["Hội An", "Phố Cổ Hội An", "Sông Thu Bồn", "Sông Hoài", "Chùa Cầu", "Cửa Đại", "Di Sản Thế Giới UNESCO", "Thương Cảng Cổ", "Kiến Trúc Nhà Cổ", "Đèn Lồng Hội An"],
        "thu bồn": ["Sông Thu Bồn", "Hạ Lưu Thu Bồn", "Cửa Đại", "Quảng Nam"],
        "chùa cầu": ["Chùa Cầu", "Lai Viễn Kiều", "Kiến Trúc Nhật Bản Hội An"],
        "tây nguyên": ["Tây Nguyên", "Cao Nguyên", "Đại Ngàn Tây Nguyên", "Văn Hóa Tây Nguyên", "Khám Phá Tây Nguyên"],
        "bazan": ["Đất Đỏ Bazan", "Núi Lửa Cổ", "Địa Mạo Cao Nguyên", "Nông Nghiệp Cao Nguyên"],
        "cà phê": ["Cà Phê Sài Gòn", "Văn Hóa Cà Phê", "Cà Phê Vợt"] if "sài gòn" in text_lower else ["Cà Phê Tây Nguyên", "Cà Phê Buôn Ma Thuột", "Hạt Cà Phê Việt Nam", "Nông Trường Cà Phê"],
        "cà phê tây nguyên": ["Cà Phê Tây Nguyên", "Cà Phê Buôn Ma Thuột", "Hạt Cà Phê Việt Nam", "Nông Trường Cà Phê"],
        "cồng chiêng": ["Không Gian Văn Hóa Cồng Chiêng", "Cồng Chiêng Tây Nguyên", "Di Sản UNESCO Tây Nguyên", "Âm Vang Đại Ngàn"],
        "nhà rông": ["Nhà Rông Ba Na", "Kiến Trúc Nhà Rông", "Buôn Làng Tây Nguyên"],
        "nhà dài": ["Nhà Dài Ê Đê", "Văn Hóa Mẫu Hệ", "Kiến Trúc Nhà Dài"],
        "đắk lắk": ["Đắk Lắk", "Buôn Ma Thuột", "Thác Dray Nur"],
        "kon tum": ["Kon Tum", "Sông Đăk Bla", "Cầu Treo Kon Klor", "Nhà Thờ Gỗ Kon Tum"],
        "gia lai": ["Gia Lai", "Pleiku", "Sông Sê San"],
        "srêpôk": ["Sông Srêpôk", "Dòng Sông Chảy Ngược", "Hệ Thống Sông Tây Nguyên"],
        "lâm đồng": ["Lâm Đồng", "Đà Lạt", "Cao Nguyên Lâm Viên"],
        "chư yang sin": ["Vườn Quốc Gia Chư Yang Sin", "Rừng Nguyên Sinh Tây Nguyên"],
        "sài gòn": ["Sài Gòn", "TP Hồ Chí Minh", "Sông Sài Gòn", "Địa Lý Sài Gòn", "Cầu Ba Son", "Bến Bạch Đằng", "Landmark 81"],
        "cà mau": ["Cà Mau", "Mũi Cà Mau", "Rừng Đước Năm Căn", "U Minh Hạ", "Sông Cửa Lớn", "Hải Lưu Ven Bờ", "Rừng Ngập Mặn", "Địa Đầu Tổ Quốc"],
        "đất mũi": ["Đất Mũi Cà Mau", "Mốc Tọa Độ GPS 0001", "Biển Tây", "Biển Đông", "Bán Đảo Cà Mau"],
        "u minh": ["U Minh Hạ", "Rừng Tràm U Minh", "Đầm Lầy Than Bùn", "Gác Kèo Ong"],
        "hồ chí minh": ["TP Hồ Chí Minh", "Sài Gòn", "Đô Thị Phương Nam", "Kinh Tế Sài Gòn"],
        "thủ thiêm": ["Bán Đảo Thủ Thiêm", "Hầm Thủ Thiêm", "Cầu Thủ Thiêm", "Sông Sài Gòn"],
        "cát lái": ["Cảng Cát Lái", "Cụm Cảng Sài Gòn", "Logistics", "Cửa Ngõ Cảng Biển"],
        "chợ lớn": ["Chợ Lớn", "Chợ Bình Tây", "Giao Thương Chợ Lớn", "Phố Người Hoa"],
        "bến nghé": ["Kênh Bến Nghé", "Bến Nghé Sài Gòn", "Lịch Sử Sài Gòn"],
        "cần giờ": ["Cần Giờ", "Rừng Sác Cần Giờ", "Cửa Biển Soài Rạp"],
        "lăng tẩm": ["Lăng Tẩm Triều Nguyễn", "Lăng Khải Định", "Lăng Tự Đức", "Kiến Trúc Cung Đình"],
        "đờn ca tài tử": ["Đờn Ca Tài Tử", "Âm Nhạc Dân Gian", "Di Sản Phi Vật Thể UNESCO"],
        "nam hoa kinh": ["Nam Hoa Kinh", "Trang Tử", "Tề Vật Luận", "Lão Trang"],
        "trang tử": ["Trang Tử", "Đạo Gia", "Vô Vi"],
        "camus": ["Albert Camus", "Kẻ Xa Lạ", "Chủ Nghĩa Hiện Sinh"],
        "khắc kỷ": ["Khắc Kỷ", "Stoicism", "Marcus Aurelius", "Epictetus"],
        "nguyễn hiến lê": ["Nguyễn Hiến Lê", "Học Giả"],
        "thu giang": ["Thu Giang Nguyễn Duy Cần"],
        "ai": ["Trí Tuệ Nhân Tạo", "AI Agency", "Công Nghệ Tương Lai"],
        "thuật toán": ["Bản Án Thuật Toán", "Mạng Xã Hội", "Thao Túng Tâm Lý"],
        "quản lý": ["Quản Lý và Quản Trị", "Lãnh Đạo", "Tâm Lý Công Sở"],
        "riêng tư": ["Quyền Riêng Tư", "Bảo Mật Dữ Liệu"],
        "thế hệ": ["Thế Hệ Giao Thoa", "Khủng Hoảng Tuổi 30", "Gen Y"],
        "máu lạnh": ["Máu Lạnh", "In Cold Blood", "Truman Capote", "Tội Phạm Học"],
        "cold blood": ["In Cold Blood", "Truman Capote", "Tội Phạm Học Hiện Thực"],
        "cái ác": ["Bản Chất Cái Ác", "Tội Phạm Học", "Tâm Lý Học Tội Phạm", "Psychopath"],
        "đề phòng": ["Cơ Chế Phòng Vệ", "Tâm Lý Học Đám Đông", "Phản Biện Xã Hội", "Lòng Trắc Ẩn"],
        "ramirez": ["Richard Ramirez", "Hồ Sơ Tội Phạm"],
        "tôi làm việc": ["Tôi Làm Việc", "Zenpham Tôi Làm Việc", "Kỹ Sư AI", "Digital Craftsmanship", "Kỹ Thuật AI", "Toán Học AI"],
        "xác suất": ["Xác Suất trong AI", "Định Lý Bayes", "Toán Học AI", "Machine Learning", "Manim"],
        "đạo hàm": ["Đạo Hàm trong AI", "Gradient Descent", "Toán Học AI", "Calculus Machine Learning"],
        "gradient": ["Gradient Descent", "Đạo Hàm Riêng", "Tối Ưu Hóa", "Loss Landscape", "Hàm Mất Mát"],
        "adam": ["Adam Optimizer", "SGD", "Momentum", "Thuật Toán Tối Ưu"],
        "learning rate": ["Learning Rate", "Tốc Độ Học", "Huấn Luyện AI", "Overfitting"],
        "backpropagation": ["Backpropagation", "Lan Truyền Ngược", "Mạng Nơ-ron", "Deep Learning"],
        "manim": ["Manim", "Math Animation", "Trực Quan Hóa Dữ Liệu", "Manim 3D"],
        "kỹ sư": ["Kỹ Sư Phần Mềm", "Nghề Lập Trình", "Kinh Nghiệm Kỹ Sư", "Văn Hóa Kỹ Sư"],
    }
    for k, v in entity_map.items():
        if re.search(rf"(?:^|[^\w]){re.escape(k)}(?:[^\w]|$)", text_lower):
            for item in v:
                if item not in tags:
                    tags.append(item)

    # Tier 3: Long-tail Intent Phrases
    if channel == "PHAMTRAI_DIALY":
        intent_candidates = [
            "khám phá địa lý việt nam",
            "lịch sử và văn hóa việt nam",
            "vẻ đẹp sông núi việt nam",
            "phim tài liệu địa lý nhân văn",
            "bài học làm người từ địa lý",
            "câu chuyện người cha kể cho con",
            "những miền sống việt nam",
            "di sản văn hóa thế giới unesco",
            "hiểu một vùng đất để hiểu con người"
        ]
        if "sài gòn" in text_lower or "hồ chí minh" in text_lower or "thủ thiêm" in text_lower:
            intent_candidates.extend(["vì sao sài gòn phát triển", "địa lý sài gòn xưa và nay", "sông sài gòn và kinh tế biển", "lịch sử cảng sài gòn"])
        elif "tây nguyên" in text_lower or "cao nguyên" in text_lower:
            intent_candidates.extend(["khám phá tây nguyên đại ngàn", "văn hóa cồng chiêng tây nguyên", "đất đỏ bazan và cà phê", "địa mạo cao nguyên xếp tầng", "di sản cồng chiêng unesco"])
        elif "hội an" in text_lower or "thu bồn" in text_lower:
            intent_candidates.extend(["khám phá phố cổ hội an", "lịch sử thương cảng hội an", "văn hóa giao thương sông nước"])
        elif "huế" in text_lower or "hương giang" in text_lower:
            intent_candidates.extend(["tìm hiểu cố đô huế", "văn hóa và phong cảnh huế"])
        elif "hà nội" in text_lower or "thăng long" in text_lower:
            intent_candidates.extend(["lịch sử thăng long hà nội", "ngàn năm văn hiến"])
        elif "mê kông" in text_lower or "cửu long" in text_lower:
            intent_candidates.extend(["khám phá miền tây nam bộ", "văn hóa sông nước mê kông"])
        elif "cà mau" in text_lower or "đất mũi" in text_lower or "u minh" in text_lower:
            intent_candidates.extend(["khám phá đất mũi cà mau", "địa lý cà mau và đường bờ biển", "hệ sinh thái rừng ngập mặn", "sống chung với biến đổi khí hậu"])
    else:
        intent_candidates = [
            "cách buông bỏ hơn thua",
            "học cách chấp nhận",
            "triết học ứng dụng đời sống",
            "đọc sách ban đêm",
            "tâm sự đêm muộn",
            "chữa lành tâm hồn",
            "suy ngẫm cuộc đời",
            "cân bằng cuộc sống",
            "tìm lại chính mình",
            "vượt qua áp lực",
            "bình yên nội tại",
            "thói quen đọc sách"
        ]
        if "tôi làm việc" in text_lower or "kỹ sư" in text_lower or "gradient" in text_lower:
            intent_candidates.extend([
                "đạo làm nghề kỹ sư",
                "toán học đằng sau ai",
                "tư duy kỹ thuật giải quyết vấn đề",
                "digital craftsmanship ai",
                "học machine learning thực tế",
                "bản chất gradient descent"
            ])
    for phrase in intent_candidates:
        tags.append(phrase)

    # Clean & ensure uniqueness, strictly respecting YouTube 400 UTF-8 byte limit
    seen = set()
    final_tags = []
    total_bytes = 0
    for t in tags:
        t_clean = unicodedata.normalize("NFC", t.strip())
        t_clean = re.sub(r"[<>]", "", t_clean).strip()
        if not t_clean:
            continue
        t_bytes = len(t_clean.encode("utf-8")) + 1
        if t_clean.lower() not in seen:
            seen.add(t_clean.lower())
            if total_bytes + t_bytes <= 390:
                final_tags.append(t_clean)
                total_bytes += t_bytes

    return final_tags


def build_seo_description(
    channel: str,
    title: str,
    script_info: Dict,
    scene_durations: Optional[List[float]] = None
) -> str:
    """
    Rich Description Builder:
    - If Shorts: High-converting teaser + Direct link to Full 16:9 Episode + CTA + Hashtags
    - If Longform: 4-part description with Backlink to 30s Short + Chapters + Credits + Hashtags
    """
    is_short = script_info.get("is_short", False)
    raw_title = script_info["raw_title"]
    source = script_info["source"]
    related_longform_id = script_info.get("related_longform_id", "")
    related_short_id = script_info.get("related_short_id", "")
    scenes = script_info["scenes"]

    # SPECIALIZED SHORTS DESCRIPTION (High-Converting Traffic Funnel)
    if is_short:
        long_url = f"https://youtube.com/watch?v={related_longform_id}" if related_longform_id else "https://youtube.com/@zenpham"
        first_d = scenes[0].get("dialogue", "") if scenes else ""
        lines = [
            f"{title}\n",
            f"\"{first_d}\"" if first_d else "Lúc 2 giờ sáng, điều kỹ sư AI sợ nhất là khi hàm mất mát nhảy về NaN.",
            "",
            "─────────────────────────────────────────",
            "👉 XEM BẢN PHÂN TÍCH TOÁN HỌC CHI TIẾT & MÃ NGUỒN MANIM 3D TẠI:",
            f"🔗 {long_url}",
            "─────────────────────────────────────────",
            "",
            "💻 SERIES: TÔI LÀM VIỆC (ZENPHAM)",
            "Chia sẻ về đạo làm nghề (Digital Craftsmanship), bản chất toán học đằng sau trí tuệ nhân tạo và tư duy kỹ thuật hệ thống tại phòng lab.",
            "",
            "🎙️ Người chia sẻ: Zen (AI Engineering & Digital Craftsmanship)",
            "🎬 Hoạt họa toán học: Manim Engine (Python 3D)",
            "",
            "💬 Bấm vào liên kết video có liên quan (Related Video) hoặc link bên trên để xem bản đầy đủ 16:9 nhé!",
            "",
            "#Shorts #ToiLamViec #ZenPham #AI #MachineLearning #GradientDescent #ToanHocAI #DeepLearning"
        ]
        return unicodedata.normalize("NFC", "\n".join(lines))

    # LONGFORM 16:9 DESCRIPTION
    if script_info.get("central_question"):
        question = script_info["central_question"]
    elif channel == "REALITY_DECODE":
        question = "Bản chất thực sự của thế giới xung quanh chúng ta đang vận hành như thế nào?"
    elif channel == "PHAMTRAI_DIALY":
        question = "Vì sao một vùng đất, một dòng sông hay một đô thị lại mang hình hài như hôm nay?"
    elif script_info.get("series", "").upper() == "TÔI LÀM VIỆC" or "tôi làm việc" in str(script_info).lower():
        question = "Bên dưới mọi thuật toán thông minh, cỗ máy thực sự suy nghĩ hay chỉ đang tính toán xác suất?"
    else:
        question = "Nếu cuộc sống cứ cuốn ta vào những hơn thua, đâu là điểm tựa để lòng mình an yên?"

    if channel == "REALITY_DECODE":
        channel_name = "REALITY DECODE"
        above_fold = f"{title}\n\n{question}\n\"Giải mã thế giới để nhìn thấu bản chất.\""
        body_lines = [
            "─────────────────────────────────────────",
            "🔍 VỀ KÊNH & NỘI DUNG TẬP NÀY:",
            "Kênh 'REALITY DECODE' giải mã bản chất thực tại qua lăng kính khoa học, công nghệ, tư duy đa chiều và triết học sâu sắc.",
            "Cùng bóc tách các lớp màn thực tại để hiểu cách vạn vật thực sự vận hành.",
            "",
            "“Đừng chỉ nhìn bề mặt. Hãy giải mã những gì đang diễn ra bên dưới.”",
        ]
        if source:
            body_lines.append(f"• Nguồn tư liệu & Đối chiếu: {source}")
    elif channel == "PHAMTRAI_DIALY":
        channel_name = "BIẾT ĐỊA LÝ TỪ BA TÔI"
        above_fold = f"{title}\n\n{question}\n\"Hiểu một vùng đất, để hiểu những người sống trên đó.\""
        body_lines = [
            "─────────────────────────────────────────",
            "🗺️ VỀ KÊNH & NỘI DUNG TẬP NÀY:",
            "Kênh 'BIẾT ĐỊA LÝ TỪ BA TÔI' kể câu chuyện địa lý như lời một người cha giải thích cho con về vì sao đất nước và con người Việt Nam lại hình thành như hôm nay.",
            "Một phong cách documentary nghiêm túc, chuẩn xác dữ liệu nhưng gần gũi, ấm áp và dễ hiểu, không khô cứng học thuật.",
            "",
            "“Địa lý không chỉ nằm trên bản đồ. Nó nằm trong cách con người sống.”",
        ]
        if source:
            body_lines.append(f"• Nguồn tư liệu & Đối chiếu: {source}")
    elif channel == "TOI_DOC_SACH":
        channel_name = "TÔI ĐỌC SÁCH"
        above_fold = f"{title}\n\n{question}\nMột góc nhìn sâu lắng, điềm đạm và đối thoại chân thành cùng bạn."
        body_lines = [
            "─────────────────────────────────────────",
            "📖 VỀ NỘI DUNG TẬP NÀY:",
        ]
        if source:
            body_lines.append(f"• Tác phẩm & Nguồn tư tưởng: {source}")
        body_lines.append(
            "Chúng ta không đọc sách để ghi nhớ câu chữ hay tỏ ra thông thái. "
            "Ta ngồi xuống, mở một trang sách cũ, đem một câu hỏi thật của đời sống hôm nay ra đối thoại, "
            "để rồi cùng giữ lại một khoảng lặng đáng sống cùng."
        )
    elif channel == "ZENPHAM" and (script_info.get("series", "").upper() == "TÔI LÀM VIỆC" or "tôi làm việc" in str(script_info).lower()):
        channel_name = "ZENPHAM • TÔI LÀM VIỆC"
        above_fold = f"{title}\n\n{question}\nMột góc nhìn sâu sắc từ trải nghiệm thực tế nghiên cứu và kỹ thuật hệ thống tại phòng lab."
        body_lines = [
            "─────────────────────────────────────────",
            "💻 VỀ SERIES 'TÔI LÀM VIỆC':",
            "Một không gian chia sẻ về đạo làm nghề (Digital Craftsmanship), toán học đằng sau các mô hình AI, và những chiêm nghiệm thực tế trong hành trình phát triển phần mềm và kỹ thuật AI của Zen.",
            "Không lý thuyết sáo rỗng, không bán khóa học — chỉ có sự điềm đạm của người thợ và vẻ đẹp của toán học.",
        ]
        if related_short_id:
            body_lines.extend([
                "",
                f"📱 Xem tóm tắt nhanh 50s của tập này: https://youtube.com/shorts/{related_short_id}",
            ])
        if source:
            body_lines.append(f"• Tác phẩm & Nguồn tư tưởng: {source}")
    else:
        channel_name = "ZENPHAM"
        above_fold = f"{title}\n\n{question}\nMột góc nhìn sâu lắng, điềm đạm và đối thoại chân thành cùng bạn."
        body_lines = [
            "─────────────────────────────────────────",
            "📖 VỀ NỘI DUNG TẬP NÀY:",
        ]
        if source:
            body_lines.append(f"• Tác phẩm & Nguồn tư tưởng: {source}")
        body_lines.append(
            "Chúng ta quan sát thế giới không phải để phán xét hay bức xúc, "
            "mà để hiểu vì sao mọi thứ lại vận hành như vậy và giữ lấy sự tự chủ bên trong mình."
        )

    # 3. Chapters / Timestamps
    chapter_lines = [
        "─────────────────────────────────────────",
        "⏱️ MỤC LỤC THỜI GIAN (CHAPTERS):",
    ]
    accum = 0.0

    def _format_chapter(heading: str, idx: int) -> str:
        h = re.sub(r"^(?:Đoạn|Phần|Scene)\s*\d+\s*[:—–\-]\s*", "", heading, flags=re.I).strip()
        h = re.sub(r"\s*[—–\-]\s*Tap\w+$", "", h, flags=re.I).strip()
        h = re.sub(r"\s*\(.*?\)", "", h).strip()
        if ":" in h and len(h) > 45:
            h = h.split(":", 1)[0].strip()
        if len(h) > 60:
            h = h[:57].rstrip() + "..."
        return h or f"Phần {idx}"

    if scene_durations and len(scene_durations) == len(scenes):
        for i, (sc, dur) in enumerate(zip(scenes, scene_durations), 1):
            mm = int(accum) // 60
            ss = int(accum) % 60
            chapter_lines.append(f"{mm:02d}:{ss:02d} - {_format_chapter(sc['heading'], i)}")
            accum += dur
    else:
        for i, sc in enumerate(scenes, 1):
            mm = int(accum) // 60
            ss = int(accum) % 60
            chapter_lines.append(f"{mm:02d}:{ss:02d} - {_format_chapter(sc['heading'], i)}")
            accum += 30.0

    # 4. Credits, CTA & Hashtags
    footer_lines = [
        "─────────────────────────────────────────",
        f"🎙️ Giọng đọc: {('Nam miền Tây (Trầm ấm, đĩnh đạc, tự sự phim tài liệu)' if channel == 'PHAMTRAI_DIALY' else 'ZenPham (Nam miền Tây trung niên — Giọng thiền định suy tư)')}",
        "✨ Phụ đề: Faster-Whisper Word-Level Alignment (Chuẩn xác 100%)",
        f"📺 Kênh: {channel_name}",
        "",
        "💬 ĐÀM ĐẠO CÙNG CHÚNG TÔI:",
        "Bạn nghĩ sao về câu hỏi trong tập này? Hãy để lại một dòng cảm nghĩ của bạn dưới phần bình luận để chúng ta cùng trò chuyện nhé.",
        "Nếu video mang lại cho bạn một góc nhìn sâu sắc, đừng quên bấm Thích và Đăng Ký Kênh để đồng hành trong những tập tiếp theo.",
        "",
    ]

    if channel == "PHAMTRAI_DIALY":
        text_context = (raw_title + " " + " ".join(s.get("dialogue", "") for s in scenes)).lower()
        region_tag = "#DiaLyNhanVan"
        if "tây nguyên" in text_context or "cao nguyên" in text_context:
            region_tag = "#TayNguyen #CongChiengTayNguyen #DatDoBazan"
        elif "hội an" in text_context:
            region_tag = "#HoiAn #PhoCoHoiAn #SongThuBon"
        elif "huế" in text_context:
            region_tag = "#CoDoHue #SongHuong #VanHoaHue"
        elif "hà nội" in text_context:
            region_tag = "#HaNoi #ThangLong #SongHong"
        elif "mê kông" in text_context or "miền tây" in text_context:
            region_tag = "#MienTaySongNuoc #DongBangSongCuuLong #SongMeKong"
        footer_lines.append(f"#BietDiaLyTuBaToi #PhamTrai #DiaLyVietNam #VietNamNhungMienSong #PhimTaiLieu {region_tag} #VanHoaVietNam")
    elif channel == "TOI_DOC_SACH":
        footer_lines.append("#ToiDocSach #TrietHocDoiThuong #NamHoaKinh #TrangTu #DocSachMoiNgay #ChuaLanh #PodcastViet")
    elif channel == "REALITY_DECODE":
        footer_lines.append("#RealityDecode #GiaiMaThucTai #KhoaHoc #CongNghe #AI #TuDuyPhanBien #TriThuc")
    else:
        footer_lines.append("#ZenPham #ToiLamViec #TrietHocDoiThuong #CongNghe #ToanHocAI #MachineLearning #DeepLearning #PodcastViet")

    desc_parts = [above_fold, "\n".join(body_lines), "\n".join(chapter_lines), "\n".join(footer_lines)]
    return unicodedata.normalize("NFC", "\n\n".join(desc_parts))


def build_seo_metadata(
    md_path: Path,
    scene_durations: Optional[List[float]] = None,
    related_longform_id: Optional[str] = None,
    related_short_id: Optional[str] = None,
) -> Dict:
    """Master SEO Builder: parses markdown and returns complete YouTube upload metadata."""
    if not md_path.exists():
        raise FileNotFoundError(f"Script not found: {md_path}")

    content = md_path.read_text(encoding="utf-8")
    channel = detect_channel(md_path, content)
    script_info = extract_script_info(content)

    if related_longform_id:
        script_info["related_longform_id"] = related_longform_id
    if related_short_id:
        script_info["related_short_id"] = related_short_id

    # Auto-probe scene durations if available
    if scene_durations is None:
        m_ep = re.search(r"tap_(\d+)", md_path.stem)
        candidate_dirs = []
        if m_ep:
            ep_num = m_ep.group(1).zfill(2)
            candidate_dirs.append(md_path.parent / "output" / "youtube_staging" / "series_01" / f"tap_{ep_num}" / "clips")
            candidate_dirs.append(md_path.parent / "clips" / f"tap_{ep_num}")
            candidate_dirs.append(md_path.parent / "clips" / "series_01" / f"tap_{ep_num}")
        for cdir in candidate_dirs:
            if cdir.exists():
                c_files = sorted(list(cdir.glob("clip_*.mp4")))
                if len(c_files) == len(script_info["scenes"]):
                    durs = []
                    try:
                        import subprocess
                        for cf in c_files:
                            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(cf)], capture_output=True, text=True)
                            durs.append(float(r.stdout.strip()))
                        if len(durs) == len(script_info["scenes"]):
                            scene_durations = durs
                            break
                    except Exception:
                        pass

    is_short = script_info.get("is_short", False)
    title = build_seo_title(
        script_info["raw_title"],
        channel,
        script_info["source"],
        script_info.get("series", ""),
        is_short=is_short,
        episode=script_info.get("episode", "")
    )
    tags = build_seo_tags(
        channel,
        content,
        script_info["raw_title"],
        frontmatter_tags=script_info.get("frontmatter_tags", []),
        is_short=is_short
    )
    description = build_seo_description(channel, title, script_info, scene_durations)
    token_path, is_specific = resolve_channel_token(channel)

    is_landscape = not is_short

    return {
        "channel": channel,
        "title": title,
        "description": description,
        "tags": tags,
        "tags_str": ",".join(tags),
        "token_path": str(token_path),
        "is_specific_token": is_specific,
        "category_id": "27",  # Education
        "default_language": "vi",
        "is_landscape": is_landscape,
        "is_short": is_short,
        "total_scenes": len(script_info["scenes"]),
        "related_longform_id": script_info.get("related_longform_id", ""),
        "related_short_id": script_info.get("related_short_id", ""),
    }


if __name__ == "__main__":
    import sys
    test_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/zen/hermes-agent/assets/scripts_video/toi_doc_sach_nam_hoa_kinh.md")
    res = build_seo_metadata(test_file)
    print("=== SEO METADATA TEST ===")
    print(f"Channel: {res['channel']}")
    print(f"Title ({len(res['title'])} chars): {res['title']}")
    print(f"Token Path: {res['token_path']} (specific: {res['is_specific_token']})")
    print(f"Tags Count ({len(res['tags'])} tags, {len(res['tags_str'])} chars): {res['tags_str'][:100]}...")
    print("\n--- DESCRIPTION PREVIEW ---")
    print(res["description"][:500] + "\n...")
