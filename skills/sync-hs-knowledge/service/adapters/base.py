"""Source Adapter Protocol specification (FR-010, Section 20.1)."""

from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
from pydantic import BaseModel, Field


class Candidate(BaseModel):
    url: str
    canonical_url: str
    content_class: str
    title: Optional[str] = None
    discovered_at: Optional[str] = None


class DiscoveryPage(BaseModel):
    candidates: List[Candidate] = Field(default_factory=list)
    next_cursor: Optional[str] = None
    has_more: bool = False
    total_estimated: Optional[int] = None


class SourceHealth(BaseModel):
    source_id: str
    is_healthy: bool
    status_code: Optional[int] = None
    latency_ms: int = 0
    error_message: Optional[str] = None


class SourceAdapter:
    source_id: str = "BASE_SOURCE"
    name: str = "Base Source Adapter"
    jurisdiction: str = "VN"

    def canonicalize_url(self, raw_url: str) -> str:
        """Strips tracking query parameters (utm_*, fbclid, etc.) and normalizes path."""
        parsed = urlparse(raw_url.strip())
        qs = parse_qs(parsed.query)
        cleaned_qs = {k: v for k, v in qs.items() if not k.startswith("utm_") and k not in ("fbclid", "gclid")}
        query_string = urlencode(cleaned_qs, doseq=True)
        path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
        return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.params, query_string, ""))

    def healthcheck(self) -> SourceHealth:
        return SourceHealth(source_id=self.source_id, is_healthy=True, latency_ms=10)

    def discover(self, cursor: Optional[str] = None, limit: int = 50, taxonomy: Optional[str] = None) -> DiscoveryPage:
        raise NotImplementedError
