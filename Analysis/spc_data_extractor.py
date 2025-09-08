import matplotlib.pyplot as plt
import struct

# This file is designed to extract the spectral data from the SPC files that Dr. Merchan is giving me
# I believe that these files are generated from a program called GENESIS by the company EDAX
# But no SPC file viewer I've tried (SpectraGryph1.2, SpectralWorks' ScanEdit) seems to be able to read these
# And it seems to be very difficult to get a working copy of GENESIS

# The first SPC file I have appears to have four-byte integer data starting at address 0x00000F2C (integer 3884)
# 4-byte (32-bit) unsigned (?) integers = longs (or ints on some platforms)

file_path = "SPCFiles\\SC 31-8-ttest2-punto1.spc"

graph_data_start = 3884  # right now, discovered by inspection

with open(file_path,'rb') as file:
    file_data = file.read()

# Between two ticks on the x-axis of the graph (ex between 8.00 and 9.00 keV) there are 100 bars
# --> Between 0.00 and 10.0 there are about 1000 bars
# --> 4000 bytes total
num_bars = 1000
graph_data_bytes = file_data[graph_data_start:graph_data_start+(4 * num_bars)]

graph_data = [struct.unpack('<l', graph_data_bytes[i*4:(i*4+4)])[0] for i in range(1000)]

independent_axis = [i/100 for i in range(1000)]

plt.plot(independent_axis, graph_data, 'r')
plt.xlabel("keV")
plt.ylabel("Counts")
plt.show()