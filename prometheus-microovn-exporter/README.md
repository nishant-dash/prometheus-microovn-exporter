## ovn checks:
1. certs
    - server.crt
    openssl x509 -noout -dates -in /var/snap/microovn/common/state/server.crt

    - cluster.crt
    openssl x509 -noout -dates -in /var/snap/microovn/common/state/cluster.crt

2. pids
    - /var/snap/microovn/common/run/central/ovnnb_db.pid  
    - /var/snap/microovn/common/run/central/ovn-northd.pid  
    - /var/snap/microovn/common/run/central/ovnsb_db.pid

    - /var/snap/microovn/common/run/chassis/ovn-controller.pid

    - /var/snap/microovn/common/run/switch/ovsdb-server.pid
    - /var/snap/microovn/common/run/switch/ovs-vswitchd.pid

3. sockets
    - /var/snap/microovn/common/run/central/ovnnb_db.sock
    - /var/snap/microovn/common/run/central/ovnsb_db.sock

    - /var/snap/microovn/common/run/switch/db.sock

4. logs path
    - /var/snap/microovn/common/logs

5. env
    - /var/snap/microovn/common/data/ovn.env

6. bins
    - /snap/bin
    - microovn.ovn-appctl
    - microovn.ovn-nbctl
    - microovn.ovn-sbctl
    
    - microovn.ovs-appctl
    - microovn.ovs-dpctl
    - microovn.ovs-ofctl
    - microovn.ovs-vsctl

7. checks
    - cluster check
        - microovn.ovs-appctl -t /var/snap/microovn/common/run/central/ovnnb_db.ctl cluster/status OVN_Northbound
        - microovn.ovs-appctl -t /var/snap/microovn/common/run/central/ovnsb_db.ctl cluster/status OVN_Southbound

    - microovn.ovs-vsctl list Open-vSwitch

    - microovn.ovs-vsctl get open . external_ids:ovn-remote

    - fix nb and sb listeners
        - microovn.ovn-nbctl --db unix:/var/snap/microovn/common/run/central/ovnnb_db.sock set-connection ptcp:6641
        - microovn.ovn-sbctl --db unix:/var/snap/microovn/common/run/central/ovnsb_db.sock set-connection ptcp:6642

    - get connections
        - microovn.ovn-nbctl --db unix:/var/snap/microovn/common/run/central/ovnnb_db.sock get-connection

8. ports
  - 6641 (OVN Northbound OVSDB Server)
  - 6642 (OVN Southbound OVSDB Server)
  - 6643 (OVN NB RAFT control plane)
  - 6644 (OVN SB RAFT control plane)