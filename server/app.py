from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit
from threading import Lock
from serial import Serial
from serial_sim import SerialSim
import numpy as np
import struct
import random
from time import time_ns
from datetime import datetime
import json
import os
import signal
import sys

# Some code taken from https://medium.com/the-research-nest/how-to-log-data-in-real-time-on-a-web-page-using-flask-socketio-in-python-fb55f9dad100
# And https://projecthub.arduino.cc/ansh2919/serial-communication-between-python-and-arduino-663756

# Set up Serial to communicate with Feather
s = Serial(port="COM16", baudrate=115200, timeout=0.5)  # change when we actually start talking with Feather
all_samples = {}
# {"sensor": [{"interptime": #, "time": #, "altitude": #, "value": #}, {"interptime": #, "time": #, "altitude": #, "value": #}], "sensor": ...}
recent_packets = []
latest_packet_num = 0
initialized = False
endianness = '<'  # must match Arduino/Feather endianness! Apparently they like little!

# Set up Flask web app
async_mode = None
app = Flask(__name__)
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

# Set up logging
log_filename = os.path.join("logs", f"log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json")
packets_since_log = 0
max_packets_since_log = 10


def handle_termination(signum, frame):
    s.close()  # It's really annoying if the Serial isn't closed because then the computer can't use it
    sys.exit(0)


signal.signal(signal.SIGINT, handle_termination)
signal.signal(signal.SIGTERM, handle_termination)


def string_to_bytes(s):
    return b''.join([int(s[i * 8: i * 8 + 8][::-1], 2).to_bytes(1, byteorder='big') for i in range(len(s) // 8)])


def get_parity(bytes_n):
    # Function to get parity of bytes n.
    # Returns 1 if n has odd parity and 0 if n has even parity
    # This is for bytes objects (multiple bytes)
    parity = False
    for i in range(len(bytes_n)):
        n = bytes_n[i]
        byte_parity = False
        while n:
            byte_parity = not byte_parity
            n = n & (n - 1)
        parity = byte_parity ^ parity
    return parity


def separate_preamble(packet):
    # Determine whether a packet is a data packet, message packet, error packet, sync packet, ack packet, etc.
    # First byte is parity, next six bytes are callsign, next two bytes are the packet number, last is the packet type
    # This is actually only some of the preamble
    # Output: success bool, parity bool, callsign string, packet number, packet type (D, E, A, S, or M)
    try:
        p, cs1, cs2, cs3, cs4, cs5, cs6, packet_num, packet_type = struct.unpack(endianness + 'BccccccHc', packet[:10])
        callsign = ''.join([c.decode('ascii') for c in (cs1, cs2, cs3, cs4, cs5, cs6)])
        packet_type = packet_type.decode('ascii')
        return True, p, callsign, packet_num, packet_type, packet[10:]
    except:  # UnicodeDecodeError and struct error
        print("ASCII error in preamble. Discarding packet")
        # socketio.emit("error", "ASCII error in preamble. Discarding packet")
        # Idk if it's smarter to send the error message here, or let the other function do it
        # I will try to keep all client communication in one function, I think
        err_msg = "ASCII error in interpreting packet type"
        return False, 0, "______", -1, "E", struct.pack(endianness + 'B', len(err_msg)) + err_msg.encode('ascii')


def unpack_data_packet(pck):
    # Convert a data packet (a series of bytes, no more than 252 bytes long) into a dictionary
    # This is assuming that the first two values of the extended preamble (packet number and type)
    # have already been extracted and removed
    # Output: success bool, dictionary of data from a TX, structured like
    # {interptime: #, time: #, altitude: #, sensors: {"": #, "": #}}
    data = []
    idx = 0
    samples_format = 'B'
    try:
        num_samples = struct.unpack(endianness + samples_format, pck[idx:idx+1])[0]
    except:  # struct error and UnicodeDecodeError
        print("Error unpacking num samples")
        return False, {}
    idx += 1
    for sample_idx in range(num_samples):
        data.append({})
        data[sample_idx]['interptime'] = time_ns() # time packet was interpreted; probably similar to time it was broadcast
        try:
            data[sample_idx]['time'], data[sample_idx]['altitude'], num_sensors = struct.unpack(endianness + 'HHB', pck[idx:idx+(2+2+1)])
        except:  # idk what the error would be, but something
            print("Error unpacking sample values")
            return False, {}
        data[sample_idx]['time'] /= 4
        data[sample_idx]['altitude'] /= 8
        idx += 2+2+1
        data[sample_idx]['sensors'] = {}
        ordered_sensors = []
        for sensor_idx in range(num_sensors):
            # Get the names of all sensors
            sensor_name_length = struct.unpack(endianness + 'B', pck[idx:idx+1])[0]
            # print(f"Found a sensor with name length {sensor_name_length}")
            if sensor_name_length > 5:
                # Something has definitely gone wrong. We shouldn't have any sensors with a name this long
                print("Sensor name too long!")
                return False, {}
            idx += 1
            try:
                sensor_name = struct.unpack(endianness + str(sensor_name_length) + 's', pck[idx:idx+sensor_name_length])[0].decode('ascii')
            except:  # UnicodeDecodeError and struct error
                print("Error unpacking sensor name")
                return False, {}
            # print(f"Sensor is a {sensor_name}!")
            idx += sensor_name_length
            ordered_sensors.append(sensor_name)
        for sensor_idx in range(num_sensors):
            # Get the actual values of all sensors
            try:
                sensor_val = struct.unpack(endianness + 'H', pck[idx:idx+2])[0]
            except:
                print("Error unpacking sensor values")
                return False, {}
            idx += 2
            data[sample_idx]['sensors'][ordered_sensors[sensor_idx]] = sensor_val
            if ordered_sensors[sensor_idx] == "BAT":
                data[sample_idx]['sensors'][ordered_sensors[sensor_idx]] /= 13107  # convert battery voltage back to 3-5 range
    return True, data


def unpack_message_packet(pck):
    # Read the message from a message packet, assuming that the packet's extended preamble (time, number, and type)
    # has already been read and extracted
    # Packet content is a ushort and a string
    try:
        msg_length = struct.unpack(endianness + 'B', bytes([pck[0]]))[0]
        pck_message = struct.unpack(endianness + f'{msg_length}s', pck[1:])[0].decode('ascii')
    except:
        return "[Error unpacking message]"
    return pck_message


def unpack_error_packet(pck):
    # Read the error from an error packet, assuming that the packet's extended preamble (time, number, and type)
    # has already been read and extracted
    # Packet content is a ushort and a string
    # This is the same as a message packet (for now), so I'll just use that
    return unpack_message_packet(pck)


def unpack_ack_packet(pck):
    # Read the packet number from an ack packet, assuming that the packet's extended preamble (time, number, and type)
    # has already been read and extracted
    # Packet content is just a uint
    orig_pck_num = struct.unpack(endianness + 'H', pck[:2])
    return orig_pck_num


def unpack_sync_packet(pck):
    # Read the time from a sync packet, assuming that the packet's extended preamble (time, number, and type)
    # has already been read and extracted
    # Packet content is just the time as a uint
    pck_time = struct.unpack(endianness + 'H', pck[:2])
    return pck_time


def packet_data_to_all_samples(data_from_packet):
    # Save a packet to all_samples
    # This may not actually be the best way to do continuous logging
    # Currently (6/18/2025) unused
    for sample_idx in range(len(data_from_packet)):
        for sensor in data_from_packet[sample_idx]['sensors'].keys():
            if sensor not in all_samples.keys():
                all_samples[sensor] = []
            all_samples[sensor].append({"interptime": data_from_packet[sample_idx]["interptime"],
                                        "time": data_from_packet[sample_idx]["time"],
                                        "altitude": data_from_packet[sample_idx]["altitude"],
                                        "value": data_from_packet[sample_idx]["sensors"][sensor]})


def interpret_packet(packet):
    # Determine the packet's type and do with it what must be done
    # If it's a data packet, add it to recent_packets and send it to the client
    # If it's a message packet, send it to the client's message box
    # If it's an error packet, send it to the client's message box
    # If it's a sync packet, ignore it
    # If it's an ack packet, ignore it
    # Using socketio.emit() is good when the server is originating an exchange
    global latest_packet_num
    # Check parity bit to see if any errors have occurred
    print(packet)
    actual_parity = get_parity(packet)
    if not actual_parity:  # = is even
        print("Packet with incorrect parity. Discarding")
        socketio.emit("error", "Packet with incorrect parity. Discarding")
    success, parity, callsign, packet_num, packet_type, packet_content = separate_preamble(packet)
    print(packet_num, packet_type, packet_content)
    latest_packet_num = max(latest_packet_num, packet_num)
    match packet_type:
        case "D":
            success, data_from_packet = unpack_data_packet(packet_content)
            if success:
                # Send data to client
                socketio.emit("data", data_from_packet)
                # Save data to all_samples
                # packet_data_to_all_samples(data_from_packet)
                # Put packet in recent_packets for logging
                recent_packets.append({"type": "D", "data": data_from_packet})
            else:
                socketio.emit("error", "Error unpacking data packet")
        case "M":
            packet_message = unpack_message_packet(packet_content)
            socketio.emit("message", packet_message)
            recent_packets.append({"type": "M", "interptime": time_ns(), "value": packet_message})
            print(packet_message)
        case "E":
            packet_error = unpack_error_packet(packet_content)
            socketio.emit("error", packet_error)
            recent_packets.append({"type": "E", "interptime": time_ns(), "value": packet_error})
            print(packet_error)
        case "A":
            ack_packet_num = unpack_ack_packet(packet_content)
            recent_packets.append({"type": "A", "interptime": time_ns(), "packet": ack_packet_num})
            print(ack_packet_num)
        case "S":
            packet_time = unpack_sync_packet(packet_content)
            recent_packets.append({"type": "S", "interptime": time_ns(), "time": packet_time})
            print(packet_time)


def write_recent_packets_to_log():
    # Write all the samples in recent_packets to the log file and clear recent_packets
    global recent_packets
    with open(log_filename, 'a') as log_file:
        log_file.writelines([json.dumps(p, sort_keys=True) + "\n" for p in recent_packets])
    recent_packets = []


def background_thread():
    # Constant updates to client
    global packets_since_log, max_packets_since_log
    while True:
        socketio.sleep(0.25)
        if initialized:
            # Get latest data from s
            num_bytes = s.in_waiting
            if num_bytes > 0:
                # print(f"{num_bytes} bytes in waiting")
                # There is data waiting to be read
                packet = s.read(size=num_bytes)
                s.reset_input_buffer()
                # print(f"Read {packet}")
                # if b'\r\n' in packet:
                #     packet = packet.split(b'\r\n')[0]  # If we accidentally miss a packet (or multiple pile up), several packets will be waiting for us; just grab the first one
                interpret_packet(packet)
                packets_since_log += 1
                if packets_since_log >= max_packets_since_log:
                    write_recent_packets_to_log()
                    packets_since_log = 0


@app.route("/")
def main_page():
    # Serve the main page, index.html. Will probably be the only page
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.event  # simplified version of on(); takes event name from function name
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)


@socketio.event
def connect_ack():
    print("A client has connected!")


@socketio.event
def note(user_note):
    socketio.emit("message", user_note)
    recent_packets.append({"type": "N", "interptime": time_ns(), "value": user_note})


@socketio.event
def initialize():
    global initialized
    print("Initialize!")
    # packet = struct.pack(endianness + 'HcH', latest_packet_num, b'S', 0)
    # s.write(packet)
    initialized = True


if __name__ == "__main__":
    app.run()


# emit() is for named events, send() is for unnamed events
# you can add broadcast=True to send the emit() or send() to all clients

