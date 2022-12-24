# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 09:27:32 2022

@author: Erwin     

"""
import wx
from PyoControls import flexGraph
import serial
import time
import threading
import sys

BORDERSIZE = 2

class CSSGui(wx.Frame):
    def __init__(self, *a, **k):
        wx.Frame.__init__(self, *a, **k)
        pyoGUI(self)        
        
class pyoGUI(wx.Panel):   
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.graphList = []
        self.theValues = []
        self.programRunning = True
        self.arduinoInit = False
        self.initGui()

        
    def initGui(self):
        rootSizer = wx.BoxSizer(wx.HORIZONTAL)
        labelSize = (100, 18)
        ctrlSize = (50, 18)
        
        labelsSizer = wx.BoxSizer(wx.VERTICAL)
        self.comPortLabel = wx.StaticText(self, label = "Com Port: ", size = labelSize)     
        self.comSpeedLabel = wx.StaticText(self, label = "Com Speed: ", size = labelSize)
        self.eegChannelsLabel = wx.StaticText(self, label = "EEG Channels: ", size = labelSize)        
        self.skipSamplesLabel = wx.StaticText(self, label = "Samples to Skip: ", size = labelSize)         
        self.outputTimeLabel = wx.StaticText(self, label = "Sample time (ms):", size = labelSize)     
        labelsSizer.Add(self.comPortLabel,  flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        labelsSizer.Add(self.comSpeedLabel,  flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        labelsSizer.Add(self.eegChannelsLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        labelsSizer.Add(self.skipSamplesLabel,  flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        labelsSizer.Add(self.outputTimeLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        
           
        controlsSizer = wx.BoxSizer(wx.VERTICAL)
        self.comPortCtrl = wx.TextCtrl(self,  value = '4', size = ctrlSize)   
        self.comSpeedCtrl = wx.TextCtrl(self,  value = '115200', size = ctrlSize)
        self.eegChannelsCtrl = wx.TextCtrl(self,  value = '3', size = ctrlSize)         
        self.skipSamplesCtrl = wx.TextCtrl(self,  value = '10', size = ctrlSize)        
        self.outputTimeCtrl = wx.TextCtrl(self,  value = '1500', size = ctrlSize)   
        controlsSizer.Add(self.comPortCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        controlsSizer.Add(self.comSpeedCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        controlsSizer.Add(self.eegChannelsCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        controlsSizer.Add(self.skipSamplesCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        controlsSizer.Add(self.outputTimeCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
               
        self.startArduinoButton = wx.Button(self, -1, 'Start Arduino',  name='startButton')
        self.startArduinoButton.Bind(wx.EVT_BUTTON, self.startArduino)
        self.startEEGButton = wx.Button(self, -1, 'Start EEG',  name='startButton')
        self.startEEGButton.Bind(wx.EVT_BUTTON, self.startEEG)
        self.startOutButton = wx.Button(self, -1, 'Start Output',  name='startOutButton')
        self.startOutButton.Bind(wx.EVT_BUTTON, self.startOutput)  
        self.stopButton = wx.Button(self, -1, 'Stop',  name='stop')
        self.stopButton.Bind(wx.EVT_BUTTON, self.stopProgram) 
        buttonsSizer = wx.BoxSizer(wx.VERTICAL)
        buttonsSizer.Add(self.startArduinoButton, border=BORDERSIZE)
        buttonsSizer.Add(self.startEEGButton, border=BORDERSIZE)
        buttonsSizer.Add(self.startOutButton, border=BORDERSIZE) 
        buttonsSizer.Add(self.stopButton, border=BORDERSIZE)  
        self.startOutButton.Disable()
        rootSizer.Add(labelsSizer)
        rootSizer.Add(controlsSizer)
        rootSizer.Add(buttonsSizer)
        self.SetSizer(rootSizer)

    def stopProgram(self, event):
        self.programRunning = False
        if self.arduinoInit:
            self.arduino.close()
        
        sys.exit()
        
    def startEEG(self, event):
        self.createGraphList(int(self.eegChannelsCtrl.Value))
        self.startEEGButton.Disable()
        self.startOutButton.Enable()
        self.eegChannelsCtrl.Disable()


    def startOutput(self, event):   
        for index in range(self.channels):
            self.theValues.append(self.graphList[index].getAllPoints(0, 124, int(self.skipSamplesCtrl.Value)))        
        self.startOutButton.Disable()
        self.sendValues()
        
    def sendValues(self):
        if self.programRunning:
          if self.outputTimeCtrl.Value:
              waitTime = int(self.outputTimeCtrl.Value) * 0.001   
          else:
              waitTime = 0.5
          threading.Timer(waitTime, self.sendValues).start()
          arduinoMessage = []
          freString = ''
          arduinoMessage.append(1000 * waitTime)
          arduinoMessage.append(float(self.channels))
          if len(self.theValues[0]) > 0:
              for index in range(self.channels):  
                  thisValue = 100 * self.theValues[index].pop()   # Send a percentage!
                  arduinoMessage.append(thisValue)
                
              for thisElement in arduinoMessage:
                    freString += '{: .1f}'.format(thisElement) 
                    freString += ";"
              print (freString)
              
              self.arduino.write(freString.encode())
          else:
              print("Error theValues is empty")
      
        if len(self.theValues[0]) < 2:
          nextBuffer = []
          skipStr = self.skipSamplesCtrl.Value
          if skipStr.strip():
              skipValue = int(skipStr)
          else:
              skipValue = 5   
          for index in range(self.channels):
              nextBuffer.clear()
              nextBuffer = self.graphList[index].getAllPoints(0, 124, skipValue)
              for number in nextBuffer:
                  self.theValues[index].append(number)
      
    def createGraphList(self, channels, theSize = (300, 250), graphsOnX = 4 ):
        self.channels = channels   
        self.theSize = theSize
        self.graphsOnX = graphsOnX
        
        thePositions = []             
        for pos in range(channels):
            xpos = theSize[0] * (pos % self.graphsOnX) + 10
            ypos = theSize[1] * int(pos / self.graphsOnX) + 10
            thePositions.append((xpos, ypos))
        for index in range(channels):
            self.graphList.append(flexGraph( str(index), index, self.graphNoAction, position = thePositions[index],  size = theSize, elements = 125, vertRange = (0.0, 1.0)))  #       
            self.graphList[index].setValues([(0,0), (60, 0.8), (124, 0)])
        
            
    def graphNoAction(self, data):
        pass
    
    
    def startArduino(self, event):        
        thePort = "COM" + self.comPortCtrl.Value
        theSpeed = self.comSpeedCtrl.Value
        #self.logFile = open("Arduinolog.txt", "w")
        try:
            self.arduino = serial.Serial(thePort, theSpeed)          
            response = str(self.arduino.read().decode())
            startTime = time.time()
            while not 'i' in response:
                response = str(self.arduino.read().decode())                
                if (time.time() - startTime) > 5:
                    self.timeOut = True
                    break
            self.arduino.flush()  # make sure buffer is emptied. There may be noise on the line due to USB connection
            print("Contact Arduino established")
        except Exception as e:
            print ("Something wrong in Arduino Setup: ")
            print(e) 
        self.startArduinoButton.Disable()
        self.comPortCtrl.Disable()
        self.comSpeedCtrl.Disable()
        self.arduinoInit = True

if __name__ == '__main__':        
    app = wx.App()   
    mfbaseTitle = 'Pyo Modulation Controller GUI '
    mainFrame = CSSGui(None, title= mfbaseTitle , size = (400, 250))
    mainFrame.Show()       
    app.MainLoop()
    
    
    
    
    
    
    
    
    
    