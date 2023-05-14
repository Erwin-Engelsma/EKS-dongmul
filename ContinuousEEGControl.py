# -*- coding: utf-8 -*-
"""
Created on Thu Mar 10 09:50:13 2022

@author: Erwin
"""


import brainaccess as ba
import numpy as np
from statistics import mean


class EEG():
    def __init__(self, channels = 2, accelChannels = 0, bufferTime = 125):
        self.sampleFreq = 125.0
        self.bufferTime = bufferTime
        self.eegStarted = False
        self.channel_numbers = [1, 2]
        self.bias_channel_numbers = [0]
        self.channels = channels
        self.accelChannels = accelChannels
        self.limitHigh = 1.0
    
    def setup(self, channels, accelChannels):
        self.channels = channels
        self.channel_numbers.clear()
        for index in range(self.channels):            
            self.channel_numbers.append(index)
        self.accelChannels = accelChannels
        response = ba.initialize()
        if response != 0:
            self.eegStarted = False
            print("error init BA \n")
            return False
        print("INFO: BrainAccess device is initialized")
        self.eegStarted = True
        ba.set_sampling_frequency(self.sampleFreq)
        ba.set_channels(self.channel_numbers, self.bias_channel_numbers)  # How to deal with accel channels?
 
        self.time = np.arange(0, self.bufferTime, 1.0/self.sampleFreq)
        self.data = np.zeros((len(self.channel_numbers), len(self.time)))
        self.lead_status = np.zeros((len(self.channel_numbers), len(self.time)))
        self.data_accel = np.zeros((3, len(self.time)))
        ba.set_preprocessing_sampling_frequency(self.sampleFreq)
        detrend = ba.DetrendSettings()  # will get default settings for detrender
        ba.set_detrend_settings(detrend)
        filt = ba.FilterSettings()
        filt.type = "bandpass"
        filt.order = 2
        filt.min_frequency = 1
        filt.max_frequency = 16
        ba.set_filter_settings([filt])
        self.data_processed = np.zeros((len(self.channel_numbers), len(self.time)))
        self.accel_data = np.zeros((self.accelChannels, len(self.time)))
 
        print("INFO: Setup is completed.")
        return True

    def acquireData(self):
        eeg_data = ba.get_data_from_now(int(len(self.time) * 1000 / self.sampleFreq))    #time in mSec to acquire data
        if eeg_data.connection_lost:
            print ("ERROR: EEG connection lost")
    
        if eeg_data.stream_disrupted:
            print ("ERROR: EEG datastream disrupted")
    
        if eeg_data.reading_is_too_slow:
            print("ERROR: EEG data reading too slow")
    
        # preprocess the eeg data
        for m in range(0, self.channels):
           self.data_processed[m] = ba.preprocess(eeg_data.measurements[m])           
           
        for m in range(self.accelChannels):                
            self.accel_data[m] = eeg_data.accelerometer_data[m]
            avg = mean(self.accel_data[m])  
            self.accel_data[m] = [x - avg for x in self.accel_data[m]]
  

    def run(self, running, requestNewData, newDataAvailable, newDataList, eegError):
        if not self.setup(self.channels, self.accelChannels):
            eegError.value = True
            running.value = True
        else:         
            self.eegStarted = True   
            if self.eegStarted:
                ba.start_acquisition()
                running.value = True
                while running.value:  
                    if requestNewData.value:  
                        requestNewData.value = False
                        self.acquireData()
                        for index in range(self.channels):
                            newDataList[index]  =  self.data_processed[index]
                        for index in range(self.accelChannels):                     
                            newDataList[self.channels + index] = self.accel_data[index]
                        newDataAvailable.value = True
                                                     
                ba.stop_acquisition()  

        

            