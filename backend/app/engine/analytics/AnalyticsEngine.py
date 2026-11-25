from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any

from app.models.analytics.AnalyticsModels import (
    CompareResponse,
    CoverageCell,
    CoverageResponse,
    GroupedSummary,
    HistogramBin,
    HistogramResponse,
    MetricDelta,
    SummaryResponse,
)


class AnalyticsEngine:
    """Pure, stateless numerical analytics engine over extracted metadata rows."""

    @staticmethod
    def extractPath(metadata: dict[str, Any], path: list[str]) -> Any:
        """Traverse nested metadata by path segments; return None if absent."""
        cursor: Any = metadata
        for seg in path:
            if isinstance(cursor, dict) and seg in cursor:
                cursor = cursor[seg]
            else:
                return None
        return cursor

    @staticmethod
    def toFiniteFloat(value: Any) -> float | None:
        if isinstance(value, bool) or value is None:
            return None
        try:
            num = float(value)
        except (TypeError, ValueError):
            return None
        return num if math.isfinite(num) else None

    @classmethod
    def computeHistogram(
        cls,
        rows: list[dict[str, Any]],
        path: list[str],
        bins: int = 10,
    ) -> HistogramResponse:
        """Bin finite numeric values at `path` into `bins` uniform-width intervals."""
        values: list[float] = []
        for row in rows:
            meta = row.get("metadata") or {}
            if isinstance(meta, dict):
                num = cls.toFiniteFloat(cls.extractPath(meta, path))
                if num is not None:
                    values.append(num)

        if not values:
            return HistogramResponse(
                path=path, bins=[], totalValues=0, min=None, max=None
            )

        lo = min(values)
        hi = max(values)

        if lo == hi:
            return HistogramResponse(
                path=path,
                bins=[HistogramBin(lower=lo, upper=hi, count=len(values))],
                totalValues=len(values),
                min=lo,
                max=hi,
            )

        width = (hi - lo) / bins
        counts = [0] * bins
        for v in values:
            idx = int((v - lo) / width)
            if idx >= bins:
                idx = bins - 1
            counts[idx] += 1

        hist_bins = [
            HistogramBin(
                lower=round(lo + i * width, 10),
                upper=round(lo + (i + 1) * width, 10),
                count=counts[i],
            )
            for i in range(bins)
        ]
        return HistogramResponse(
            path=path,
            bins=hist_bins,
            totalValues=len(values),
            min=lo,
            max=hi,
        )

    @classmethod
    def computeSummary(
        cls,
        rows: list[dict[str, Any]],
        groupPath: list[str],
        metricPath: list[str] | None = None,
    ) -> SummaryResponse:
        """Group rows by `groupPath` and optionally compute count/sum/mean/min/max on `metricPath`."""
        grouped_counts: Counter[Any] = Counter()
        grouped_metrics: dict[Any, list[float]] = defaultdict(list)

        for row in rows:
            meta = row.get("metadata") or {}
            if not isinstance(meta, dict):
                continue
            key = cls.extractPath(meta, groupPath)
            if isinstance(key, (dict, list)):
                key = str(key)
            grouped_counts[key] += 1
            if metricPath is not None:
                num = cls.toFiniteFloat(cls.extractPath(meta, metricPath))
                if num is not None:
                    grouped_metrics[key].append(num)

        groups: list[GroupedSummary] = []
        for key, cnt in sorted(
            grouped_counts.items(),
            key=lambda kv: (-kv[1], "" if kv[0] is None else str(kv[0])),
        ):
            vals = grouped_metrics.get(key, [])
            if metricPath is not None and vals:
                total = math.fsum(vals)
                groups.append(
                    GroupedSummary(
                        group=key,
                        count=cnt,
                        sum=round(total, 10),
                        mean=round(total / len(vals), 10),
                        min=min(vals),
                        max=max(vals),
                    )
                )
            else:
                groups.append(GroupedSummary(group=key, count=cnt))

        return SummaryResponse(
            groupBy=groupPath,
            metric=metricPath,
            groups=groups,
            totalEntries=len(rows),
        )

    @classmethod
    def computeCompare(
        cls,
        rowsA: list[dict[str, Any]],
        rowsB: list[dict[str, Any]],
        metricPaths: list[list[str]],
    ) -> CompareResponse:
        """Compute per-metric mean, absolute delta (B - A), and ratio (B / A)."""
        deltas: list[MetricDelta] = []
        for path in metricPaths:
            valsA = [
                n
                for r in rowsA
                if isinstance(r.get("metadata"), dict)
                and (n := cls.toFiniteFloat(cls.extractPath(r["metadata"], path))) is not None
            ]
            valsB = [
                n
                for r in rowsB
                if isinstance(r.get("metadata"), dict)
                and (n := cls.toFiniteFloat(cls.extractPath(r["metadata"], path))) is not None
            ]
            meanA = round(math.fsum(valsA) / len(valsA), 10) if valsA else None
            meanB = round(math.fsum(valsB) / len(valsB), 10) if valsB else None
            delta = (
                round(meanB - meanA, 10)
                if meanA is not None and meanB is not None
                else None
            )
            ratio = (
                round(meanB / meanA, 10)
                if meanA is not None and meanB is not None and meanA != 0.0
                else None
            )
            deltas.append(
                MetricDelta(
                    path=path,
                    meanA=meanA,
                    meanB=meanB,
                    delta=delta,
                    ratio=ratio,
                )
            )
        return CompareResponse(
            countA=len(rowsA),
            countB=len(rowsB),
            deltas=deltas,
        )

    @classmethod
    def computeCoverage(
        cls,
        rows: list[dict[str, Any]],
        rowPath: list[str],
        colPath: list[str],
    ) -> CoverageResponse:
        """Build a 2D phase-space coverage matrix counting (rowField, colField) pairs."""
        counts: Counter[tuple[Any, Any]] = Counter()
        for row in rows:
            meta = row.get("metadata") or {}
            if not isinstance(meta, dict):
                continue
            r_val = cls.extractPath(meta, rowPath)
            c_val = cls.extractPath(meta, colPath)
            if r_val is None or c_val is None:
                continue
            if isinstance(r_val, (dict, list)):
                r_val = str(r_val)
            if isinstance(c_val, (dict, list)):
                c_val = str(c_val)
            counts[(r_val, c_val)] += 1

        cells = [
            CoverageCell(row=r, col=c, count=cnt)
            for (r, c), cnt in sorted(
                counts.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))
            )
        ]
        return CoverageResponse(
            rowField=rowPath,
            colField=colPath,
            cells=cells,
            totalEntries=len(rows),
        )
