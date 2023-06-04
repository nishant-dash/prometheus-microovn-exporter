"""Exporter module."""
from time import sleep
import sys
from logging import getLogger
from typing import Any, Dict

from prometheus_client import CollectorRegistry, Gauge, start_http_server, REGISTRY

from prometheus_microovn_exporter.collector import Collector
from prometheus_microovn_exporter.config import Config


class ExporterDaemon:
    """Core class of the exporter daemon."""

    def __init__(self) -> None:
        """Create new daemon and configure runtime environment."""
        self.config = Config().get_config()
        self.logger = getLogger(__name__)
        self.logger.info(f"Parsed config: {self.config.config_dir()}")
        self.collector = Collector()
        self.logger.debug("Exporter initialized")

    def collect(self) -> None:
        """Call Collector"""
        REGISTRY.register(self.collector)
        while True:
            try:
                self.logger.info("Collecting gauges...")
                sleep(self.config["exporter"]["collect_interval"].get(int) * 60)
            except Exception as exception:  # pylint: disable=W0703
                self.logger.error(f"Collection job resulted in error: {exception}")
                sys.exit(1)

    def run(self) -> None:
        """Run exporter"""
        self.logger.debug("Running prometheus client http server.")
        start_http_server(self.config["exporter"]["port"].get(int))
        try:
            self.collect()
        except KeyboardInterrupt as exception:
            # Gracefully handle keyboard interrupt
            self.logger.info(f"{exception}: Exiting...")
            sys.exit(0)


if __name__ == "__main__":
    obj = ExporterDaemon()
    obj.run()