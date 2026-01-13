"""
Structured telemetry logging.
"""

import logging
import json
from datetime import datetime
from app.config import Settings
from app.models import TelemetryEvent


class TelemetryLogger:
    """Logs telemetry events."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger("insightbridge")
    
    async def emit(self, event: TelemetryEvent):
        """Emit telemetry event."""
        try:
            if self.settings.telemetry_emit_enabled:
                event_dict = event.dict()
                self.logger.info(json.dumps(event_dict))
        except Exception as e:
            self.logger.error(f"Failed to emit telemetry: {e}")