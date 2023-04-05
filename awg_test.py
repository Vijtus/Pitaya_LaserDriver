#!/usr/bin/python3

import numpy as np
import math
from matplotlib import pyplot as plt
import redpitaya_scpi as scpi

IP = "rp-f0a29f.local"
rp_s = scpi.scpi(IP)

wave_form = 'arbitrary'
freq = 100
ampl = 1

N = 10000#16384               # Number of samples
t = np.linspace(0, 1, N)

#x = np.sin(t) + 1/3*np.sin(3*t)

waveform_ch_10 = []

def ramp_generator(N, min=0, max=1):
    ramp = np.linspace(0, 1, N)
    ramp = ramp * (max - min) + min
    #ramp = ramp.tolist()
    return ramp

def impose_sine(amp, freq, input_data):
    data = input_data.copy()
    for i in range(len(data)):
        data[i] = data[i] + amp * math.sin(freq * 2 * math.pi * i / len(data))
        if data[i] > 1:
            data[i] = 1
        elif data[i] < -1:
            data[i] = -1
    return data


x = ramp_generator(N, min=0, max=1)
x = impose_sine(0.1, 100, x)
plt.plot(t, x)
plt.title('Custom waveform')
plt.show()

for n in x:
    waveform_ch_10.append(f"{n:.5f}")
waveform_ch_1 = ", ".join(map(str, waveform_ch_10))

print(waveform_ch_10)
print(len(waveform_ch_10)) # 16384  --- 16384

rp_s.tx_txt('GEN:RST')

rp_s.tx_txt('SOUR1:FUNC ' + str(wave_form).upper())

rp_s.tx_txt('SOUR1:TRAC:DATA:DATA ' + waveform_ch_1)

rp_s.tx_txt('SOUR1:FREQ:FIX ' + str(freq))

rp_s.tx_txt('SOUR1:VOLT ' + str(ampl))

rp_s.tx_txt('OUTPUT1:STATE ON')
rp_s.tx_txt('SOUR1:TRIG:INT')

rp_s.close()