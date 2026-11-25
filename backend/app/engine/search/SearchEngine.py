from __future__ import annotations

import math
import re
from typing import Any

from app.models.search.SearchModels import SearchHit

# Keep underscores intact so physics identifiers like "ee_ZH" stay atomic tokens
TOKEN_SPLIT_RE = re.compile(r"[^a-zA-Z0-9_]+")

# Relative weights for physics metadata similarity scoring
SIMILARITY_WEIGHTS: dict[str, float] = {
    "process": 0.35,
    "ecm": 0.25,
    "generator": 0.15,
    "campaign": 0.15,
    "detector": 0.10,
}


class SearchEngine:
    """Pure, stateless scoring and ranking engine for fulltext, similarity, and suggestions."""

    @staticmethod
    def flattenScalars(
        obj: Any, prefix: str = ""
    ) -> list[tuple[str, Any]]:
        """Flatten nested JSON metadata into (dot_path, scalar_value) pairs."""
        items: list[tuple[str, Any]] = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                path = f"{prefix}.{k}" if prefix else str(k)
                items.extend(SearchEngine.flattenScalars(v, path))
        elif isinstance(obj, list):
            for idx, v in enumerate(obj):
                path = f"{prefix}[{idx}]" if prefix else f"[{idx}]"
                items.extend(SearchEngine.flattenScalars(v, path))
        elif obj is not None:
            items.append((prefix, obj))
        return items

    @classmethod
    def tokenize(cls, text: str) -> set[str]:
        return {tok for tok in TOKEN_SPLIT_RE.split(text.lower()) if tok}

    @classmethod
    def rankFulltext(
        cls,
        query: str,
        rows: list[dict[str, Any]],
        *,
        limit: int = 25,
    ) -> list[SearchHit]:
        """Score and rank candidate rows against query tokens + optional DB similarity."""
        q_lower = query.strip().lower()
        q_tokens = cls.tokenize(q_lower)
        hits: list[SearchHit] = []

        for row in rows:
            metadata = row.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}
            matched_fields: list[str] = []
            token_score = 0.0

            for path, value in cls.flattenScalars(metadata):
                val_str = str(value).lower()
                if q_lower and q_lower in val_str:
                    matched_fields.append(path)
                    token_score += 1.0
                elif q_tokens:
                    overlap = q_tokens & cls.tokenize(val_str)
                    if overlap:
                        matched_fields.append(path)
                        token_score += len(overlap) / len(q_tokens)

            db_sim = float(row.get("db_score", 0.0) or 0.0)
            score = round(max(token_score, db_sim), 4)
            if score <= 0.0 and not matched_fields:
                continue

            hits.append(
                SearchHit(
                    id=str(row["id"]),
                    entryType=str(row.get("entry_type", "")),
                    score=score,
                    matchedFields=sorted(set(matched_fields)),
                    metadata=metadata,
                )
            )

        hits.sort(key=lambda h: (-h.score, h.id))
        return hits[:limit]

    @classmethod
    def rankSimilar(
        cls,
        target: dict[str, Any],
        candidates: list[dict[str, Any]],
        *,
        limit: int = 10,
    ) -> list[SearchHit]:
        """Rank candidate entries by structural/numeric proximity to target metadata."""
        target_id = str(target.get("id", ""))
        target_meta = target.get("metadata") or {}
        target_flat = dict(cls.flattenScalars(target_meta))
        hits: list[SearchHit] = []

        for row in candidates:
            cid = str(row.get("id", ""))
            if cid == target_id:
                continue
            cand_meta = row.get("metadata") or {}
            cand_flat = dict(cls.flattenScalars(cand_meta))

            score = 0.0
            matched: list[str] = []

            for key, weight in SIMILARITY_WEIGHTS.items():
                t_val = target_flat.get(key)
                c_val = cand_flat.get(key)
                if t_val is None or c_val is None:
                    continue
                if isinstance(t_val, (int, float)) and isinstance(c_val, (int, float)):
                    denom = max(abs(float(t_val)), abs(float(c_val)), 1e-9)
                    prox = max(0.0, 1.0 - abs(float(t_val) - float(c_val)) / denom)
                    if math.isfinite(prox) and prox > 0.0:
                        score += weight * prox
                        matched.append(key)
                elif str(t_val).lower() == str(c_val).lower():
                    score += weight
                    matched.append(key)

            t_pairs = {(k, str(v).lower()) for k, v in target_flat.items()}
            c_pairs = {(k, str(v).lower()) for k, v in cand_flat.items()}
            union = t_pairs | c_pairs
            if union:
                jaccard = len(t_pairs & c_pairs) / len(union)
                score += 0.25 * jaccard
                for k, _ in t_pairs & c_pairs:
                    matched.append(k)

            if score <= 0.0:
                continue

            hits.append(
                SearchHit(
                    id=cid,
                    entryType=str(row.get("entry_type", "")),
                    score=round(min(score, 1.0), 4),
                    matchedFields=sorted(set(matched)),
                    metadata=cand_meta if isinstance(cand_meta, dict) else {},
                )
            )

        hits.sort(key=lambda h: (-h.score, h.id))
        return hits[:limit]

    @staticmethod
    def rankSuggestions(
        prefix: str,
        values: list[str],
        *,
        limit: int = 15,
    ) -> list[str]:
        """Filter and rank autocomplete suggestions: prefix matches first, then substring matches."""
        p = prefix.strip().lower()
        unique = list(dict.fromkeys(v for v in values if isinstance(v, str) and v))
        if not p:
            return sorted(unique)[:limit]

        prefix_matches = sorted([v for v in unique if v.lower().startswith(p)])
        contains_matches = sorted(
            [v for v in unique if p in v.lower() and not v.lower().startswith(p)]
        )
        return (prefix_matches + contains_matches)[:limit]
