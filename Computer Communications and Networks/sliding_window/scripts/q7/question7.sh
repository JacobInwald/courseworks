#!/bin/sh

sudo tc qdisc del dev lo root
sudo tc qdisc add dev lo root netem loss 5% delay 25ms rate 10mbit

./question7.py
