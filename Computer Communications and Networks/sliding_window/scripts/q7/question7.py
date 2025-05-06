#!/bin/python3
import subprocess
import shlex
import time
import re

# Define the variables for the experiment
SERVER_IP = "localhost"  # IP address of the iperf server
FILE_PATH = "../../test.jpg"  # Path to the file to be transferred
TIME = 20 # Duration of the test in seconds
WINDOW_SIZES = ['1KB','2KB','4KB','8KB','16KB','32KB']
# WINDOW_SIZES=['16']
MSS = 1024  # Maximum Segment Size in bytes (1KB)

# Function to start the iperf3 server (run on the server side)
def start_iperf_server(window_size):
    print("Starting iperf server...")
    p = subprocess.Popen('sudo iperf -s -P 1', stdout=subprocess.PIPE, shell=True)
    time.sleep(1)  # Wait for the server to start
    return p

# Function to run iperf3 client and capture the throughput
def run_iperf_client(window_size):
    print(f"Running iperf with TCP, MSS={MSS} and window size={window_size}...")
    

    command = f'iperf -f K -c localhost -M 1024 -F ../../test.jpg -t 20 -w {window_size}'
    # Run the iperf3 client command
    print('Running', command) 
    result = subprocess.run(shlex.split(command), capture_output=True, text=True)
    
    # Extract throughput values from the output using regex
    throughput_match = re.search(r'(\d+\.\d+)\s+KBytes/sec', result.stdout)
    if throughput_match:
        throughput = throughput_match.group(1)  # Extract the throughput value (in Mbits/sec)
        return float(throughput)
    else:
        print(f"No throughput data found for window size {window_size}")
        return -10000 

# Function to save results to a file
def save_results(window_size, throughput):
    with open("throughput_results.txt", "a") as f:
        f.write(f"Window Size: {window_size}, Throughput: {throughput} KBps\n")

def main():
    # Start iperf3 server on the server side
    print('starting experiments')
    # Loop through the different window sizes
    for window_size in WINDOW_SIZES:
        print('next window size')
        throughput = 0
        for _ in range(3):
            start_iperf_server(window_size)
            throughput += run_iperf_client(window_size)

        throughput /= 3
        if throughput > 0:
            save_results(window_size, throughput)
            print(f"Throughput for window size {window_size}: {throughput} KBps")
        
        # Sleep before starting the next test

    print("Experiment completed. Throughput results saved to throughput_results.txt.")

if __name__ == "__main__":
    main()

