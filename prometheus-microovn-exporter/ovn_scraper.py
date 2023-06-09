"""Collector module."""
from logging import getLogger
from typing import Any, Dict
import subprocess as sp
import socket as sock
from datetime import datetime
import OpenSSL as openssl

from prometheus_microovn_exporter.config import Config


class OvnScraper:
    """Core class of the PrometheusMicroovnExporter collector's data source."""

    def __init__(self) -> None:
        """Read configs and initialize scrape."""
        self.config = Config().get_config()
        self.logger = getLogger(__name__)
        self.mode = self.config["mode"].get(str)
        self.logger.debug("Ovn Scraper initialized")
        if self.mode == "microovn":
            self.ovs_appctl = "microovn.ovs-appctl"
        else:
            self.ovs_appctl = "ovs-appctl"
        self.cluster_name = {
            "nb": "OVN_Northbound",
            "sb": "OVN_Southbound",
        }

    def _condense_cluser_status(self, cluster_status_dict: Dict [str, Dict]) -> Dict [str, int]:
        '''
        Status of
        0: good
        1: bad
        '''
        condensed_dict = {}
        for cluster, cluster_info in cluster_status_dict.items():
            status = 0
            if cluster_info["vote"].lower() == "unknown":
                status = 1
            if cluster_info["role"].lower() not in ["leader", "follower"]:
                status = 1
            if cluster_info["status"].lower() != "cluster member":
                status = 1 
            condensed_dict[cluster] = status
        self.logger.debug(f"Condensed cluster status dict to {condensed_dict}")
        return condensed_dict

    def _parse_cluster_status_output(self, to_parse : Dict [str, Any]) -> Dict [str, Any]:
        """Read a ovn central's cluster/status ouput and extract information.
        
        :param Dict [str, Any] to_parse: dict of nb/sb cluster to it's cluster status
            output in plaintext
        """
        final_dict = {}
        to_consider = ["role" ,"leader" ,"vote", "address", "status"]
        for unit, cluster_status in to_parse.items():
            status_dict = {}
            for row in cluster_status.split('\n'):
                key = row.split(':')[0].lower()
                value = row.split(':')[-1]
                if key in to_consider:
                    if key == "address":
                        status_dict[key] = ':'.join(row.split(':')[2:])
                    else:
                        status_dict[key] = value.lstrip(' ')
            final_dict[unit] = status_dict
        self.logger.debug(f"From cluster status, parsed {final_dict}")
        return final_dict

    @staticmethod
    def _get_db_ctl(cluster: str) -> str:
        """Static function that renders nb/sb database ctl file name.
        
        :param str cluster: cluster name, either nb or sb
        """
        return f"ovn{cluster}_db.ctl"

    def check_cluster_status(self) -> Dict[str, Any]:
        """
        Queries the nb and sb cluster of the unit for its cluster status.
        Returns a dictionary mapping the cluster (nb/sb) to a dict of values
        representating the state of the cluster in various aspects.
        """
        output_to_parse = {}
        clusters = ["nb", "sb"]
        for cluster in clusters:
            config_key = f"{self.config['mode']}_cluster"
            path = self.config[config_key]["path"]
            path = f"{path}/{self._get_db_ctl(cluster)}"
            # @TODO: Add timeout when checking cluster status
            cmd = [self.ovs_appctl, "-t", path, "cluster/status", self.cluster_name[cluster]]
            try:
                self.logger.debug(f"Running {cmd}")
                output = sp.run(cmd, stdout=sp.PIPE, stderr=sp.DEVNULL)
                output_to_parse[cluster] = output.stdout.decode('utf-8')
            except Exception as exception:
                self.logger.warning(f"Could not query {cluster} cluster for status")
            continue
        return self._parse_cluster_status_output(output_to_parse)
    
    def get_cluster_status(self) -> Dict[str, Any]:
        cluster_status_dict = self.check_cluster_status()
        return self._condense_cluser_status(cluster_status_dict)

    # def _get_local_ip(self) -> str:
    #     '''
    #     Parses local ip either from
    #     env file, if using microovn
    #     cluster status, if using ovn
    #     '''
    #     ip = None
    #     if self.mode == "microovn":
    #         try:
    #             env_file = self.config["microovn_env"]
    #             with open(env_file, 'r') as f:
    #                 env_data = f.read()
    #         except Exception as exception:
    #             self.logger.warning(f"Could not read {env_file}")
    #             return None
    #         env_data = env_data.split('\n')
    #         for row in env_data:
    #             if row.split('=')[0].lower() == "ovn_local_ip":
    #                 ip = row.split('=')[1]
    #     elif self.mode == "ovn":
    #         cluster_info = self.check_cluster_status()
    #         ip = cluster_info['nb']["address"].split(':')[0]
    #     return ip
    def _get_local_ip(self) -> str:
        '''
        Parses local ip from cluster status output
        @TODO: microovn provides a env file, should try to get something similar
            from ovn
        '''
        ip = None
        cluster_info = self.check_cluster_status()
        if 'nb' in cluster_info:
            ip = cluster_info['nb']["address"].split(':')[0]
        else:
            self.logger.debug(cluster_info)
        return ip

    def get_ports(self) -> Dict[int, int]:
        '''
        Returns a dictionary of port to state mapping where a state value of
        0: port if OPEN
        1: port is CLOSED
        Other values: UNKNOWN
        '''
        port_state = {}
        local_ip = self._get_local_ip()
        if not local_ip:
            self.logger.warning("Could not get cluster status for local ip")
            return
        ports = {
            6641: {"ip": "127.0.0.1", "msg": "OVN Northbound OVSDB Server"},
            6642: {"ip": "127.0.0.1", "msg": "OVN Southbound OVSDB Server"},
            6643: {"ip": local_ip, "msg": "OVN NB RAFT Control Plane"},
            6644: {"ip": local_ip, "msg": "OVN SB RAFT Control Plane"},
        }
        if self.mode == "ovn":
            ports[16642] = {"ip": "127.0.0.1", "msg": "OVN misc port"}
        for p in ports:
            create_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            create_socket.settimeout(5)
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

    @staticmethod
    def _cleanedup_cert_name(cert_name: str) -> str:
        return str(cert_name.split("/")[-1])

    def get_certs(self) -> Dict[str, int]:
        '''
        Checks the validity of certs and returns a state value where
        0: Valid
        1: Invalid
        2: Valid, but only for a maximum of 30 days
        '''
        config_key = f"{self.mode}_certs"
        cert_validity = {
            self._cleanedup_cert_name(str(cert)): 1 for cert in self.config[config_key].values()
        }
        for cert in self.config[config_key]:
            cert = self.config[config_key][cert].get(str)
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
                self.logger.error(f"Could not decode {cert}")
                continue
            # get the number of valid days left for the cert, compating the cert's
            # notAfter date to "today's" date
            not_after = datetime.strptime(not_after_timestamp, "%Y%m%d%H%M%S%z").date()
            now = datetime.now().date()
            num_days = not_after - now
            num_days = num_days.days
            self.logger.info(f"{cert} valid for {num_days} days, till {not_after}")
            if num_days > 30:
                cert_validity[self._cleanedup_cert_name(cert)] = 0
            elif num_days > 0 and num_days <= 30:
                cert_validity[self._cleanedup_cert_name(cert)] = 2
        return cert_validity

    def get_stats(self) -> Dict[str, Dict]:
        """Get stats from current ovn cluster unit"""
        stats = {
            "cluster_status": self.get_cluster_status(),
            "ports": self.get_ports(),
            "certs": self.get_certs(),
        }
        return stats


if __name__ == "__main__":
    scraper = OvnScraper()
    for k,v in scraper.get_stats().items():
        print(f"RET for {k}", v)