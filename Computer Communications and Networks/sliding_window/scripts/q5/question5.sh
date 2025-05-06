#!/bin/sh


sudo tc qdisc del dev lo root
sudo tc qdisc add dev lo root netem loss 5% delay 25ms rate 10mbit

echo -n > "q5-out-$1"

for i in $(seq 1 3);
do
  echo "Running ..."
  sudo python3 ../../Receiver4.py 1 ../../test_copy.jpg $1 & 
  sudo python3 ../../Sender4.py localhost 1 ../../test.jpg 20 $1 >> "q5-out-$1"
  wait $!
done

