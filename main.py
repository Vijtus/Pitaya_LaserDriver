#!/usr/bin/python3
#Importing libraries

import matplotlib.pyplot as plot
import sys
import redpitaya_scpi as scpi
import numpy as np
from time import sleep
import csv
from simple_pid import PID 
import time
import struct

#Setup the connection to the Red Pitaya
IP = "rp-f0a29f.local"
rp_s = scpi.scpi(IP)

#Set the parameters for the signal generator
wave_form = 'SQUARE'
freq = 2000
ampl = 1
#Decimation factor
dec = 32

#Generate the signal
def set_generator(waveform, frequency, amplitude, offset):
    rp_s.tx_txt('GEN:RST')
    rp_s.tx_txt('SOUR1:FUNC ' + str(waveform).upper())
    rp_s.tx_txt('SOUR1:FREQ:FIX ' + str(frequency))
    rp_s.tx_txt('SOUR1:VOLT ' + str(amplitude))
    rp_s.tx_txt('SOUR1:VOLT:OFFS ' + str(offset))
    rp_s.tx_txt('OUTPUT1:STATE ON')
    rp_s.tx_txt('SOUR1:TRIG:INT')

set_generator(wave_form, freq, ampl, 0)
sleep(0.5)

#Modify the offset of the signal generator
def write_generator_offset(offset):
    rp_s.tx_txt('SOUR1:VOLT:OFFS ' + str(offset))

#Define a function to sample the oscilloscope
def sample_oscilloscope():
    #Set the parameters for the acquisition
    rp_s.tx_txt('ACQ:RST')
    sleep(0.1)
    rp_s.tx_txt('ACQ:DATA:FORMAT BIN')
    rp_s.tx_txt('ACQ:DATA:UNITS VOLTS')
    #The Red Pitaya has a sample rate of 125 MS/s
    #we use the decimation factor to reduce the sample rate
    rp_s.tx_txt(f'ACQ:DEC {dec}')
    rp_s.tx_txt('ACQ:SOUR1:GAIN HV')
    rp_s.tx_txt('ACQ:TRIG:LEV 0.5')
    rp_s.tx_txt('ACQ:TRIG:DLY 8000')
    rp_s.tx_txt('ACQ:START')
    rp_s.tx_txt('ACQ:TRIG CH1_PE')
    sleep(0.1)

    #Wait for the acquisition to finish
    while 1:
        rp_s.tx_txt('ACQ:TRIG:STAT?')
        if rp_s.rx_txt() == 'TD':
            break
    #Read the data from the acquisition
    rp_s.tx_txt('ACQ:SOUR1:DATA?')
    print('Reading data...')
    #rp_s.tx_txt('ACQ:SOUR1:DATA:STA:N? 0,1000')
    buff_byte = rp_s.rx_arb()
    print('Done reading data!') 

    #Convert the data to a list of floats
    # buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
    # buff = list(map(float, buff_string))

    buff = [struct.unpack('!f',bytearray(buff_byte[i:i+4]))[0] for i in range(0, len(buff_byte), 4)]
    return buff

buff = sample_oscilloscope()



#Save the data to a csv file
# with open('data.csv', 'w') as f:    
#     writer = csv.writer(f)
#     writer.writerows(zip(range(len(buff)), buff))

#Plot the data
plot.plot(buff)
plot.ylabel('Voltage')
plot.show()
#exit()
def calculate_3rd_harmonic_amplitude(buff):
    #Calculate the FFT of the data
    t = np.array(buff)
    #Compute the time step including decimation
    dt = 1/(125000000/dec)
    freqs = np.fft.fftfreq(t.shape[-1], dt)
    fft = np.abs(np.fft.fft(t))
    #Plot the FFT amplitude
    # plot.plot(freqs, fft)
    # plot.ylabel('Amplitude')
    # plot.xlabel('Frequency')
    # plot.title('FFT of the signal')
    # plot.xlim(left=0, right=freq*10)
    # plot.ylim(bottom=0)
    # plot.show()

    #Find the 3rd harmonic amplitude from the freqs array
    # print("freqs:")
    # print(freqs)
    # print("fft:")
    # print(fft)
    target_freq = freq*3
    lowest_delta = 1000000
    index = 0
    for i in range(len(freqs)):
        delta = abs(freqs[i]-target_freq)
        if delta < lowest_delta:
            lowest_delta = delta
            index = i
    return fft[index]

harm = calculate_3rd_harmonic_amplitude(buff)
print("The 3rd harmonic amplitude is: " + str(harm))

# Initialize PID controller
pid = PID(0.1, 0.1, 0.1, setpoint=0)

# Initialize process variable and control variable
generator_output = 0
offset = 0

try:
    # Loop until desired stability is reached
    while True:
        # Sample oscilloscope and run FFT to get 3rd harmonic amplitude
        third_harmonic_amplitude = calculate_3rd_harmonic_amplitude(sample_oscilloscope())

        # Calculate offset value using PID controller
        offset = pid(third_harmonic_amplitude)

        # Write new generator offset value to generator
        #write_generator_offset(offset)

        # Print output
        print("3rd harmonic amplitude: " + str(third_harmonic_amplitude))
        print("PID offset: " + str(offset))
        print("")
        # Simulate time passing
        time.sleep(1)
except KeyboardInterrupt:
    rp_s.close()
    print("Exiting program")
