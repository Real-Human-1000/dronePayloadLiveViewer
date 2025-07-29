from serial import Serial
import os
import sys
import signal
from datetime import datetime
from time import sleep

# Script to just save messages from Serial to a new file

# Set up Serial connection
s = Serial(port="COM6", baudrate=115200, timeout=0.5)  # change when we actually start talking with Feather

log_filename = os.path.join("raw_serial_logs", f"log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json")

# test 1: bringing drone down at setting 43, will continue rolling until its on the ground
# was still about 400ft away when the last successful test happened
# got stuck on the way back

# test 2: 1086 feet away, 350 ft up

# both tests have groundstation under a metal structure

# First test was recalled at drone battery percent 40%
# Second test: test 43 at drone battery percent 50%
# Setting 51 stops working on both tests(?) Pulled drone back after got stuck at 51 (then it unstuck itself after the drone got really close)


def handle_termination(signum, frame):
    s.close()  # It's really annoying if the Serial isn't closed because then the computer can't use it
    sys.exit(0)


signal.signal(signal.SIGINT, handle_termination)
signal.signal(signal.SIGTERM, handle_termination)


# Constant updates to client
while True:
    sleep(0.25)
    # Get latest data from s
    num_bytes = s.in_waiting
    if num_bytes > 0:
        # print(f"{num_bytes} bytes in waiting")
        # There is data waiting to be read
        serial_messages = s.read(size=num_bytes)
        s.reset_input_buffer()
        # print(f"Read {packet}")
        # if b'\r\n' in packet:
        #     packet = packet.split(b'\r\n')[0]  # If we accidentally miss a packet (or multiple pile up), several packets will be waiting for us; just grab the first one
        serial_messages = [n.decode('ascii') + "\n" for n in serial_messages.split(b'\r\n') if len(n) > 0]
        print(serial_messages)
        with open(log_filename, 'a') as file:
            file.writelines(serial_messages)

