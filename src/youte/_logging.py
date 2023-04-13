from __future__ import annotations

import logging

from click import style

DEFAULT_FORMATS = {
    logging.DEBUG: style("DEBUG", fg="cyan") + " | " + style("%(message)s", fg="cyan"),
    logging.INFO: style("INFO") + " | " + style("%(message)s"),
    logging.WARNING: style("WARN ", fg="yellow")
    + " | "
    + style("%(message)s", fg="yellow"),
    logging.ERROR: style("ERROR", fg="red") + " | " + style("%(message)s", fg="red"),
    logging.CRITICAL: style("FATAL", fg="white", bg="red", bold=True)
    + " | "
    + style("%(message)s", fg="red", bold=True),
}


class MultiFormatter(logging.Formatter):
    """Format log messages differently for each log level"""

    def __init__(self, formats: dict[int, str] | None = None, **kwargs):
        base_format = kwargs.pop("fmt", None)
        super().__init__(base_format, **kwargs)

        formats = formats if formats else DEFAULT_FORMATS

        self.formatters = {
            level: logging.Formatter(fmt, **kwargs) for level, fmt in formats.items()
        }

    def format(self, record: logging.LogRecord) -> str:
        formatter = self.formatters.get(record.levelno)

        if formatter is None:
            return super().format(record)

        return formatter.format(record)
