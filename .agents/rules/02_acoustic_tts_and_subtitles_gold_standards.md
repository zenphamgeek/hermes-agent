# Master Pillar 2: Acoustic TTS V0-Sense & Gold SRT Karaoke Standards

> **Authority**: Kỹ Sư Trưởng Âm Thanh & ASR Khép Kín (Chief Acoustic & ASR QA Engineer).  
> **Target**: All Voiceover, Audio Mastering, and Subtitle Generation across Content Factory.

---

## 1. TTS V0-Sense: The Sovereign Gold Audio Standard

All voiceover generation across all Content Factory channels and videos MUST strictly adhere to the **TTS V0-Sense standard** (`assets/scripts_video/tts_v0_sense_synthesizer.py`). Intermediate text manipulation, prosody dictionaries (`prosody_dictionary.json`), 24 Wave matrices, compound locks, and phonetic preprocessors remain **COMPLETELY ABANDONED**.

TTS V0-Sense consists of 5 strict pillars and 1 foundational invariant:

### Invariant 0: Zero-Atempo-Slowdown & Native 1.0x Neural Cadence Mandate
- **Absolute Ban on atempo < 1.0**: Under NO circumstances may any script, FFmpeg filter, or DSP chain apply `atempo < 1.0` (such as `atempo=0.73`, `atempo=0.85`, `atempo=0.94`). Neural inference runs at 100% native 1.0x speed.
- **Shorts Duration Decoupling**: For 50.00s YouTube Shorts, speech must NEVER be artificially stretched to fill 48.8s. Narration naturally finishes between 36s and 42s; the remaining window through 50.0s is carried by ambient background pad, SFX, and visual conversion CTA to the Related Video.
- **Zero Mechanical Zero-Padding**: Forbid inserting synthetic silent arrays (`np.zeros(...)`) between fine-grained clauses. Inter-clause pacing derives purely from VieNeu punctuation cadence and Smart Silence Gate.

### Pillar 1: Sense-Processing & Dynamic Temper
- **English Tech Terms**: Wraps English technical terms in `<en>...</en>` tags (e.g. `<en>Stochastic Gradient Descent</en>`, `<en>Learning Rate</en>`).
- **Punctuation & Modulations**: Replaces ellipsis `...` with comma `, ` to generate clear, crisp pauses. Adds subtle `[cười]` cues at cognitive paradox beats.
- **Dynamic Scene Temper**:
  - Hook / Cold Open: `0.58 – 0.60` (alert, captivating)
  - Math / Technical Deep-Dive: `0.52 – 0.54` (deliberate, crystal clear)
  - Outro / Philosophical CTA: `0.52` (calm, contemplative)

### Pillar 2: Acoustic Clause Guard (Max 75 Chars per Unit)
- **Hard Invariant**: VieNeu-TTS v3 Turbo MUST NEVER receive an unsegmented text block exceeding 80 characters.
- **Micro-Segmentation**: All sentences must be split at punctuation boundaries (`, `, `; `, `.`, `!`, `?`) into fine-grained units of $\le 75$ characters.
- **Micro-Pause Insertion**:
  - Sub-clause pause: $120$ ms
  - Sentence boundary pause: $220$ ms
  - Paragraph boundary pause: $350$ ms

### Pillar 3: Closed-Loop ASR Verification (Whisper on CUDA/CPU)
- **Verification Loop**: Every synthesized unit is transcribed by Faster-Whisper.
- **Repetition Check**: Checks for 2-gram to 6-gram stuttering and phrase loops (`check_repetition`).
- **Word Coverage**: Requires $\ge 75\%$ keyword match with canonical script. If repetition occurs or coverage drops, automatically retries with adjusted temperature ($+0.015$) and repetition penalty ($+0.04$).

### Pillar 4: Smart Silence Gate (Zero Acoustic EOS Holes)
- Frame-by-frame 20ms RMS scan (`threshold_rms = 0.0008`, `safety_pad = 40ms`).
- Compresses dead silence gaps $> 0.35$s down to $0.20 – 0.25$s, eliminating acoustic EOS-delay holes while preserving 100% natural breath cadence.

### Pillar 5: 5-Stage Studio Vocal Mastering Chain
Every audio stream must pass through the studio mastering filter graph:
1. **Highpass Filter**: $75 – 80$ Hz (eliminates sub-bass rumble)
2. **De-Mud Parametric EQ**: $300$ Hz, $Q=1.2$, $-1.5$ dB (cleans boxy chest resonance)
3. **Presence Parametric EQ**: $3.4 – 3.8$ kHz, $Q=1.0$, $+1.8$ dB (enhances vocal articulation)
4. **Air Treble Shelf**: $8.5 – 9.0$ kHz, $+2.0$ dB (adds modern studio sheen)
5. **EBU R128 Integrated Loudnorm**: Integrated Loudness **$-14.5 \pm 0.5$ LUFS**, True Peak **$\le -1.5$ dBTP**, LRA $\le 7.0$ LU, $48$ kHz Stereo.

---

## 2. Gold SRT Karaoke Standard (Subtitles)

All subtitle generation (`.srt`) across Masterclass 16:9 and Shorts 9:16 MUST strictly adhere to the **Gold SRT Karaoke standard** (`assets/scripts_video/gold_srt_karaoke_aligner.py`). Full paragraph or long sentence dumps (10–15s static blocks) are **COMPLETELY FORBIDDEN**.

Every subtitle cue must adhere to 5 strict invariants:
1. **A Few Words Only**: Exactly 3 to 5 words per cue (hard limit 2–6 words).
2. **60% Screen Width Constraint**: Max 34 characters per line (hard limit 35 chars) occupying only the center 60% horizontal viewport, single line only.
3. **Dynamic Karaoke Pacing**: Duration $0.8$s to $2.2$s per cue (hard max 2.5s), pacing in lockstep with spoken speech.
4. **Zero Broken Compounds**: Compound terms and scientific names (e.g. *ngẫu nhiên*, *xác suất*, *điểm yên ngựa*, *Stochastic Gradient Descent*, *Quỷ Laplace*) must NEVER be split across cue boundaries.
5. **Canonical Script Fidelity**: 100% of subtitle text must derive from the canonical author script (0 ASR phonetic typos), with word-level timestamps extracted via Faster-Whisper on CUDA/CPU.
