"""Collector module."""
import re
from enum import Enum
from logging import getLogger
from typing import Any, Dict, List

from prometheus_microovn_exporter.config import Config


class Collector:
    """Core class of the PrometheusMicroovnExporter collector."""

    def __init__(self) -> None:
        """Create new collector and configure runtime environment."""
        self.config = Config().get_config()
        self.logger = getLogger(__name__)
        self.data: Dict[str, Any] = {}
        self.logger.debug("Collector initialized")