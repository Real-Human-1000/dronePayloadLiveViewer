from time import sleep
import math
import random
import struct
# An interesting shell command:
# python -m serial.tools.list_ports


class SerialSim:
    def __init__(self, port, baudrate, timeout):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.opened = True if port is not None else False
        # Simulation (this is just all the values, not in packet form):
        self.latest_packet = 0
        self.data = {"time": 0.0, 'altitude': 0.0, 'CO2': 400.0, 'temperature': 21.0, 'humidity': 0.4, 'TVOC': 1000.0, 'eCO2': 410.0, 'PM': 1000.0}
        self.step_data(0.25)
        # Buffers
        self.input_buffer = b'' #self.generate_data_packet()
        self.output_buffer = b''

    # Simulation functions
    def step_data(self, dt):
        # Step the data forward in time (add randomly to most of the other values)
        self.latest_packet += random.randint(1,2)
        self.data['time'] += dt
        self.data['altitude'] = max(250 * (1 - math.cos(0.2 * self.data['time'])) + 3 * random.random(), 0)
        self.data['CO2'] = 200.0 / (1.0 + ((self.data['altitude']-100.0)/10.0)**2.0) + 400.0 + random.random() * 60.0 - 30.0
        self.data['temperature'] = max(21.0 + random.random() * 4.0 - 2.0, 0.0)
        self.data['humidity'] = min(max(0.4 + random.random() / 10.0 - 0.05, 0.0), 1.0)
        self.data['TVOC'] = max(200.0 / (1.0 + ((self.data['altitude']-100.0)/20.0)**2.0) + random.random() * 50.0 - 25.0, 0)
        self.data['eCO2'] = max(self.data['CO2'] + random.random() * 60.0 - 30.0, 0)
        self.data['PM'] = max(200.0 / (1.0 + ((self.data['altitude']-90.0)/5.0)**2.0) + 100.0 + random.random() * 200.0 - 100.0, 0)
        # print(self.data)

    def generate_data_packet(self):
        # Convert the internal data into a data packet
        # I think the preamble is automatically separated, so I will ignore that
        extended_preamble_format = 'Hc'
        sensors_to_include = ["CO2", "TVOC", "eCO2", "PM"]
        assert all([s in self.data.keys() for s in sensors_to_include])
        sample_format = 'HBBB' + ('B'.join([str(len(s)) + 's' for s in sensors_to_include])) + 'H'*len(sensors_to_include)
        complete_format = extended_preamble_format + 'B' + sample_format
        sample = [int(self.data['time'] * 4), int(self.data['altitude'] / 2), len(sensors_to_include)]
        for s in sensors_to_include:
            sample.append(len(s))
            sample.append(s.encode('ascii'))
        for s in sensors_to_include:
            sample.append(int(self.data[s]))
        packet = struct.pack('<' + complete_format, self.latest_packet, b'D', 1, *sample)
        # print(packet)
        # print("True:")
        # print(struct.unpack('<' + complete_format, packet))
        # print("Generated a packet of length " + str(len(packet)))
        packet = self.string_to_bytes("100100111100000000100010100000000011110110111010011001011001000011000000110000101111001001001100001000000010101001101010111100101100001000100000101001101100001011110010010011000010000000001010101100100000110011001100001000000000101010110010000011001010110000100000000010101011001010001100000011000010000000001010101100100100110010101100001000000000101010110010101011000000110011000000010000101000001000101010110100110100000011100010000000000100111110000000010001010000000000110100000000000010000000000000000000000000000000000000000000000011001100011101")
        return packet

    def string_to_bytes(self, s):
        return b''.join([int(s[i*8 : i*8+8][::-1], 2).to_bytes(1, byteorder='big') for i in range(len(s)//8)])

    def generate_message_packet(self):
        # Create a message packet
        msg = "I am a"
        msg += random.choice([" red", "n orange", " yellow", " green", " blue", "n indigo", " violet", " crimson", "n umber", " golden", " lime", " cyan", " navy", " magenta", " purple", " white", " gray", " black"])
        msg += " "
        msg += random.choice(["eagle", "hawk", "parrot", "elephant", "hippo", "rhino", "possum", "raccoon", "squirrel", "cat", "dog", "hamster", "guinea pig", "ant", "anteater", "crocodile", "alligator", "butterfly", "moth", "falcon", "horse", "donkey", "cow", "bull", "goat", "chicken", "quail", "beetle", "centipede", "penguin"])
        msg += "!"
        self.latest_packet += 1
        packet = struct.pack(f'>HcB{len(msg)}s', self.latest_packet, b'M', len(msg), msg.encode('ascii'))
        return packet

    def generate_error_packet(self):
        # Create an error packet
        err = "Error: Not enough errors!"
        self.latest_packet += 1
        packet = struct.pack(f'>HcB{len(err)}s', self.latest_packet, b'E', len(err), err.encode('ascii'))
        return packet

    def generate_sync_packet(self):
        # Create a sync packet
        self.latest_packet += 1
        packet = struct.pack('>HcH', self.latest_packet, b'S', self.data['time'])
        return packet

    def generate_ack_packet(self, pck):
        # Create an acknowledgement packet based on a sync packet
        orig_pck_num = struct.unpack('>H', pck[0])
        self.latest_packet += 1
        packet = struct.pack('>HcH', self.latest_packet, b'A', orig_pck_num)
        return packet

    def generate_random_average_packet(self):
        r = random.random()
        if r < 0.9:
            self.step_data(dt=0.25)
            return self.generate_data_packet()
        elif r < 0.95:
            return self.generate_message_packet()
        else:
            return self.generate_error_packet()

    # Serial functions
    def open(self):
        pass

    def close(self):
        pass

    def read(self, size=1):
        if size < len(self.input_buffer):
            vals_read = self.input_buffer[:size]
            self.input_buffer = self.input_buffer[size:]
        else:
            vals_read = self.input_buffer
            self.input_buffer = b''
        return vals_read

    def readline(self):
        # "Reading from Serial connection"
        # I'm going to assume that I'm never going to use this
        sleep(self.timeout)
        vals_read = self.input_buffer
        self.input_buffer = b''
        return vals_read

    def write(self, data):
        # "Writing to the Serial connection"
        self.output_buffer = data

    @property
    def in_waiting(self):
        # Get number of bytes in the input buffer
        if random.random() < 0.25:
            # Artificially generate some packets, sometimes
            self.input_buffer += self.generate_random_average_packet()
        return len(self.input_buffer)

    def out_waiting(self):
        # Get the number of bytes in the output buffer
        return len(self.output_buffer)

    def reset_input_buffer(self):
        self.input_buffer = b''

    def readable(self):
        return True

    def writable(self):
        return True

    def seekable(self):
        return False

    def readinto(self, b):
        # I'm gonna be honest I don't know what this does
        return len(b)



if __name__ == "__main__":
    s = SerialSim(port="COM4", baudrate=115200, timeout=0.1)
