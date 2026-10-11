"""Robots.txt parser and snapshot manager."""

import hashlib
from typing import Dict, Optional
import urllib.robotparser
from sqlalchemy.orm import Session

from service.db.models import RobotsSnapshot


class RobotsManager:
    def __init__(self):
        self._parsers: Dict[str, urllib.robotparser.RobotFileParser] = {}

    def parse_and_store(self, host: str, content_text: str, db: Optional[Session] = None) -> RobotsSnapshot:
        content_sha256 = hashlib.sha256(content_text.encode("utf-8")).hexdigest()
        
        parser = urllib.robotparser.RobotFileParser()
        parser.parse(content_text.splitlines())
        self._parsers[host] = parser

        snapshot = RobotsSnapshot(
            host=host,
            content_sha256=content_sha256,
            content_text=content_text
        )

        if db:
            existing = db.query(RobotsSnapshot).filter_by(host=host, content_sha256=content_sha256).first()
            if not existing:
                db.add(snapshot)
                db.commit()

        return snapshot

    def is_allowed(self, host: str, url: str, user_agent: str = "*") -> bool:
        parser = self._parsers.get(host)
        if not parser:
            return True  # If no robots.txt was found/parsed, default allow
        return parser.can_fetch(user_agent, url)
