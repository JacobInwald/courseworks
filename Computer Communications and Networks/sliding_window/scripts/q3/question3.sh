#!/bin/sh


echo "Starting 5ms delay run"
sudo tc qdisc del dev lo root
sudo tc qdisc add dev lo root netem loss 5% delay 5ms rate 10mbit

echo -n > "q3-5ms-out-$1"

for i in $(seq 1 3);
do
  echo "Running ..."
  sudo python3 ../../Receiver3.py 1 ../../test_copy.jpg & 
  sudo python3 ../../Sender3.py localhost 1 ../../test.jpg 20 $1 >> "q3-5ms-out-$1"
  wait $!
done


echo "Starting 25ms delay run"
sudo tc qdisc del dev lo root
sudo tc qdisc add dev lo root netem loss 5% delay 25ms rate 10mbit

echo -n > "q3-25ms-out-$1"

for i in $(seq 1 3);
do
  echo "Running ..."
  sudo python3 ../../Receiver3.py 1 ../../test_copy.jpg & 
  sudo python3 ../../Sender3.py localhost 1 ../../test.jpg 20 $1 >> "q3-25ms-out-$1"
  wait $!
done


echo "Starting 100ms delay run"
sudo tc qdisc del dev lo root
sudo tc qdisc add dev lo root netem loss 5% delay 100ms rate 10mbit

echo -n > "q3-100ms-out-$1"

for i in $(seq 1 3);
do
  echo "Running ..."
  sudo python3 ../../Receiver3.py 1 ../../test_copy.jpg & 
  sudo python3 ../../Sender3.py localhost 1 ../../test.jpg 20 $1 >> "q3-100ms-out-$1"
  wait $!
done


