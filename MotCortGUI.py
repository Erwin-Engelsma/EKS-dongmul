# -*- coding: utf-8 -*-
"""
Created on Mon Mar  7 20:30:03 2022
A

@author: Erwin
"""
import tkinter as tk
from tkinter import ttk

import multiprocessing as mp
from MotCortArduinoControl import Arduino 
from MotCortEEGControl import EEG
#from time import sleep  
import time  
        
class mprocExample(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.num = mp.Value('d', 0.0)
        #self.arr = mp.Array('i', range(10)) 
        self.eegStatus = mp.Value('i', 0)
        self.excitement = mp.Value('d', 0.0)
        self.curiosity = mp.Value('d', 0.5)
        self.curiosityScaler = mp.Value('d', 1.0)
        self.excitementScaler = mp.Value('d', 2200.0)
        self.freqScaler = mp.Value('d', 1.0 / 28.0)
        self.algorithmSel = mp.Value('i', 0)
        self.negVolumeScaler = mp.Value('d', 0.032)
        self.posVolumeScaler  = mp.Value('d', 0.1)
        self.ArduinoCommand = mp.Value('i', -1)
        self.ArduinoRunning = False
        self.eegRunning = False
        self.exciteInit = 0.5
        self.updateTime = 0.5
        self.finish = mp.Value('i', 0)
        self.curioSliderMin = 1
        self.curioSliderMax = 30     
        self.excitementSliderMin = 100          
        self.excitementSliderMax = 100000              
        self.freqScaleSliderMin =  1.0      
        self.freqScaleSliderMax =  40  
        self.curiosityCorrelationInit = 10.0
        self.excitementCorrelationInit= 2300.0
        self.freqCorrelationInit= 1.0
        self.curiosityFourierInit = 150.0
        self.excitementFourierInit= 50
        self.freqFourierInit= 28        
    
        self.initGui()
        
    def initGui(self):
        """
        Overview panel
        """
        self.title("Motor Cortex Control")
        self.geometry("1200x600")
        self.resizable(width = True, height = True)
        self.attributes("-topmost", True) 
        self.stopButton = tk.Button(self, text="Stop", command = self.stopRun)
        self.stopButton.grid(column = 0, row = 20, sticky = 'we') 
        self.calibrateButton = tk.Button(self, text="Calibrate", command = self.calibrateArduino)
        self.calibrateButton.grid(column = 0, row = 16, sticky = 'we')         
        self.resetButton = tk.Button(self, text="Reset", command = self.resetArduino)
        self.resetButton.grid(column = 0, row = 17, sticky = 'we')         
        
        self.excitementBar = ttk.Progressbar(self, orient='vertical', length=300, mode='determinate', maximum = 1)
        self.excitementBar['value'] = self.exciteInit
        self.excitementBar.grid(column = 0, row = 5, sticky='we')
        self.excitement_label = tk.Label(self, text="Excitement level", width=20, height=2)
        self.excitement_label.grid(column = 0, row = 0, sticky='n')
        
         
        self.exciteScaler_label = tk.Label(self, text="Surface Divider", width=20, height=2)
        self.exciteScaler_label.grid(column = 3, row = 0, sticky='n')
        self.curiosScaler_label = tk.Label(self, text="Correlation Multiple 0.1", width=20, height=2)
        self.curiosScaler_label.grid(column = 2, row = 0, sticky='n')
        self.freqScaler_label = tk.Label(self, text="Not used", width=20, height=2)
        self.freqScaler_label.grid(column = 4, row = 0, sticky='n')
        
        self.curiosityBar = ttk.Progressbar(self, orient='vertical', length=300, mode='determinate', maximum = 1)
        self.curiosityBar['value'] = self.exciteInit
        self.curiosityBar.grid(column = 1, row = 5, sticky='we')
        self.curiosity_label = tk.Label(self, text = "Curiosity level", width=20, height=2)
        self.curiosity_label.grid(column = 1, row = 0,   sticky='n') 

        self.curiositySlider = tk.Scale(self, from_=  self.curioSliderMin, to =  self.curioSliderMax, orient = "vertical", length = 300, sliderlength = 20)
        self.curiositySlider.bind("<ButtonRelease-1>", self.updateCalibSliderValue)
        self.curiositySlider.set(10)
        self.curiositySlider.grid(column = 2, row = 5, sticky = 'n')           
        
        self.excitementSlider = tk.Scale(self, from_= self.excitementSliderMin, to = self.excitementSliderMax, orient="vertical", length = 300, sliderlength = 20)
        self.excitementSlider.bind("<ButtonRelease-1>", self.updateexcitementSliderValue)
        self.excitementSlider.set(2300)
        self.excitementSlider.grid(column = 3, row = 5, sticky = 'n') 
        
        self.freqScaleSlider = tk.Scale(self, from_= self.freqScaleSliderMin, to = self.freqScaleSliderMax, orient="vertical", length = 300, sliderlength = 20)
        self.freqScaleSlider.bind("<ButtonRelease-1>", self.updatefreqScaleSliderValue)
        self.freqScaleSlider.set(28)
        self.freqScaleSlider.grid(column = 4, row = 5, sticky = 'n') 
        
        """
            Arduino GUI settings
        """
        self.startArduinoButton = tk.Button(self, text="Start Arduino", command = self.startArduino)
        self.startArduinoButton.grid(column = 0, row = 10, sticky = 'we') 
        self.portLabel =tk.Label(self, text = "Port nbr")
        self.portLabel.grid(column = 1, row = 10, sticky ='nwe')
        self.portEntry =  tk.Entry(self)
        self.portEntry.grid(column = 2, row = 10, sticky ='nwe')
        self.portEntry.insert( -1, "4")
        self.speedLabel = tk.Label(self, text = "Serial Speed")
        self.speedLabel.grid(column = 1, row = 15, sticky ='nwe')
        self.speedEntry =  tk.Entry(self)
        self.speedEntry.grid(column = 2, row = 15, sticky ='nwe')
        self.speedEntry.insert(-1, "115200")
        self.posVolume_label = tk.Label(self, text="pos volume", width=20, height=2)
        self.posVolume_label.grid(column = 5, row = 0, sticky='n')
        self.posVolumeSlider = tk.Scale(self, from_= 80.0, to = 1, orient="vertical", digits = 3, resolution = 0.01, length = 300, sliderlength = 20)
        self.posVolumeSlider.bind("<ButtonRelease-1>", self.updatePosVolSliderValue)
        self.posVolumeSlider.set(32.0)
        self.posVolumeSlider.grid(column = 5, row = 5, sticky = 'n') 
        self.negVolume_label = tk.Label(self, text="neg volume", width=20, height=2)
        self.negVolume_label.grid(column = 6, row = 0, sticky='n')
        self.negVolumeSlider = tk.Scale(self, from_= 100.0, to = 1, orient="vertical", digits = 3, resolution = 0.01, length = 300, sliderlength = 20)
        self.negVolumeSlider.bind("<ButtonRelease-1>", self.updateNegVolSliderValue)
        self.negVolumeSlider.set(100.0)
        self.negVolumeSlider.grid(column = 6, row = 5, sticky = 'n')
        self.message_label = tk.Label(self)
        self.message_label.grid(column = 0 , row = 25)
        
        """ 
        EEG settings
        """
        self.startEEGButton = tk.Button(self, text="Start EEG", command = self.startEEG)
        self.startEEGButton.grid(column = 0, row = 15, sticky = 'we')  
        self.selectedAlgorithm= tk.StringVar()   
        self.algoSelectorCombo= ttk.Combobox(self, textvariable= self.selectedAlgorithm)         
        self.algoSelectorCombo['values']= ('Weight', 'Fourier')   
        self.algoSelectorCombo.current(1)
        self.algoSelectorCombo.grid(column = 1, row = 20, sticky ='nwe')   
        self.algoSelectorCombo.bind('<<ComboboxSelected>>', self.algoChanged)  
        self.update()   

    def updatefreqScaleSliderValue(self, event):
        self.freqScaler.value = 1.0 / self.freqScaleSlider.get()
             
    def updateCalibSliderValue(self, event):
        self.curiosityScaler.value =  self.curiositySlider.get()

    def updateexcitementSliderValue(self, event):
        self.excitementScaler.value = self.excitementSlider.get()
        
    def updateNegVolSliderValue(self, event):
        self.negVolumeScaler.value = self.negVolumeSlider.get() / 1000       

    def updatePosVolSliderValue(self, event):
        self.posVolumeScaler.value = self.posVolumeSlider.get() / 1000 

    def algoChanged (self, event):
       if int(self.algoSelectorCombo.current()) == 0:
           self.exciteScaler_label.configure(text="Surface Divider")    
           self.curiosScaler_label.configure(text="Correlation Multiple 0.1")
           self.freqScaler_label.configure(text="Not Used")
           self.curiositySlider.configure(from_= self.curioSliderMin)            
           self.curiositySlider.configure(to= self.curioSliderMax)
           self.excitementSlider.configure(from_= self.excitementSliderMin)            
           self.excitementSlider.configure(to = self.excitementSliderMax)                       
           self.freqScaleSlider.configure(from_= self.freqScaleSliderMin)            
           self.freqScaleSlider.configure(to= self.freqScaleSliderMax) 
           self.excitementSlider.set(self.excitementCorrelationInit)   
           self.curiositySlider.set(self.curiosityCorrelationInit)
           self.freqScaleSlider.set(self.freqCorrelationInit)           

       if int(self.algoSelectorCombo.current()) == 1:           
           self.exciteScaler_label.configure(text="Excitement Threshold")
           self.curiosScaler_label.configure(text="Curiosity Threshold")  
           self.freqScaler_label.configure(text="Freq Scaling")
           self.curiositySlider.configure(from_= 10)            
           self.curiositySlider.configure(to = 500)  
           self.excitementSlider.configure(from_= 10)            
           self.excitementSlider.configure(to = 500)                       
           self.freqScaleSlider.configure(from_= 2)            
           self.freqScaleSlider.configure(to= 40)  
           self.excitementSlider.set(self.excitementFourierInit)   
           self.curiositySlider.set(self.curiosityFourierInit)
           self.freqScaleSlider.set(self.freqFourierInit)            
           
           
    def stopRun(self) :
        self.finish.value = 1
        print ("finished it")

    def run(self, *args): 
        lastTime = time.time()
        while self.finish.value == 0:  
            self.algorithmSel.value = int(self.algoSelectorCombo.current())
            if (time.time() - lastTime > self.updateTime) and (self.ArduinoCommand.value == -1):
                if self.eegRunning:
                    print ("Curiosity: " + str(self.curiosity.value))
                    print ("Excitement: " + str(self.excitement.value))
                    print ("Algorithm: " + str(self.algorithmSel.value))
                    self.excitementBar['value'] = self.excitement.value
                    self.curiosityBar['value'] = self.curiosity.value 
                    self.ArduinoCommand.value = 0;
                else:
                    print("Waiting for acq to start")
                lastTime = time.time()                
            self.update()  
        
        if self.finish.value == 2:
            print ("eeg Status error: " + self.eegStatus.value)
            
        if self.finish.value == 3:
            print ("EEG never started")
        
        if self.ArduinoRunning:
            self.ArduinoRunning = False
            self.ardProc.join()
        if self.eegRunning:
            self.eegRunning = False
            self.eegProc.join()
            
        print("Program finished \n")
        self.destroy()

    def calibrateArduino(self):
        self.ArduinoCommand.value = 1
        
    def resetArduino(self):
        self.ArduinoCommand.value = 2

    def startEEG(self):  
        if not self.eegRunning:
            self.theEEG = EEG()
            self.eegProc = mp.Process(target=self.theEEG.run, args=(self.excitement, self.curiosity, self.finish,
                                        self.eegStatus, self.excitementScaler, self.curiosityScaler, self.freqScaler,  
                                        self.algorithmSel))
            self.eegProc.start() 
            self.eegRunning = True                                                                                                  
 
    def startArduino(self):
        if not self.ArduinoRunning:
            comPort = int(self.portEntry.get())
            speed = int(self.speedEntry.get())
            self.theArduino = Arduino(comPort, speed)
            self.ArduinoRunning = True
            self.ardProc = mp.Process(target=self.theArduino.run, args=(self.excitement, self.curiosity, self.finish,
                                             self.negVolumeScaler, self.posVolumeScaler, self.ArduinoCommand))
            self.ardProc.start()    


if __name__ == '__main__':
    app = mprocExample()
    app.run()