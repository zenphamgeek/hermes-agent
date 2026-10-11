"""
Quality helpers for Video Face Segmenter.
Pure functions (numpy + stdlib only) — testable without insightface/cv2.
"""

from typing import List, Tuple, Set
import numpy as np


def greedy_cluster_identity(embeddings: List[np.ndarray], min_sim: float = 0.30) -> Tuple[Set[int], List[float]]:
    """
    Single-pass greedy clustering of L2-normalized face embeddings.

    Returns (primary_mask, id_sim_list):
      primary_mask  — set of embedding indices belonging to the largest cluster.
      id_sim_list   — cosine similarity of each embedding to the primary centroid.
    """
    if not embeddings:
        return set(), []

    # centroids: list of running-mean (L2-normalized) embeddings
    centroids = [embeddings[0].copy()]
    members = [{0}]

    for i in range(1, len(embeddings)):
        sims = [float(np.dot(embeddings[i], c)) for c in centroids]
        best = int(np.argmax(sims))
        if sims[best] >= min_sim:
            members[best].add(i)
            # update running mean
            count = len(members[best])
            centroids[best] = (centroids[best] * (count - 1) + embeddings[i]) / count
            # renormalize
            norm = np.linalg.norm(centroids[best])
            if norm > 0:
                centroids[best] = centroids[best] / norm
        else:
            centroids.append(embeddings[i].copy())
            members.append({i})

    primary = int(np.argmax([len(m) for m in members]))
    primary_mask = members[primary]
    id_sim = [float(np.dot(embeddings[i], centroids[primary])) for i in range(len(embeddings))]
    return primary_mask, id_sim


def extract_ok_runs(
    ok_flags: List[bool],
    timestamps: List[float],
    sample_dt: float,
    gap_ok: int = 1,
    min_dur: float = 2.0,
    merge_gap: float = 0.0,
) -> List[Tuple[float, float, float]]:
    """
    Extract contiguous runs of OK frames from sampled metrics.

    ok_flags      — per-sample boolean (is_ok at that timestamp).
    timestamps    — corresponding frame timestamps (seconds).
    sample_dt     — time between consecutive samples (seconds).
    gap_ok        — number of consecutive BAD samples allowed between runs (merged).
    min_dur       — minimum run duration (seconds) to emit.
    merge_gap     — max time (seconds) between two OK samples that still merges the
                    two runs into one segment, bridging brief bad footage (blinks,
                    occlusions, cuts). 0 disables time-based merging.

    Returns list of (start_sec, end_sec, duration_sec).
    end_sec = last_ok_timestamp + sample_dt (covers tail of last frame).
    """
    ok_idxs = [i for i, ok in enumerate(ok_flags) if ok]
    if not ok_idxs:
        return []

    # Build runs
    runs = [[ok_idxs[0]]]
    for i in ok_idxs[1:]:
        prev = runs[-1][-1]
        gap = i - prev - 1  # skipped bad samples between previous ok and this one
        if gap <= gap_ok or (merge_gap > 0 and timestamps[i] - timestamps[prev] <= merge_gap):
            runs[-1].append(i)
        else:
            runs.append([i])

    out = []
    for r in runs:
        if len(r) < 2:
            continue  # single ok frame too short
        start = timestamps[r[0]]
        end = timestamps[r[-1]] + sample_dt
        dur = end - start
        if dur >= min_dur:
            out.append((start, end, round(dur, 3)))

    return out