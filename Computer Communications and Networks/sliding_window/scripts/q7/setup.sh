#!/bin/sh

# echo 'net.core.wmem_max=4194304' >> /etc/sysctl.conf
# echo 'net.core.rmem_max=12582912' >> /etc/sysctl.conf
# echo 'net.core.wmem_min=1' >> /etc/sysctl.conf
# echo 'net.core.rmem_min=1' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_rmem = 1 87380 4194304' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_wmem = 1 87380 4194304' >> /etc/sysctl.conf

sysctl -p
