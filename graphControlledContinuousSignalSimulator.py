# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 09:27:32 2022

@author: Erwin     

"""
import wx
from wx.lib import plot as wxplot
from PyoControls import flexGraph
import serial
import time
import threading
import sys
import copy

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
        self.colours = [(200, 20, 20), (20, 200, 20),(20, 20, 200),(200, 200, 20) ,(200, 20, 200),(20, 200, 200),
                        (200, 200, 200),(20, 20, 20), (200, 70, 150), (150, 200, 90), (50, 70, 90), (50, 70, 90),(50, 70, 90)
                        ,(50, 70, 90),(50, 70, 90),(50, 70, 90),(50, 70, 90),(50, 70, 90),(50, 70, 90)]
        self.lineWidth = 3
        self.initGui()

        
    def initGui(self):
        rootSizer = wx.BoxSizer(wx.HORIZONTAL)
        panelSizer = wx.BoxSizer(wx.HORIZONTAL)
        labelSize = (100, 18)
        ctrlSize = (50, 18)
        textCtrlSize = (150, 18)
        self.panel = wxplot.PlotCanvas(self)
        axes_pen = wx.Pen(wx.BLUE, 1, wx.PENSTYLE_LONG_DASH)
        self.panel.axesPen = axes_pen  
        
        labelsSizer = wx.BoxSizer(wx.VERTICAL)
        self.comPortLabel = wx.StaticText(self, label = "Com Port: ", size = labelSize)     
        self.comSpeedLabel = wx.StaticText(self, label = "Com Speed: ", size = labelSize)
        self.inputEEGFileName = wx.StaticText(self, label = "Input FileName: ", size = labelSize)
        self.eegChannelsLabel = wx.StaticText(self, label = "EEG Channels: ", size = labelSize)        
        self.skipSamplesLabel = wx.StaticText(self, label = "Samples to Skip: ", size = labelSize)         
        self.outputTimeLabel = wx.StaticText(self, label = "Sample time (ms):", size = labelSize)     
        labelsSizer.Add(self.comPortLabel,  flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        labelsSizer.Add(self.comSpeedLabel,  flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        labelsSizer.Add(self.inputEEGFileName,  flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)       
        labelsSizer.Add(self.eegChannelsLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        labelsSizer.Add(self.skipSamplesLabel,  flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        labelsSizer.Add(self.outputTimeLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        
           
        controlsSizer = wx.BoxSizer(wx.VERTICAL)
        self.comPortCtrl = wx.TextCtrl(self,  value = '3', size = ctrlSize)   
        self.comSpeedCtrl = wx.TextCtrl(self,  value = '115200', size = ctrlSize)
        self.inputFileNameCtrl = wx.TextCtrl(self,  value = 'Arduinolog.csv', size = textCtrlSize)
        self.eegChannelsCtrl = wx.TextCtrl(self,  value = '3', size = ctrlSize)         
        self.skipSamplesCtrl = wx.TextCtrl(self,  value = '10', size = ctrlSize)        
        self.outputTimeCtrl = wx.TextCtrl(self,  value = '1500', size = ctrlSize)   
        controlsSizer.Add(self.comPortCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        controlsSizer.Add(self.comSpeedCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        controlsSizer.Add(self.inputFileNameCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)        
        controlsSizer.Add(self.eegChannelsCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        controlsSizer.Add(self.skipSamplesCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        controlsSizer.Add(self.outputTimeCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
               
        self.startArduinoButton = wx.Button(self, -1, 'Start Arduino',  name='startButton')
        self.startArduinoButton.Bind(wx.EVT_BUTTON, self.startArduino)
        self.startEEGButton = wx.Button(self, -1, 'Start EEG',  name='startButton')
        self.startEEGButton.Disable()
        self.startEEGButton.Bind(wx.EVT_BUTTON, self.startEEG)
        self.startOutButton = wx.Button(self, -1, 'Start Output',  name='startOutButton')
        self.startOutButton.Disable()
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
        
        panelSizer.Add(rootSizer)
        panelSizer.Add(self.panel, 1, wx.EXPAND | wx.ALL, 10)    

        self.SetSizer(panelSizer)    
        
        #self.SetSizer(rootSizer)

    def stopProgram(self, event):
        self.programRunning = False
        if self.arduinoInit:
            self.arduino.close()
        
        sys.exit()
        
    def startEEG(self, event):
        if self.inputFileNameCtrl.Value == "None":
            self.createGraphList(int(self.eegChannelsCtrl.Value))
        else: 
            self.inputGraphList()

        self.graphBuffer = []
        for index in range(len(self.theValues)):
            self.graphBuffer.append(copy.deepcopy(self.theValues[index]))
        self.graphIndex = 0        
        self.startEEGButton.Disable()
        self.startOutButton.Enable()
        self.eegChannelsCtrl.Disable()


    def startOutput(self, event):            
        self.startOutButton.Disable()
        self.sendValues()
        
    def sendValues(self):
        if self.programRunning:
          if self.outputTimeCtrl.Value:
              waitTime = int(self.outputTimeCtrl.Value) * 0.001   
          else:
              waitTime = 0.5
          threading.Timer(waitTime, self.sendValues).start()
          self.sendDataToArduino(waitTime)
          self.fillBuffer()
          
    def fillBuffer(self):  
          if len(self.theValues[0]) < 2:
              if self.inputFileNameCtrl.Value == "None":
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
              else:
                  self.theValues = copy.deepcopy(self.theValuesSource)
              
    def sendDataToArduino(self, waitTime):
          graphValues = []
          if len(self.theValues[0]) > 0:
              arduinoMessage = []
              freString = ''
              arduinoMessage.append(1000 * waitTime)
              arduinoMessage.append(float(self.channels))
              for index in range(self.channels):  
                  thisValue = 100 * self.theValues[index].pop()   # Send a percentage!
                  arduinoMessage.append(thisValue)
                  graphValues.append(thisValue)
                
              for thisElement in arduinoMessage:
                    freString += '{: .1f}'.format(thisElement) 
                    freString += ";"
              print (freString)              
              self.arduino.write(freString.encode())
              
              
              for index in range(len(self.graphBuffer)): 
                  self.graphBuffer[index][self.graphIndex] = graphValues[index] 
              self.graphIndex += 1
              if self.graphIndex >= (len(self.graphBuffer[0]) - 1):
                  self.graphIndex = 0
              self.plotFromGraphBuffer()
              
          else:
              print("Error theValues is empty")      
      
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
            self.theValues.append(self.graphList[index].getAllPoints(0, 124, int(self.skipSamplesCtrl.Value))) 

    def inputGraphList(self, theSize = (300, 250), graphsOnX = 4 ):
        self.theSize = theSize
        self.graphsOnX = graphsOnX  
        self.theValuesSource = []
        inFileName = self.inputFileNameCtrl.Value
        if ".csv" not in inFileName:
            inFileName += ".csv"
        inFile = open(inFileName)    
        inputLine = inFile.readline()
        theList = self.textToFloatList(inputLine)       
        waitTimeInput = inputLine.split(";")
        self.outputTimeCtrl.Value = waitTimeInput[0]
        self.channels = int(theList[1])
        for thisChannel in range(self.channels):
            self.theValuesSource.append([theList[thisChannel+2]]) 
        inputLine = inFile.readline()        
        while inputLine:
            theList = self.textToFloatList(inputLine)               
            for thisChannel in range(self.channels):
                self.theValuesSource[thisChannel].append(theList[thisChannel+2])
            inputLine = inFile.readline()       
        inFile.close()    
        self.theValues = copy.deepcopy(self.theValuesSource)
            
    def textToFloatList(self, text):
        x = text.split(";")
        floatList = []
        floatList.append(float(x[0]))
        floatList.append(float(x[1]))
        stopCrit = floatList[1] + 2
        for theCounter in range(2, int(stopCrit )):
            floatList.append(float(x[theCounter]))
        
        return floatList
    
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
        self.startEEGButton.Enable()
        self.arduinoInit = True
        
    def plotFromGraphBuffer(self):
        lines = []
        index = 0
        self.x_data = []
        for xIndex in range(len(self.graphBuffer[0]) - 1):
            self.x_data.append(xIndex)
        for theLine in self.graphBuffer:           
            xy_data = list(zip(self.x_data, theLine))
            lines.append(wxplot.PolySpline(xy_data, colour=wx.Colour(self.colours[index]), width=self.lineWidth,))  
            index += 1 
        
        graphics = wxplot.PlotGraphics(lines)
        self.panel.Draw(graphics)   

if __name__ == '__main__':        
    app = wx.App()   
    mfbaseTitle = 'Pyo EEG Simulator GUI '
    mainFrame = CSSGui(None, title= mfbaseTitle , size = (1400, 800))
    mainFrame.Show()       
    app.MainLoop()
    
    
    
    
    
    
    
    
    
    