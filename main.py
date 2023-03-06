#!/usr/bin/python3
#Importing libraries

import matplotlib.pyplot as plot
import sys
import redpitaya_scpi as scpi
import numpy as np
from time import sleep
import csv

#Setup the connection to the Red Pitaya
IP = "rp-f0a29f.local"
rp_s = scpi.scpi(IP)

#Set the parameters for the signal generator
wave_form = 'SQUARE'
freq = 3000
ampl = 1
#Decimation factor
dec = 64

#Generate the signal
rp_s.tx_txt('GEN:RST')
rp_s.tx_txt('SOUR1:FUNC ' + str(wave_form).upper())
rp_s.tx_txt('SOUR1:FREQ:FIX ' + str(freq))
rp_s.tx_txt('SOUR1:VOLT ' + str(ampl))
rp_s.tx_txt('OUTPUT1:STATE ON')

#Set the parameters for the acquisition
rp_s.tx_txt('SOUR1:TRIG:INT')
rp_s.tx_txt('ACQ:RST')
rp_s.tx_txt('ACQ:DATA:FORMAT ASCII')
rp_s.tx_txt('ACQ:DATA:UNITS VOLTS')
#The Red Pitaya has a sample rate of 125 MS/s
#we use the decimation factor to reduce the sample rate
rp_s.tx_txt(f'ACQ:DEC {dec}')
rp_s.tx_txt('ACQ:SOUR1:GAIN HV')
rp_s.tx_txt('ACQ:TRIG:LEV 0.5')
rp_s.tx_txt('ACQ:TRIG:DLY 200000')
rp_s.tx_txt('ACQ:START')
rp_s.tx_txt('ACQ:TRIG CH1_PE')

#Wait for the acquisition to finish
while 1:
    rp_s.tx_txt('ACQ:TRIG:STAT?')
    if rp_s.rx_txt() == 'TD':
        break
sleep(0.5)
#Read the data from the acquisition
rp_s.tx_txt('ACQ:SOUR1:DATA?')
print('Reading data...')
#rp_s.tx_txt('ACQ:SOUR1:DATA:STA:N? 0,1000')
buff_string = rp_s.rx_txt()
print('Done reading data!') 

#Convert the data to a list of floats
buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
buff = list(map(float, buff_string))

#Save the data to a csv file
with open('data.csv', 'w') as f:    
    writer = csv.writer(f)
    writer.writerows(zip(range(len(buff)), buff))

#Plot the data
plot.plot(buff)
plot.ylabel('Voltage')
plot.show()

#Calculate the FFT of the data
t = np.array(buff)
#Compute the time step including decimation
dt = 1/(125000000/dec)
freqs = np.fft.fftfreq(t.shape[-1], dt)
fft = np.abs(np.fft.fft(t))
#Plot the FFT amplitude
plot.plot(freqs, fft)
plot.ylabel('Amplitude')
plot.xlabel('Frequency')
plot.title('FFT of the signal')
plot.xlim(left=0, right=freq*10)
plot.ylim(bottom=0)
plot.show()

#Find the 3rd harmonic amplitude from the freqs array
print("freqs:")
print(freqs)
print("fft:")
print(fft)
target_freq = freq*3
lowest_delta = 1000000
index = 0
for i in range(len(freqs)):
    delta = abs(freqs[i]-target_freq)
    if delta < lowest_delta:
        lowest_delta = delta
        index = i
print("The 3rd harmonic amplitude is: " + str(fft[index]))
