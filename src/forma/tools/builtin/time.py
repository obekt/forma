"""Get current time tool."""

import time
from datetime import datetime, timezone
from typing import Any

from forma.tools.base import SyncTool, ToolResult


class GetCurrentTimeTool(SyncTool):
    """Get the current date and time.

    Returns current UTC time and optionally local time for a timezone.
    Useful for time-sensitive queries and scheduling.
    """

    name = "get_current_time"
    description = "Get the current date and time. Returns UTC time by default, can optionally return time for a specific timezone. Use this for time-sensitive queries or when you need to know the current time."

    parameters = {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "Optional timezone name (e.g., 'Europe/Berlin', 'America/New_York', 'Asia/Tokyo'). If not provided, returns UTC time.",
            },
            "format": {
                "type": "string",
                "description": "Output format: 'iso' (ISO 8601), 'readable' (human-readable), or 'both' (default: 'both')",
                "default": "both",
                "enum": ["iso", "readable", "both"],
            },
        },
        "required": [],
    }

    timeout = 1.0

    def execute_sync(self, **kwargs: Any) -> ToolResult:
        """Get current time."""
        timezone_name = kwargs.get("timezone")
        format_type = kwargs.get("format", "both")

        start_time = time.time()

        try:
            # Get UTC time
            utc_now = datetime.now(timezone.utc)

            result_data: dict[str, Any] = {}

            # Add UTC time
            if format_type in ("iso", "both"):
                result_data["utc_iso"] = utc_now.isoformat()
            if format_type in ("readable", "both"):
                result_data["utc_readable"] = utc_now.strftime("%Y-%m-%d %H:%M:%S UTC")

            # Add timezone-specific time if requested
            if timezone_name:
                try:
                    import zoneinfo

                    tz = zoneinfo.ZoneInfo(timezone_name)
                    local_now = datetime.now(tz)

                    if format_type in ("iso", "both"):
                        result_data["local_iso"] = local_now.isoformat()
                    if format_type in ("readable", "both"):
                        result_data["local_readable"] = local_now.strftime("%Y-%m-%d %H:%M:%S %Z")
                    result_data["timezone"] = timezone_name
                except Exception as tz_error:
                    result_data["timezone_error"] = (
                        f"Invalid timezone '{timezone_name}': {tz_error}"
                    )

            # Add additional useful info
            result_data["unix_timestamp"] = int(utc_now.timestamp())
            result_data["day_of_week"] = utc_now.strftime("%A")
            result_data["date"] = utc_now.strftime("%Y-%m-%d")

            duration_ms = (time.time() - start_time) * 1000

            return ToolResult(
                success=True,
                output=result_data,
                duration_ms=duration_ms,
                metadata={"timezone_requested": timezone_name},
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                success=False,
                error=f"Failed to get current time: {str(e)}",
                duration_ms=duration_ms,
            )
