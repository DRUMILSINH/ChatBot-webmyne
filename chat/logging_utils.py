import json
import logging
from datetime import datetime, timezone
from typing import Any


class JsonLogFormatter(logging.Formatter):
    """
    Minimal JSON formatter for structured logs that works with stdlib logging only.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
        }

        message = record.getMessage()
        try:
            parsed = json.loads(message)
            if isinstance(parsed, dict):
                payload.update(parsed)
            else:
                payload["message"] = parsed
        except (json.JSONDecodeError, TypeError):
            payload["message"] = message

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)
