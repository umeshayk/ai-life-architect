from __future__ import annotations

from app.models.system_record import SystemRecord


class SeedService:
    """Controlled hook for future dev/demo data bootstrapping."""

    @staticmethod
    def baseline_records() -> list[SystemRecord]:
        return [
            SystemRecord(
                key="foundation.version",
                value="0.1.0",
                metadata_json={"source": "bootstrap", "scope": "system"},
            )
        ]
