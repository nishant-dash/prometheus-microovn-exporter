# Prometheus Microovn Exporter

## A simple snap package that exports minimal data from a ovn cluster such as:
1. Cluster status
2. Open ports
3. Valid certs

*Can use with either microovn or ovn (chassis and central both)*

Example output (here, 0 generally means good, as in cluster state is good, port is open, cert is valid)

```console
$ curl localhost:9999
...
# HELP ovn_cluster_state State of ovn ovn_cluster_state
# TYPE ovn_cluster_state gauge
ovn_cluster_state{cluster_status="nb"} 0.0
ovn_cluster_state{cluster_status="sb"} 0.0
# HELP ovn_cluster_state State of ovn ovn_cluster_state
# TYPE ovn_cluster_state gauge
ovn_cluster_state{ports="6641"} 0.0
ovn_cluster_state{ports="6642"} 0.0
ovn_cluster_state{ports="6643"} 0.0
ovn_cluster_state{ports="6644"} 0.0
# HELP ovn_cluster_state State of ovn ovn_cluster_state
# TYPE ovn_cluster_state gauge
ovn_cluster_state{certs="server.crt"} 0.0
ovn_cluster_state{certs="cluster.crt"} 1.0
```
