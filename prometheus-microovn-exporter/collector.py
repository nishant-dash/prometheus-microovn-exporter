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
        if self.mode == "microovn":
            self.ovs_appctl = "microovn.ovs-appctl"
        else:
            self.ovs_appctl = "ovs-appctl"
        self.cluster_name = {
            "nb": "OVN_Northbound",
            "sb": "OVN_Southbound",
        }

    def refresh_cache(self, gauge_name: str, gauge_desc: str, labels: List[str]) -> None:
        """Refresh instances for each collection job.

        :param str gauge_name: the name of the gauge
        :param str gauge_desc: the description of the gauge
        :param List[str] labels: the label set of the gauge
        """
        self.data = {
            gauge_name: {
                "gauge_desc": gauge_desc,
                "labels": labels,
                "labelvalues_update": [],
            }
        }

    def collect(self) -> Dict[str, Any]:
        """Get stats from current host"""
        gauge_name = "ovn_state"
        gauge_desc = "State of ovn ports certs cluster"
        labels = [
            "job",
            "hostname",
        ]

        return self.data


if __name__ == "__main__":
    collector = Collector()
    print("RET", collector.collect())