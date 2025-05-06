#!/bin/sh

sudo tc qdisc del dev lo root
sudo tc qdisc add dev lo root netem loss 5% delay 5ms rate 10mbit

echo -n > "q1-out-$1"

for i in $(seq 1 4);
do
  echo "Running ..."
  sudo python3 ../../Receiver2.py 1 ../../test_copy.jpg & 
  sudo python3 ../../Sender2.py localhost 1 ../../test.jpg $1 >> "q1-out-$1"
  wait $!
done


