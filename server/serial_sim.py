from time import sleep, time
import math
import random
import struct
# An interesting shell command:
# python -m serial.tools.list_ports


def get_parity(bytes_n):
    # Function to get parity of number n.
    # It returns 1 if n has odd parity,
    # and returns 0 if n has even parity
    # This is for bytes objects (arrays of bytes)
    parity = False
    for i in range(len(bytes_n)):
        n = bytes_n[i]
        byte_parity = False
        while n:
            byte_parity = not byte_parity
            n = n & (n - 1)
        parity = byte_parity ^ parity
    return parity


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
        self.last_step = time()
        # Buffers
        self.input_buffer = b'' #self.generate_data_packet()
        self.output_buffer = b''

    def gaussian(self, x, max, x_at_max, stretching, baseline):
        return max / (1 + ((x-x_at_max)/stretching)**2.0) + baseline

    def crand(self, amp):
        # Centered random number (-amp to +amp)
        return random.random() * 2 * amp - amp

    # Simulation functions
    def step_data(self, dt):
        # Step the data forward in time (add randomly to most of the other values)
        max_alt = 106
        period = 30
        alt_noise = 3
        self.latest_packet += random.randint(1,2)
        self.data['time'] += dt
        self.data['altitude'] = max(max_alt/2 * (1 - math.cos(6.28/period * self.data['time'])) + alt_noise * random.random(), 0)
        self.data['CO2'] = self.gaussian(self.data['altitude'], 400, 100, 10, 400) + self.crand(30.0)
        self.data['temperature'] = max(21.0 + random.random() * 4.0 - 2.0, 0.0)
        self.data['humidity'] = min(max(0.4 + random.random() / 10.0 - 20.05, 0.0), 1.0)
        self.data['TVOC'] = self.gaussian(self.data['altitude'], 300, 80, 5, 100) + self.crand(10.0)
        self.data['eCO2'] = (self.data['TVOC'] / 400 + self.data['CO2'] / 800) * 500
        self.data['PM'] = self.gaussian(self.data['altitude'], 200, 70, 5, 20) + self.crand(10.0)
        # print(self.data)

    def generate_data_packet(self):
        # Convert the internal data into a data packet
        # I think the preamble is automatically separated, so I will ignore that

        # [parity bool not included; will add later]
        # 6 characters = callsign
        # packet number
        # "D" for data packet
        # number of samples
        extended_preamble_format = 'ccccccHcB'
        sensors_to_include = ["CO2", "TVOC", "eCO2", "PM"]

        assert all([s in self.data.keys() for s in sensors_to_include])

        sample_format = 'HHBB' + ('B'.join([str(len(s)) + 's' for s in sensors_to_include])) + 'H'*len(sensors_to_include)
        complete_format = extended_preamble_format + sample_format
        sample = [int(self.data['time'] * 4), int(self.data['altitude'] * 8), len(sensors_to_include)]
        for s in sensors_to_include:
            sample.append(len(s))
            sample.append(s.encode('ascii'))
        for s in sensors_to_include:
            sample.append(int(self.data[s]))
        packet = struct.pack('<' + complete_format, b'K', b'J', b'5', b'I', b'R', b'C', self.latest_packet, b'D', 1, *sample)
        # Need to calculate parity
        parity = not get_parity(packet)
        parity_byte = struct.pack('<?', parity)
        packet = parity_byte + packet
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
        if r < 1.1:
            self.step_data(dt=time() - self.last_step)
            self.last_step = time()
            return self.generate_data_packet()
        elif r < 1.2:
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
        if random.random() < 0.4:
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
