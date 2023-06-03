"""Collector module."""
import re
from enum import Enum
from logging import getLogger
from typing import Any, Dict, List
import subprocess as sp
import socket as sock
from datetime import datetime
import OpenSSL as openssl

from prometheus_microovn_exporter.config import Config


class Collector:
    """Core class of the PrometheusMicroovnExporter collector."""

    def __init__(self) -> None:
        """Create new collector and configure runtime environment."""
        self.config = Config().get_config()
        self.logger = getLogger(__name__)
        self.data: Dict[str, Any] = {}
        self.logger.debug("Collector initialized")
        if self.config["mode"] == "microovn":
            self.ovs_appctl = "microovn.ovs-appctl"
        else:
            self.ovs_appctl = "ovs-appctl"

    def _parse_cluster_status_output(self) -> Dict [str, Any]:
        return {}

    def get_cluster_status(self) -> Dict[str, Any]:
        # microovn.ovs-appctl -t /var/snap/microovn/common/run/central/ovnnb_db.ctl cluster/status OVN_Northbound
        # microovn.ovs-appctl -t /var/snap/microovn/common/run/central/ovnsb_db.ctl cluster/status OVN_Southbound
        cmd = []
        output_to_parse = {}
        clusters = ["nb", "sb"]
        for cluster in clusters:
            try:
                self.logger.debug(f"Running {cmd}")
                output = sp.run(cmd, stdout=sp.PIPE, stderr=sp.DEVNULL)
                output_to_parse[cluster] = output.stdout
            except Exception as exception:
                self.logger.warning(f"Could not query {cluster} cluster for status")
            continue

        return self._parse_cluster_status_output(output_to_parse)

    def check_ports(self) -> Dict[int, int]:
        '''
        Returns a dictionary of port to state mapping where a state value of
        0 -> port if OPEN,
        1 -> port is CLOSED,
        Other values -> UNKNOWN.
        '''
        ports = {
            6641: "OVN Northbound OVSDB Server",
            6642: "OVN Southbound OVSDB Server",
            6643: "OVN NB RAFT Control Plane",
            6644: "OVN SB RAFT Control Plane",
        }
        port_state = {}
        for p in ports:
            create_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            result = create_socket.connect_ex(("127.0.0.1", p))
            create_socket.close()
            port_state[p] = int(result)
            if port_state[p] == 1:
                self.logger.warning(f"Port {p} for {ports[p]} is NOT open")
            elif port_state[p] == 0:
                self.logger.debug(f"Port {p} for {ports[p]} is OPEN")
            else:
                self.logger.warning(f"Port {p} for {ports[p]} is an an UNKNOWN state")
        return port_state

    def _get_date_time(self, timestamp):
        return datetime.strptime(timestamp, "%Y%m%d%H%M%S%z").date().isoformat()

    def check_certs(self) -> Dict[str, int]:
        '''
        Checks the validity of certs and returns a state value where
        0 -> Valid
        1 -> Invalid
        2 -> Valid, but only for 30 more days
        '''
        cert_validity = {cert: 1 for cert in self.config["microovn_certs"]}
        for cert in self.config["microovn_certs"]:
            cert_data = None
            x509_cert = None
            not_after_timestamp = None
            try:
                with open(cert, 'r') as f:
                    cert_data = f.read()
            except Exception as exception:
                self.logger.error("Could not find {cert}")
                return
            try:
                x509_cert = openssl.crypto.load_certificate(openssl.crypto.FILETYPE_PEM, cert_data)
                self.logger.debug(f"Loaded x509 object of {cert}")
            except Exception as exception:
                self.logger.error("Could not use openssl to load {cert}")
                return
            try:
                not_after_timestamp = x509_cert.get_notAfter().decode("utf-8")
            except Exception as exception:
                self.logger.error("Could not use decode {cert}")
                return
            not_after = self._get_date_time(not_after_timestamp)
            now = self._get_date_time(datetime.now())
            num_days = not_after - now
            num_days = num_days.days
            self.logging.info(f"{cert} valid for {num_days} days, till {not_after}")
            if num_days > 30:
                cert_validity[cert] = 2
            elif num_days > 0 and num_days <= 30:
                cert_validity[cert] = 0
        
        return cert_validity