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
        self.mode = str(self.config["mode"])
        self.logger.debug("Collector initialized")
        if self.mode == "microovn":
            self.ovs_appctl = "microovn.ovs-appctl"
        else:
            self.ovs_appctl = "ovs-appctl"
        self.cluster_name = {
            "nb": "OVN_Northbound",
            "sb": "OVN_Southbound",
        }

    def _parse_cluster_status_output(self, to_parse : Dict [str, Any]) -> Dict [str, Any]:
        if len(to_parse) != 3:
            self.logger.warning(
                "Did not get cluster status output from all 3 units, only got {len(to_parse)}"
            )
        roles = []
        leaders = []
        votes = []
        for unit, cluster_status in to_parse.items():
            continue
        return {}

    def _get_db_ctl(self, cluster: str) -> str:
        return f"ovn{cluster}_db.ctl"

    def get_cluster_status(self) -> Dict[str, Any]:
        output_to_parse = {}
        clusters = ["nb", "sb"]
        for cluster in clusters:
            config_key = f"{self.config['mode']}_cluster"
            path = self.config[config_key]["path"]
            path = f"{path}/{self._get_db_ctl(cluster)}"
            cmd = [self.ovs_appctl, "-t", path, "cluster/Status", self.cluster_name[cluster]]
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
            6641: {"ip": "127.0.0.1", "msg": "OVN Northbound OVSDB Server"},
            6642: {"ip": "127.0.0.1", "msg": "OVN Southbound OVSDB Server"},
            6643: {"ip": None, "msg": "OVN NB RAFT Control Plane"},
            6644: {"ip": None, "msg": "OVN SB RAFT Control Plane"},
        }
        if self.mode == "ovn":
            ports[16642] = {"ip": "127.0.0.1", "msg": "OVN misc port"}
        port_state = {}
        for p in ports:
            create_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            result = create_socket.connect_ex((ports[p]["ip"], p))
            create_socket.close()
            port_state[p] = int(result)
            if port_state[p] == 1:
                self.logger.warning(f"Port {p} for {ports[p]['msg']} is NOT open")
            elif port_state[p] == 0:
                self.logger.debug(f"Port {p} for {ports[p]['msg']} is OPEN")
            else:
                self.logger.warning(f"Port {p} for {ports[p]['msg']} is an an UNKNOWN state")
        return port_state

    def check_certs(self) -> Dict[str, int]:
        '''
        Checks the validity of certs and returns a state value where
        0 -> Valid
        1 -> Invalid
        2 -> Valid, but only for 30 more days
        '''
        config_key = f"{self.config['mode']}_certs"
        cert_validity = {str(cert): 1 for cert in self.config[config_key].values()}
        for cert in self.config[config_key]:
            cert = str(self.config[config_key][cert])
            cert_data = None
            x509_cert = None
            not_after_timestamp = None
            try:
                with open(cert, 'r') as f:
                    cert_data = f.read()
            except Exception as exception:
                # @TODO: Need to find a good way of determining if
                # node is either a central or chassis
                self.logger.warning(f"Could not find {cert}")
                continue
            try:
                x509_cert = openssl.crypto.load_certificate(openssl.crypto.FILETYPE_PEM, cert_data)
                self.logger.debug(f"Loaded x509 object of {cert}")
            except Exception as exception:
                self.logger.error(f"Could not use openssl to load {cert}")
                continue
            try:
                not_after_timestamp = x509_cert.get_notAfter().decode("utf-8")
            except Exception as exception:
                self.logger.error(f"Could not use decode {cert}")
                continue
            not_after = datetime.strptime(not_after_timestamp, "%Y%m%d%H%M%S%z").date()
            now = datetime.now().date()
            num_days = not_after - now
            num_days = num_days.days
            self.logger.info(f"{cert} valid for {num_days} days, till {not_after}")
            if num_days > 30:
                cert_validity[cert] = 2
            elif num_days > 0 and num_days <= 30:
                cert_validity[cert] = 0
        
        return cert_validity

if __name__ == "__main__":
    collector = Collector()
    collector.check_ports()
    collector.check_certs()