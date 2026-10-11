"""Unattended Smart Acquisition Gateway with Multi-Channel Failover (FR-006, FR-011)."""

import time
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse
import httpx
from pydantic import BaseModel
from sqlalchemy.orm import Session

from service.core.policy_engine import PolicyEngine, PolicyDecisionType
from service.acquisition.classifier import ResponseClassifier, ResponseClass
from service.acquisition.retry_engine import AdaptiveRetryEngine
from service.acquisition.circuit_breaker import CircuitBreakerManager
from service.storage.artifact_manager import ArtifactManager, StoredArtifact
from service.db.models import FetchAttempt, ChallengeEvent


class GatewayFetchResult(BaseModel):
    success: bool
    status_code: Optional[int] = None
    response_class: ResponseClass
    artifact: Optional[StoredArtifact] = None
    error_message: Optional[str] = None
    duration_ms: int = 0
    channel_used: str = "http"


class AcquisitionGateway:
    def __init__(
        self,
        policy_engine: PolicyEngine,
        artifact_manager: ArtifactManager,
        retry_engine: Optional[AdaptiveRetryEngine] = None,
        circuit_breaker: Optional[CircuitBreakerManager] = None
    ):
        self.policy_engine = policy_engine
        self.artifact_manager = artifact_manager
        self.retry_engine = retry_engine or AdaptiveRetryEngine()
        self.circuit_breaker = circuit_breaker or CircuitBreakerManager()

    def fetch_url(
        self,
        source_id: str,
        target_url: str,
        content_class: str,
        db: Session,
        channel: str = "http",
        etag: Optional[str] = None,
        last_modified: Optional[str] = None
    ) -> GatewayFetchResult:
        # 1. Pre-fetch Policy Evaluation
        decision = self.policy_engine.evaluate_request(source_id, target_url, content_class, db)
        if not decision.allowed:
            return GatewayFetchResult(
                success=False,
                response_class=ResponseClass.POLICY_DENIED,
                error_message=decision.reason or "Pre-fetch policy denied request"
            )

        parsed = urlparse(target_url)
        host = parsed.netloc.split(":")[0].lower()

        # 2. Check Circuit Breaker
        if not self.circuit_breaker.is_available(host, db):
            return GatewayFetchResult(
                success=False,
                response_class=ResponseClass.TRANSIENT,
                error_message=f"Host {host} is currently in circuit breaker cooldown"
            )

        headers = {
            "User-Agent": "HSEKnowledgeSync/1.0 (+https://nousresearch.com/hse-compliance-bot)",
            "Accept": "text/html,application/xhtml+xml,application/pdf,application/json;q=0.9,*/*;q=0.8"
        }
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        start_time = time.time()
        attempt_count = 0
        max_retries = 3

        while attempt_count <= max_retries:
            attempt_count += 1
            try:
                with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                    resp = client.get(target_url, headers=headers)
                    duration_ms = int((time.time() - start_time) * 1000)

                    resp_class = ResponseClassifier.classify(
                        status_code=resp.status_code,
                        headers=dict(resp.headers),
                        body_text=resp.text if len(resp.content) < 500000 else ""
                    )

                    # Record attempt
                    attempt_rec = FetchAttempt(
                        source_id=source_id,
                        target_url=target_url,
                        channel_used=channel,
                        status_code=resp.status_code,
                        response_class=resp_class.value,
                        duration_ms=duration_ms
                    )
                    db.add(attempt_rec)
                    db.commit()

                    if resp_class == ResponseClass.SUCCESS:
                        self.circuit_breaker.record_success(host, db)
                        mime = resp.headers.get("content-type", "text/html").split(";")[0]
                        artifact = self.artifact_manager.store_artifact(
                            content_bytes=resp.content,
                            source_id=source_id,
                            source_url=target_url,
                            canonical_url=str(resp.url),
                            db=db,
                            declared_mime_type=mime
                        )
                        return GatewayFetchResult(
                            success=True,
                            status_code=resp.status_code,
                            response_class=ResponseClass.SUCCESS,
                            artifact=artifact,
                            duration_ms=duration_ms,
                            channel_used=channel
                        )

                    elif resp_class == ResponseClass.NOT_MODIFIED:
                        self.circuit_breaker.record_success(host, db)
                        return GatewayFetchResult(
                            success=True,
                            status_code=304,
                            response_class=ResponseClass.NOT_MODIFIED,
                            duration_ms=duration_ms
                        )

                    elif resp_class == ResponseClass.INTERACTIVE_CHALLENGE:
                        # Log and quarantine
                        challenge = ChallengeEvent(
                            source_id=source_id,
                            target_url=target_url,
                            challenge_type="CLOUDFLARE_TURNSTILE_OR_CAPTCHA",
                            action_taken="QUARANTINED"
                        )
                        db.add(challenge)
                        self.circuit_breaker.record_failure(host, "INTERACTIVE_CHALLENGE", db)
                        db.commit()
                        return GatewayFetchResult(
                            success=False,
                            status_code=resp.status_code,
                            response_class=ResponseClass.INTERACTIVE_CHALLENGE,
                            error_message="Interactive challenge detected; quarantined without manual solver"
                        )

                    elif resp_class == ResponseClass.RATE_LIMIT or resp_class == ResponseClass.TRANSIENT:
                        if attempt_count <= max_retries:
                            retry_after = self.retry_engine.parse_retry_after(dict(resp.headers))
                            delay = retry_after or self.retry_engine.calculate_backoff(attempt_count)
                            time.sleep(min(delay, 2.0))  # Capped for fast execution
                            continue
                        self.circuit_breaker.record_failure(host, f"STATUS_{resp.status_code}", db)
                        return GatewayFetchResult(
                            success=False,
                            status_code=resp.status_code,
                            response_class=resp_class,
                            error_message=f"HTTP {resp.status_code} after {attempt_count} attempts"
                        )

                    else:
                        return GatewayFetchResult(
                            success=False,
                            status_code=resp.status_code,
                            response_class=resp_class,
                            error_message=f"Request failed with response class {resp_class.value}"
                        )

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                if attempt_count <= max_retries:
                    delay = self.retry_engine.calculate_backoff(attempt_count)
                    time.sleep(min(delay, 1.0))
                    continue
                self.circuit_breaker.record_failure(host, str(e), db)
                return GatewayFetchResult(
                    success=False,
                    response_class=ResponseClass.TRANSIENT,
                    error_message=str(e),
                    duration_ms=duration_ms
                )

        return GatewayFetchResult(
            success=False,
            response_class=ResponseClass.TRANSIENT,
            error_message="Max retries exceeded"
        )
