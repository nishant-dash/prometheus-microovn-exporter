"""Collector module."""
from logging import getLogger
from typing import Any, Dict, List
from prometheus_client.core import GaugeMetricFamily

from prometheus_microovn_exporter.config import Config
from prometheus_microovn_exporter.ovn_scraper import OvnScraper

class Collector:
    """Core class of the PrometheusMicroovnExporter collector."""

    def __init__(self) -> None:
        """Create new collector and configure runtime environment."""
        self.config = Config().get_config()
        self.logger = getLogger(__name__)
        self.data: Dict[str, Any] = {}
        self.mode = self.config["mode"].get(str)
        self.logger.debug("Collector initialized")
        self.ovn_scraper = OvnScraper()

    def create_gauge(self, element) -> GaugeMetricFamily():
        gauge_name = f"ovn_{element}_state"
        gauge_desc = f"State of ovn {element}"
        labels = [
            "job",
            "hostname",
        ]
        gauge = GaugeMetricFamily(gauge_name, gauge_desc, labels=labels)
        return gauge

    def collect(self) -> Any:
        """Get stats from current host"""
        data = self.ovn_scraper.get_stats()
        # gauges = {i: self.create_gauge(i) for i in data.keys()}
        gauge = self.create_gauge("cluster")
        for elem, info in data.items():
            for k,v in info.items():
                g.add_metric([k], v)
        yield gauge


if __name__ == "__main__":
    from prometheus_client.core import REGISTRY
    from prometheus_client import start_http_server
    import time
    collector = Collector()
    start_http_server(9999)
    REGISTRY.register(Collector())
    while True:
        time.sleep(10)