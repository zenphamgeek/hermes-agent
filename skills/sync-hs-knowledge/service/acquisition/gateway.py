"""Unattended Smart Acquisition Gateway orchestrating polite multi-channel retrieval."""

import time
from typing import Optional, Dict, Any, Tuple
import httpx
from pydantic import BaseModel
from sqlalchemy.orm import Session

from service.db.models import ChallengeEvent, FetchAttempt
from service.core.policy_engine import PolicyEngine, PolicyDecisionType
from service.storage.artifact_manager import ArtifactManager, StoredArtifact
from .classifier import ResponseClass, ResponseClassifier
from .retry_engine import AdaptiveRetryEngine
from .circuit_breaker import CircuitBreakerManager


class AcquisitionResult(BaseModel):
    success: bool
    status_code: Optional[int]
    response_class: ResponseClass
    artifact: Optional[StoredArtifact] = None
    not_modified: bool = False
    error_message: Optional[str] = None
    channel_used: str = "http"
    quarantined: bool = False


class AcquisitionGateway:
    def __init__(
        self,
        policy_engine: PolicyEngine,
        artifact_manager: ArtifactManager,
        client: Optional[httpx.Client] = None
    ):
        self.policy_engine = policy_engine
        self.artifact_manager = artifact_manager
        self.client = client or httpx.Client(timeout=30.0, follow_redirects=True)
        self.retry_engine = AdaptiveRetryEngine()
        self.breaker_manager = CircuitBreakerManager()

    def fetch_url(
        self,
        source_id: str,
        url: str,
        canonical_url: str,
        content_class: str,
        db: Session,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None
    ) -> AcquisitionResult:
        # 1. Pre-fetch policy check
        decision = self.policy_engine.evaluate_request(source_id, url, content_class, db=db)
        if decision.decision in (PolicyDecisionType.DENIED, PolicyDecisionType.DENIED_UNALLOWED_HOST, PolicyDecisionType.DENIED_URL_PATTERN):
            return AcquisitionResult(
                success=False,
                status_code=403,
                response_class=ResponseClass.POLICY_DENIED,
                error_message=decision.reason
            )

        if decision.decision == PolicyDecisionType.LICENSE_REQUIRED:
            return AcquisitionResult(
                success=False,
                status_code=402,
                response_class=ResponseClass.POLICY_DENIED,
                error_message="Source content blocked: Pending entitlement required"
            )

        if decision.decision == PolicyDecisionType.QUARANTINED:
            return AcquisitionResult(
                success=False,
                status_code=503,
                response_class=ResponseClass.TRANSIENT,
                error_message="Source is quarantined by circuit breaker",
                quarantined=True
            )

        # 2. Check circuit breaker allowance
        if not self.breaker_manager.can_attempt(source_id, db):
            return AcquisitionResult(
                success=False,
                status_code=503,
                response_class=ResponseClass.TRANSIENT,
                error_message="Circuit breaker is OPEN",
                quarantined=True
            )

        # 3. Prepare headers
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; HS-Knowledge-Bot/1.1; +https://hermes-agent.org/bot)"
        }
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        attempt_count = 0
        while attempt_count < self.retry_engine.max_retries:
            attempt_count += 1
            start_time = time.time()

            try:
                response = self.client.get(url, headers=headers)
                duration_ms = int((time.time() - start_time) * 1000)
                status_code = response.status_code
                resp_headers = dict(response.headers)
                body_bytes = response.content
                body_text = response.text[:2000]

                # Classify response
                resp_class = ResponseClassifier.classify(status_code, resp_headers, body_text)

                # Record fetch attempt
                attempt_record = FetchAttempt(
                    item_id=source_id,
                    channel="http",
                    status_code=status_code,
                    response_class=resp_class.value,
                    etag=resp_headers.get("etag"),
                    last_modified=resp_headers.get("last-modified"),
                    duration_ms=duration_ms
                )
                db.add(attempt_record)
                db.commit()

                # Handle 304 Not Modified
                if resp_class == ResponseClass.NOT_MODIFIED:
                    self.breaker_manager.record_success(source_id, db)
                    return AcquisitionResult(
                        success=True,
                        status_code=304,
                        response_class=ResponseClass.NOT_MODIFIED,
                        not_modified=True
                    )

                # Handle Interactive Challenge (FR-023)
                if resp_class == ResponseClass.INTERACTIVE_CHALLENGE:
                    challenge_event = ChallengeEvent(
                        source_id=source_id,
                        url=url,
                        challenge_type="CLOUDFLARE_TURNSTILE_OR_MANAGED",
                        redacted_evidence="[REDACTED_CHALLENGE_HTML]",
                        action_taken="QUARANTINED"
                    )
                    db.add(challenge_event)
                    self.breaker_manager.record_failure(source_id, db)
                    db.commit()
                    return AcquisitionResult(
                        success=False,
                        status_code=status_code,
                        response_class=ResponseClass.INTERACTIVE_CHALLENGE,
                        error_message="Interactive challenge detected - quarantined (no-human SLA)",
                        quarantined=True
                    )

                # Handle Success
                if resp_class == ResponseClass.SUCCESS:
                    self.breaker_manager.record_success(source_id, db)
                    mime_type = resp_headers.get("content-type", "application/octet-stream").split(";")[0].strip()

                    artifact = None
                    if decision.can_store_raw:
                        artifact = self.artifact_manager.store_artifact(
                            data=body_bytes,
                            mime_type=mime_type,
                            source_id=source_id,
                            source_url=url,
                            canonical_url=canonical_url,
                            db=db
                        )

                    return AcquisitionResult(
                        success=True,
                        status_code=status_code,
                        response_class=ResponseClass.SUCCESS,
                        artifact=artifact
                    )

                # Transient or Rate Limit error: evaluate retry
                self.breaker_manager.record_failure(source_id, db)
                retry_decision = self.retry_engine.compute_retry(attempt_count, resp_class, resp_headers)
                if not retry_decision.should_retry:
                    return AcquisitionResult(
                        success=False,
                        status_code=status_code,
                        response_class=resp_class,
                        error_message=f"Fetch failed: {retry_decision.reason}"
                    )

                time.sleep(retry_decision.delay_seconds)

            except Exception as e:
                self.breaker_manager.record_failure(source_id, db)
                retry_decision = self.retry_engine.compute_retry(attempt_count, ResponseClass.TRANSIENT, {})
                if not retry_decision.should_retry:
                    return AcquisitionResult(
                        success=False,
                        status_code=500,
                        response_class=ResponseClass.TRANSIENT,
                        error_message=f"Network exception: {str(e)}"
                    )
                time.sleep(retry_decision.delay_seconds)

        return AcquisitionResult(
            success=False,
            status_code=504,
            response_class=ResponseClass.TRANSIENT,
            error_message="Max retries exhausted"
        )
