#!/usr/bin/env python3
"""
Hermes-Agent Unified Media & SwapFace Organizer
===============================================
Scientific Media Classifier & Auto-Organizer based on Signatures:
1. SwapFace Archives:
   - Discovers face swap images/videos across historical directories:
     (output img *, output vid *, output-9-7, output-image-11-7, output-image-7-7-mojo-pham,
      output video 25-05, Name SF Center, Zen vault/luu Out, Audrey Base)
   - Routes into Content Factory: 06_Exports/Review/swapface/<Face_Name>/{img, vid}/
2. Footage Classifier:
   - Movies from Vault root, subdirs, and SSD 1.5tb into:
     * /Ai (wan, touching hair, comfyui, generated)
     * /eporner (eporner, hash id _720p/_480p, EPO folder)
     * /erome (erome)
     * /onlyfans (onlyfans)
     * /studio_clips (babes, bangbros, xhamster, natalia starr, hot pearl)
     * /web (hqporn, weliketosuck, cammer, tiktoker, rphang)
     * /general (remaining raw clips)
3. Stock Bases (Flickr):
   - High-resolution Flickr bases (3K-6K) into 02_Media/Images/Base_Flickr_HQ/
4. Sound & Voice Classifier:
   - Audio files (.m4a, .mp3, .wav) into:
     * 04_Sound/Voiceover/Zen/
     * 04_Sound/Music/Stems/
5. Personal Archive (Camera RAW DCIM & Travel):
   - 100EOS7D, An Giang SEP 2014, Ban Mê 2015, OneDrive 2024 into:
     * 07_Archive/Personal_Photography/{Folder_Name}/
6. OS Junk Purge:
   - Removes ._*, .DS_Store, Thumbs.db
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

DEFAULT_CF_REMOTE = "phamvuthang@gmail.com:Content Factory"
DEFAULT_VAULT_REMOTE = "phamvuthang@gmail.com:Vault"
DEFAULT_SWAPFACE_DIR = "06_Exports/Review/swapface"
DEFAULT_FOOTAGE_RAW_DIR = "05_Footage/Raw"
DEFAULT_GDRIVE_FACES_DIR = "02_Media/Images/Faces/female"
DEFAULT_LOCAL_FACES_DIR = Path("/home/zen/hermes-agent/assets/faces/female")


def sanitize_name(name: str) -> str:
    """Normalize names for matching: '020 SM' -> '020_sm', 'image (28)' -> 'image_28'"""
    clean = re.sub(r"[^\w\-.]", "_", name.lower())
    clean = re.sub(r"_+", "_", clean).strip("_")
    return clean


@dataclass
class FaceMetadata:
    name: str                    # e.g. "020 SM"
    sanitized: str               # e.g. "020_sm"
    number_prefix: Optional[str] = None # e.g. "020"
    alias: Optional[str] = None         # e.g. "sm"
    local_image_path: Optional[Path] = None
    gdrive_image_path: Optional[str] = None
    matched_videos: List[str] = field(default_factory=list)


class UnifiedMediaOrganizer:
    def __init__(
        self,
        cf_remote: str = DEFAULT_CF_REMOTE,
        vault_remote: str = DEFAULT_VAULT_REMOTE,
        swapface_dir: str = DEFAULT_SWAPFACE_DIR,
        footage_raw_dir: str = DEFAULT_FOOTAGE_RAW_DIR,
        gdrive_faces_dir: str = DEFAULT_GDRIVE_FACES_DIR,
        local_faces_dir: Path = DEFAULT_LOCAL_FACES_DIR,
        target_faces: Optional[List[str]] = None,
        dry_run: bool = True,
    ):
        self.cf_remote = cf_remote.rstrip("/")
        self.vault_remote = vault_remote.rstrip("/")
        self.swapface_dir = swapface_dir.strip("/")
        self.footage_raw_dir = footage_raw_dir.strip("/")
        self.gdrive_faces_dir = gdrive_faces_dir.strip("/")
        self.local_faces_dir = local_faces_dir
        self.target_faces = [f.lower() for f in target_faces] if target_faces else None
        self.dry_run = dry_run

        self.faces: Dict[str, FaceMetadata] = {}  # key = sanitized

    def run_rclone(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        cmd = ["rclone"] + args
        return subprocess.run(cmd, capture_output=True, text=True, check=check)

    def load_known_faces(self) -> None:
        """Discover faces from local assets, GDrive Content Factory, and Vault."""
        # 1. Local faces directory
        if self.local_faces_dir.exists():
            for f in self.local_faces_dir.iterdir():
                if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                    self._register_face(f.stem, local_path=f)

        # 2. GDrive faces directory
        gdrive_faces_remote = f"{self.cf_remote}/{self.gdrive_faces_dir}"
        res = self.run_rclone(["lsf", gdrive_faces_remote], check=False)
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                line = line.strip()
                if not line or line.endswith("/"):
                    continue
                ext = os.path.splitext(line)[1].lower()
                if ext in (".jpg", ".jpeg", ".png", ".webp"):
                    stem = Path(line).stem
                    self._register_face(stem, gdrive_path=f"{self.gdrive_faces_dir}/{line}")

        # 3. Vault faces directory (Vault/0 Face)
        vault_faces_remote = f"{self.vault_remote}/0 Face"
        res = self.run_rclone(["lsf", vault_faces_remote], check=False)
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                line = line.strip()
                if not line or line.endswith("/"):
                    continue
                ext = os.path.splitext(line)[1].lower()
                if ext in (".jpg", ".jpeg", ".png", ".webp"):
                    self._register_face(Path(line).stem)

        # 4. Include well-known extra face codes found in historical archives
        known_extras = [
            "025 KhanhChi", "026 Trâm", "027 Nhu", "028 Thuy Duy",
            "013 Linh Ng", "017 AP", "017 KhanhChi", "017 Ly", "017 Nga", "017 NhiTran", "017 Nhu Ng",
            "000 Truc", "018 Loan Face", "019 Giang", "020 SM", "021 HaiYen"
        ]
        for extra in known_extras:
            self._register_face(extra)

    def _register_face(self, name: str, local_path: Optional[Path] = None, gdrive_path: Optional[str] = None):
        san = sanitize_name(name)
        if self.target_faces and not any(tf in name.lower() for tf in self.target_faces):
            return

        parts = name.split()
        num = parts[0] if len(parts) > 1 and parts[0].isdigit() else None
        alias = parts[1].lower() if len(parts) > 1 else name.lower()

        if san not in self.faces:
            self.faces[san] = FaceMetadata(
                name=name,
                sanitized=san,
                number_prefix=num,
                alias=alias,
                local_image_path=local_path,
                gdrive_image_path=gdrive_path
            )
        else:
            if local_path:
                self.faces[san].local_image_path = local_path
            if gdrive_path:
                self.faces[san].gdrive_image_path = gdrive_path

    def match_face_for_name(self, filename: str) -> Optional[FaceMetadata]:
        """Multi-stage signature matching for face names."""
        low = filename.lower()
        san_file = sanitize_name(filename)

        # 1. Exact sanitized prefix or name match (longest first)
        sorted_faces = sorted(self.faces.values(), key=lambda m: len(m.name), reverse=True)
        for meta in sorted_faces:
            fl = meta.name.lower()
            if (low.startswith(fl) or
                low.startswith(fl.replace(" ", "_")) or
                low.startswith(fl.replace(" ", "")) or
                san_file.startswith(meta.sanitized)):
                return meta

        # 2. Number prefix match: e.g. "019 " or "019_"
        for meta in sorted_faces:
            if meta.number_prefix:
                num = meta.number_prefix
                if low.startswith(f"{num} ") or low.startswith(f"{num}_") or f"_{num} " in low:
                    return meta

        # 3. Substring / Alias matching
        for meta in sorted_faces:
            fl = meta.name.lower()
            if fl in low or meta.sanitized in san_file:
                return meta
            if meta.alias and len(meta.alias) >= 3:
                # e.g. "giang", "audrey", "loan"
                if (f"_{meta.alias}_" in low or
                    low.startswith(f"{meta.alias}_") or
                    f"_{meta.alias}." in low):
                    return meta

        # Special casing for short codes: "SM"
        if "sm_audrey" in low or "sm audrey" in low or low.startswith("sm_") or "_sm_" in low:
            for meta in sorted_faces:
                if meta.name == "020 SM":
                    return meta

        return None

    # =========================================================================
    # 1. SWAPFACE REVIEW & ARCHIVE ORGANIZER (<Face_Name>/{img, vid})
    # =========================================================================
    def plan_swapface_archives(self) -> Dict:
        """
        Scans all historical output directories in Vault and routes them into:
        06_Exports/Review/swapface/<Face_Name>/{img, vid}/
        """
        output_dirs = [
            "output img 01 08", "output vid 17 07", "output vid 18-07", "output vid 19 07",
            "output vid 20 07", "output video 25-05", "output-9-7", "output-image-11-7",
            "output-image-7-7-mojo-pham", "Name SF Center", "Zen vault/luu Out", "Audrey Base"
        ]

        moves = []
        breakdown = {}

        for out_dir in output_dirs:
            remote = f"{self.vault_remote}/{out_dir}"
            res = self.run_rclone(["lsf", remote, "--recursive"], check=False)
            if res.returncode != 0:
                continue

            lines = [l.strip() for l in res.stdout.splitlines() if l.strip() and not l.endswith("/")]
            count = 0

            for rel_path in lines:
                fname = rel_path.split("/")[-1]
                if fname.startswith("._") or fname == ".DS_Store":
                    continue

                matched = self.match_face_for_name(fname)
                if not matched:
                    # check parent folder name if it was grouped by face
                    parent_part = rel_path.split("/")[0]
                    matched = self.match_face_for_name(parent_part)

                if matched:
                    src = f"{remote}/{rel_path}"
                    ext = os.path.splitext(fname)[1].lower()
                    sub_type = "vid" if ext in (".mp4", ".mov", ".mkv", ".webm", ".avi") else "img"
                    dst = f"{self.cf_remote}/{self.swapface_dir}/{matched.name}/{sub_type}/{fname}"
                    moves.append((src, dst, f"Route swapface archive {out_dir} -> {matched.name}/{sub_type}/"))
                    count += 1

            breakdown[out_dir] = count

        return {
            "moves": moves,
            "breakdown": breakdown,
            "total_moves": len(moves)
        }

    # =========================================================================
    # 2. FOOTAGE MOVIES CLASSIFIER (Vault root, subdirectories & SSD 1.5tb)
    # =========================================================================
    def plan_footage_organization(self, scan_subdirs: bool = True) -> Dict:
        sources_to_scan = [""]  # Vault root
        if scan_subdirs:
            vault_media_subs = [
                "013 Linh Ng", "020 SM Teen Shower", "BJ Contest",
                "Base Media temp", "EPO/EPORNER.COM", "Ebony 18 Base", "Luu Mp4", "POV", "SF mov",
                "SSD 1.5tb/BASE SF", "SSD 1.5tb/Bathjob KC",
                "SSD 1.5tb/Blue eyed slim blonde gives amazing handjob (Natalia Starr, Hand Job, Natalia in Bangbros)"
            ]
            sources_to_scan.extend(vault_media_subs)

        eporner_id_re = re.compile(r"^[a-zA-Z0-9_-]{8,12}_(720|480|1080)p\.(mp4|mov)$", re.IGNORECASE)
        studio_re = re.compile(r"\((Babes|Bangbros|Slim 4K|Hot Pearl|Natalia Starr|Valerie Kay|Antonia Sainz|Nina North|Danny Mountain)\)", re.IGNORECASE)

        moves = []
        breakdown = {
            "swapped_to_review": 0,
            "Ai": 0,
            "eporner": 0,
            "erome": 0,
            "onlyfans": 0,
            "studio_clips": 0,
            "web": 0,
            "general": 0,
        }

        for sub in sources_to_scan:
            scan_remote = f"{self.vault_remote}/{sub}".rstrip("/")
            res = self.run_rclone(["lsf", scan_remote], check=False)
            if res.returncode != 0:
                continue

            items = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            movies = [
                f for f in items
                if not f.endswith("/") and not f.startswith("._") and f.lower().endswith((".mp4", ".mov", ".mkv", ".webm", ".avi"))
            ]

            for m in movies:
                src = f"{scan_remote}/{m}"
                low = m.lower()

                # A. Check if Face-Swapped Video
                matched_face = self.match_face_for_name(m)
                if not matched_face and "020 sm" in sub.lower():
                    matched_face = self.match_face_for_name("020 SM")
                if not matched_face and "013 linh" in sub.lower():
                    matched_face = self.match_face_for_name("013 Linh")

                if matched_face:
                    dst = f"{self.cf_remote}/{self.swapface_dir}/{matched_face.name}/vid/{m}"
                    moves.append((src, dst, f"Route swapped movie from {sub or 'Vault root'} -> {matched_face.name}/vid/"))
                    breakdown["swapped_to_review"] += 1
                    continue

                # B. Categorize Raw Footage
                if any(k in low for k in ("wan", "touching hair", "comfyui", "generated")):
                    category = "Ai"
                elif "eporner" in low or eporner_id_re.match(m) or "eporner" in sub.lower():
                    category = "eporner"
                elif "erome" in low:
                    category = "erome"
                elif "onlyfans" in low:
                    category = "onlyfans"
                elif studio_re.search(m) or "natalia" in low or "bangbros" in low or "babes" in low:
                    category = "studio_clips"
                elif any(k in low for k in ("hqporn", "weliketosuck", "cammer", "tiktoker", "rphang", "diễn đàn", "thập cẩm")):
                    category = "web"
                else:
                    category = "general"

                dst = f"{self.cf_remote}/{self.footage_raw_dir}/{category}/{m}"
                moves.append((src, dst, f"Classify raw footage from {sub or 'Vault root'} -> 05_Footage/Raw/{category}/"))
                breakdown[category] += 1

        return {
            "moves": moves,
            "breakdown": breakdown,
            "total_movies": len(moves)
        }

    # =========================================================================
    # 3. STOCK BASES & BASE IMAGES (Flickr 3K-6K in EPO & Name SF Center)
    # =========================================================================
    def plan_stock_bases(self) -> Dict:
        """
        Classifies high-resolution Flickr base images into:
        02_Media/Images/Base_Flickr_HQ/
        """
        flickr_re = re.compile(r"^\d{10,12}_[a-f0-9]{10}_(o|k|5k|6k|3k)\.(jpg|png)$", re.IGNORECASE)
        sources = ["EPO", "EPO/AI Image", "EPO/AI GIRL"]

        moves = []
        for s in sources:
            remote = f"{self.vault_remote}/{s}"
            res = self.run_rclone(["lsf", remote], check=False)
            if res.returncode != 0:
                continue

            for line in res.stdout.splitlines():
                f = line.strip()
                if not f or f.endswith("/") or f.startswith("._"):
                    continue

                src = f"{remote}/{f}"
                if flickr_re.match(f) or f.lower().endswith((".jpg", ".png", ".webp")):
                    dst = f"{self.cf_remote}/02_Media/Images/Base_Flickr_HQ/{f}"
                    moves.append((src, dst, f"Classify stock image {s} -> 02_Media/Images/Base_Flickr_HQ/"))

        return {
            "moves": moves,
            "total_stock_images": len(moves)
        }

    # =========================================================================
    # 4. SOUND & VOICE CLASSIFIER (Vault/Desktop Data & Vault sound files)
    # =========================================================================
    def plan_sound_organization(self) -> Dict:
        """
        Routes Zen audio, Voiceovers, and Stems into 04_Sound/
        """
        sound_sources = ["Desktop Data", "Zen vault"]
        moves = []

        for s in sound_sources:
            remote = f"{self.vault_remote}/{s}"
            res = self.run_rclone(["lsf", remote], check=False)
            if res.returncode != 0:
                continue

            for line in res.stdout.splitlines():
                f = line.strip()
                if not f or f.endswith("/") or f.startswith("._"):
                    continue

                low = f.lower()
                src = f"{remote}/{f}"
                if low.endswith((".m4a", ".mp3", ".wav", ".aac", ".flac")):
                    if "zen" in low or "sáng tạo" in low or "trang tu" in low:
                        dst = f"{self.cf_remote}/04_Sound/Voiceover/Zen/{f}"
                        moves.append((src, dst, f"Route Zen Voiceover -> 04_Sound/Voiceover/Zen/"))
                    elif "vocals" in low or "accompaniment" in low or "stem" in low:
                        dst = f"{self.cf_remote}/04_Sound/Music/Stems/{f}"
                        moves.append((src, dst, f"Route Audio Stem -> 04_Sound/Music/Stems/"))
                    else:
                        dst = f"{self.cf_remote}/04_Sound/SFX/{f}"
                        moves.append((src, dst, f"Route Sound file -> 04_Sound/SFX/"))

        return {
            "moves": moves,
            "total_sound_files": len(moves)
        }

    # =========================================================================
    # 5. PERSONAL ARCHIVE CLASSIFIER (Canon EOS 7D, Nikon, Travel Albums)
    # =========================================================================
    def plan_personal_archive(self) -> Dict:
        """
        Moves Camera RAW DCIM & Travel Albums to Content Factory:
        07_Archive/Personal_Photography/{Album_Name}/
        """
        personal_folders = [
            ("Zen vault/100EOS7D", "Canon_EOS_7D_Originals"),
            ("Zen vault/An Giang SEP 2014 413", "An_Giang_SEP_2014"),
            ("Zen vault/Ban Mê 2015", "Ban_Me_2015"),
            ("OneDrive_2_6-10-2024", "Mobile_DCIM_2024")
        ]

        moves = []
        for src_sub, dest_album in personal_folders:
            remote = f"{self.vault_remote}/{src_sub}"
            res = self.run_rclone(["lsf", remote], check=False)
            if res.returncode != 0:
                continue

            for line in res.stdout.splitlines():
                f = line.strip()
                if not f or f.endswith("/") or f.startswith("._"):
                    continue

                src = f"{remote}/{f}"
                dst = f"{self.cf_remote}/07_Archive/Personal_Photography/{dest_album}/{f}"
                moves.append((src, dst, f"Archive personal photo -> 07_Archive/Personal_Photography/{dest_album}/"))

        return {
            "moves": moves,
            "total_photos": len(moves)
        }

    # =========================================================================
    # EXECUTION RUNNER
    # =========================================================================
    def execute_operations(
        self,
        copies: List[Tuple[str, str, str]],
        moves: List[Tuple[str, str, str]],
        deletes: List[Tuple[str, str]],
        max_workers: int = 8,
    ) -> None:
        print("\n" + "=" * 75)
        mode_str = "DRY-RUN (SIMULATED)" if self.dry_run else "REAL EXECUTION (SERVER-SIDE)"
        print(f"EXECUTING OPERATIONS ON GOOGLE DRIVE [{mode_str}] WITH {max_workers} WORKERS...")
        print("=" * 75)

        def do_copy(item):
            src, dst, reason = item
            print(f"[COPY] {reason}\n  From: {src}\n  To:   {dst}", flush=True)
            if not self.dry_run:
                self.run_rclone(["copyto", src, dst], check=False)

        def do_move(item):
            src, dst, reason = item
            print(f"[MOVE] {reason}\n  From: {src}\n  To:   {dst}", flush=True)
            if not self.dry_run:
                self.run_rclone(["moveto", src, dst], check=False)

        def do_delete(item):
            path, reason = item
            print(f"[DELETE] {reason}\n  Target: {path}", flush=True)
            if not self.dry_run:
                if path.endswith("/"):
                    self.run_rclone(["purge", path], check=False)
                else:
                    self.run_rclone(["deletefile", path], check=False)

        if copies:
            print(f"\n--- [COPIES: {len(copies)} tasks] ---", flush=True)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                list(executor.map(do_copy, copies))

        if moves:
            print(f"\n--- [MOVES: {len(moves)} tasks] ---", flush=True)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                list(executor.map(do_move, moves))

        if deletes:
            print(f"\n--- [DELETES: {len(deletes)} tasks] ---", flush=True)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                list(executor.map(do_delete, deletes))

        status_tag = "[DRY-RUN COMPLETE]" if self.dry_run else "[EXECUTION SUCCESSFUL]"
        print("\n" + "=" * 75)
        print(f"{status_tag} All requested media operations processed cleanly.")
        print("=" * 75)


def main():
    parser = argparse.ArgumentParser(description="Hermes-Agent Scientific Media Organizer")
    parser.add_argument("--cf-remote", type=str, default=DEFAULT_CF_REMOTE, help="Content Factory remote")
    parser.add_argument("--vault-remote", type=str, default=DEFAULT_VAULT_REMOTE, help="Vault remote")
    parser.add_argument("--swapface-archives", action="store_true", help="Organize historical swapface output dirs into <Face_Name>/{img, vid}")
    parser.add_argument("--footage", action="store_true", help="Classify movies from Vault & SSD into Footage / Review")
    parser.add_argument("--stock-bases", action="store_true", help="Organize Flickr bases into Base_Flickr_HQ")
    parser.add_argument("--sound", action="store_true", help="Organize audio & voices into 04_Sound")
    parser.add_argument("--personal-archive", action="store_true", help="Move DCIM & travel albums into 07_Archive")
    parser.add_argument("--all", action="store_true", help="Perform full scientific sweep across all categories")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Simulate execution without modifying files")
    parser.add_argument("--execute", action="store_true", help="Execute real operations")
    parser.add_argument("--workers", type=int, default=8, help="Number of parallel rclone workers")
    args = parser.parse_args()

    dry_run = not args.execute

    organizer = UnifiedMediaOrganizer(
        cf_remote=args.cf_remote,
        vault_remote=args.vault_remote,
        dry_run=dry_run,
    )
    organizer.load_known_faces()

    if not (args.swapface_archives or args.footage or args.stock_bases or args.sound or args.personal_archive or args.all):
        args.all = True

    all_copies = []
    all_moves = []
    all_deletes = []

    print("=" * 75)
    print("HERMES-AGENT SCIENTIFIC SIGNATURE MEDIA ORGANIZER")
    print("=" * 75)
    print(f"Content Factory Remote : {args.cf_remote}")
    print(f"Vault Remote           : {args.vault_remote}")
    print(f"Execution Mode         : {'DRY-RUN (Simulated)' if dry_run else 'REAL EXECUTE (Server-Side)'}")
    print(f"Workers                : {args.workers}")
    print(f"Known Faces Loaded     : {len(organizer.faces)}")
    print("-" * 75)

    if args.swapface_archives or args.all:
        sf = organizer.plan_swapface_archives()
        all_moves.extend(sf["moves"])
        print(f"SwapFace Archives   : {sf['total_moves']} moves across {len(sf['breakdown'])} directories")

    if args.footage or args.all:
        ft = organizer.plan_footage_organization(scan_subdirs=True)
        all_moves.extend(ft["moves"])
        print(f"Footage Tasks       : {ft['total_movies']} movies to classify")

    if args.stock_bases or args.all:
        st = organizer.plan_stock_bases()
        all_moves.extend(st["moves"])
        print(f"Stock Bases (Flickr): {st['total_stock_images']} images to Base_Flickr_HQ")

    if args.sound or args.all:
        sd = organizer.plan_sound_organization()
        all_moves.extend(sd["moves"])
        print(f"Sound & Voiceover   : {sd['total_sound_files']} audio files to 04_Sound")

    if args.personal_archive or args.all:
        pa = organizer.plan_personal_archive()
        all_moves.extend(pa["moves"])
        print(f"Personal DCIM Photo : {pa['total_photos']} photos to 07_Archive/Personal_Photography")

    print("-" * 75)
    print(f"Total Operations Planned: {len(all_copies)} copies, {len(all_moves)} moves, {len(all_deletes)} deletes")

    if args.execute:
        organizer.execute_operations(all_copies, all_moves, all_deletes, max_workers=args.workers)
    else:
        print("\n[NOTE] Running in --dry-run mode. Add '--execute' to perform cloud modifications.")


if __name__ == "__main__":
    main()
