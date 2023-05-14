# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 09:27:32 2022

@author: Erwin     

"""
import wx
from wx.lib import plot as wxplot
from ContinuousEEGControl import EEG
from multiprocessing import Process, Manager, Value
import serial
import time
import threading
import sys
import copy

BORDERSIZE = 2

class CSSGui(wx.Frame):
    def __init__(self, *a, **k):     
        wx.Frame.__init__(self, *a, **k)
        mainGUI(self)        
        
class mainGUI(wx.Panel):   
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.eegRunning = False
        self.theValues = []
        self.programRunning = True
        self.arduinoInit = False
        self.manager =  Manager() 
        self.newDataList = self.manager.list()
        self.running = Value('b', False)
        self.requestNewData = Value('b', False)
        self.newDataAvailable = Value('b', False)
        self.eegError = Value('b', False)
        self.colours = [(200, 20, 20), (20, 200, 20),(20, 20, 200),(200, 200, 20) ,(200, 20, 200),(20, 200, 200),
                        (200, 200, 200),(20, 20, 20), (200, 70, 150), (150, 200, 90), (50, 70, 90), (50, 70, 90),(50, 70, 90)
                        ,(50, 70, 90),(50, 70, 90),(50, 70, 90),(50, 70, 90),(50, 70, 90),(50, 70, 90)]
        self.eegScaler = 100
        self.skipSamples = 2
        self.waitTime = 0.150
        self.lineWidth = 3
        self.logResults = False
        self.initGui()
        self.Bind(wx.EVT_MENU, self.onExit, id=3)
      
               
    def initGui(self):
        panelSizer = wx.BoxSizer(wx.HORIZONTAL)
        menuSizer = wx.BoxSizer(wx.HORIZONTAL)
        labelSize = (160, 22)
        messageSize = (346, 66)
        ctrlSize = (80, 22)
        buttonSize = (90, 23)
        self.panel = wxplot.PlotCanvas(self)
        axes_pen = wx.Pen(wx.BLUE, 1, wx.PENSTYLE_LONG_DASH)
        self.panel.axesPen = axes_pen        
        labelsSizer = wx.BoxSizer(wx.VERTICAL)

        self.comPortLabel = wx.StaticText(self, label = "Com Port: ", size = labelSize)     
        self.comSpeedLabel = wx.StaticText(self, label = "Com Speed: ", size = labelSize)
        self.eegChannelsLabel = wx.StaticText(self, label = "EEG Channels: ", size = labelSize)   
        self.accelChannelsLabel = wx.StaticText(self, label = "Accelerator Channels: ", size = labelSize)   
        self.skipSamplesLabel = wx.StaticText(self, label = "Decimation factor: ", size = labelSize)         
        self.outputTimeLabel = wx.StaticText(self, label = "Sample out time (ms):", size = labelSize) 
        self.getNewDataLabel = wx.StaticText(self, label = "Get new data at sample:", size = labelSize)
        self.eegScalerLabel = wx.StaticText(self, label = "Full Scale EEG Value:", size = labelSize)
        self.accelScalerLabel = wx.StaticText(self, label = "Accel scaler :", size = labelSize)
        self.colorChannelLabel = wx.StaticText(self, label = "Colour channel: ", size = labelSize)
        self.redValueLabel = wx.StaticText(self, label = "Red Value :", size = labelSize)
        self.greenValueLabel = wx.StaticText(self, label = "Green Value :", size = labelSize)
        self.blueValueLabel = wx.StaticText(self, label = "Blue Value :", size = labelSize)


        self.inputSampleTimeLabel = wx.StaticText(self, label = "Input Sampling Time (Sec):", size = labelSize)
        self.lineWidthLabel = wx.StaticText(self, label = "Set Line width (pixels):", size = labelSize)
        self.logFileNameLabel = wx.StaticText(self, label = "Log file name:", size = labelSize)
        
        labelsSizer.Add(self.comPortLabel,  flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        labelsSizer.Add(self.comSpeedLabel,  flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        labelsSizer.Add(self.inputSampleTimeLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)        
        labelsSizer.Add(self.eegChannelsLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        labelsSizer.Add(self.accelChannelsLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        labelsSizer.Add(self.skipSamplesLabel,  flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        labelsSizer.Add(self.outputTimeLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        labelsSizer.Add(self.getNewDataLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        labelsSizer.Add(self.eegScalerLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        labelsSizer.Add(self.accelScalerLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE) 
        labelsSizer.Add(self.colorChannelLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE) 
        labelsSizer.Add(self.redValueLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE) 
        labelsSizer.Add(self.greenValueLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE) 
        labelsSizer.Add(self.blueValueLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE) 
        labelsSizer.Add(self.lineWidthLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE) 
        labelsSizer.Add(self.logFileNameLabel, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE) 


        controlsSizer = wx.BoxSizer(wx.VERTICAL)
        self.comPortCtrl = wx.TextCtrl(self,  value = '4', size = ctrlSize)   
        self.comSpeedCtrl = wx.TextCtrl(self,  value = '115200', size = ctrlSize)
        self.eegChannelsCtrl = wx.TextCtrl(self,  value = '3', size = ctrlSize) 
        self.accelChannelsCtrl = wx.TextCtrl(self,  value = '3', size = ctrlSize) 
        self.skipSamplesCtrl = wx.TextCtrl(self,  value = '5', size = ctrlSize, style=wx.TE_PROCESS_ENTER)        
        self.outputTimeCtrl = wx.TextCtrl(self,  value = '150', size = ctrlSize, style=wx.TE_PROCESS_ENTER )   
        self.getNewDataCtrl = wx.TextCtrl(self,  value = '3', size = ctrlSize)
        self.eegScalerCtrl = wx.TextCtrl(self,  value = '100', size = ctrlSize, style=wx.TE_PROCESS_ENTER)
        self.accelScalerCtrl = wx.TextCtrl(self,  value = '160', size = ctrlSize)
        self.inSampleCtrl = wx.TextCtrl(self,  value = '0.5', size = ctrlSize)
        self.colorChannelCtrl = wx.TextCtrl(self,  value = '0', size = ctrlSize, style=wx.TE_PROCESS_ENTER)
        self.redValueCtrl = wx.TextCtrl(self,  value = '100', size = ctrlSize, style=wx.TE_PROCESS_ENTER)
        self.greenValueCtrl = wx.TextCtrl(self,  value = '100', size = ctrlSize, style=wx.TE_PROCESS_ENTER)
        self.blueValueCtrl = wx.TextCtrl(self,  value = '100', size = ctrlSize, style=wx.TE_PROCESS_ENTER)       
        self.lineWidthCtrl = wx.TextCtrl(self,  value = '3', size = ctrlSize, style=wx.TE_PROCESS_ENTER) 
        self.logFileNameCtrl = wx.TextCtrl(self,  value = 'logFile', size = ctrlSize) 
        controlsSizer.Add(self.comPortCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        controlsSizer.Add(self.comSpeedCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        controlsSizer.Add(self.inSampleCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)         
        controlsSizer.Add(self.eegChannelsCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        controlsSizer.Add(self.accelChannelsCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        controlsSizer.Add(self.skipSamplesCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        controlsSizer.Add(self.outputTimeCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)
        controlsSizer.Add(self.getNewDataCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)       
        controlsSizer.Add(self.eegScalerCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)  
        controlsSizer.Add(self.accelScalerCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE)  
        controlsSizer.Add(self.colorChannelCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE) 
        controlsSizer.Add(self.redValueCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE) 
        controlsSizer.Add(self.greenValueCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE) 
        controlsSizer.Add(self.blueValueCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE) 
        controlsSizer.Add(self.lineWidthCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE) 
        controlsSizer.Add(self.logFileNameCtrl, flag=wx.EXPAND|wx.ALL, border=BORDERSIZE) 
        
        self.startArduinoButton = wx.Button(self, -1, 'Start Arduino',  name='startButton', size = buttonSize)
        self.startArduinoButton.Bind(wx.EVT_BUTTON, self.startArduino)
        self.startEEGButton = wx.Button(self, -1, 'Start EEG',  name='startButton', size = buttonSize)
        self.startEEGButton.Bind(wx.EVT_BUTTON, self.startEEG)
        self.startOutButton = wx.Button(self, -1, 'Start Output',  name='startOutButton', size = buttonSize)
        self.startOutButton.Bind(wx.EVT_BUTTON, self.startOutput)  
        self.startLogButton = wx.Button(self, -1, 'Start Logging',  name='startLogButton', size = buttonSize)
        self.startLogButton.Bind(wx.EVT_BUTTON, self.switchLogging)         
        self.stopButton = wx.Button(self, -1, 'Stop',  name='stop', size = buttonSize)
        self.stopButton.Bind(wx.EVT_BUTTON, self.stopProgram)   
        self.colorChannelCtrl.Bind(wx.EVT_TEXT_ENTER, self.displayColors)
        self.redValueCtrl.Bind(wx.EVT_TEXT_ENTER, self.changeLineColor)
        self.greenValueCtrl.Bind(wx.EVT_TEXT_ENTER, self.changeLineColor)        
        self.blueValueCtrl.Bind(wx.EVT_TEXT_ENTER, self.changeLineColor)    
        self.eegScalerCtrl.Bind(wx.EVT_TEXT_ENTER, self.setEEGScaler)
        self.skipSamplesCtrl.Bind(wx.EVT_TEXT_ENTER, self.setSkipSamples)
        self.outputTimeCtrl.Bind(wx.EVT_TEXT_ENTER, self.setOutputTime)
        self.lineWidthCtrl.Bind(wx.EVT_TEXT_ENTER, self.setLineWidth)
        buttonsSizer = wx.BoxSizer(wx.VERTICAL)
        buttonsSizer.Add(self.startArduinoButton, flag=wx.EXPAND|wx.ALL,border=BORDERSIZE)    #wx.EXPAND|wx.TOP|wx.BOTTOM, 5
        buttonsSizer.Add(self.startEEGButton, flag=wx.EXPAND|wx.TOP, border = 28)
        buttonsSizer.Add(self.startOutButton, flag=wx.EXPAND|wx.ALL,border=BORDERSIZE) 
        buttonsSizer.Add(self.startLogButton, flag=wx.EXPAND|wx.TOP,border = 287)          
        buttonsSizer.Add(self.stopButton, flag=wx.EXPAND|wx.BOTTOM|wx.TOP, border = 10)  
        self.startEEGButton.Disable()
        self.startOutButton.Disable()
  
        menuSizer.Add(labelsSizer)
        menuSizer.Add(controlsSizer)
        menuSizer.Add(buttonsSizer)

        self.messageLabel = wx.StaticText(self, label = "Message area ", size = messageSize)        
        #self.Bind(wx.EVT_MENU, self.OnMax, id=1)
        #self.Bind(wx.EVT_MENU, self.OnMin, id=2)
        self.Bind(wx.EVT_MENU, self.onExit, id=3)
        boldFont = wx.Font(10, wx.DECORATIVE, wx.BOLD, wx.NORMAL)
        self.messageLabel.SetFont(boldFont)  
        self.messageLabel.SetBackgroundColour((230, 230, 230))
        messageSizer =  wx.BoxSizer(wx.VERTICAL)
        messageSizer.Add(menuSizer)
        messageSizer.Add(self.messageLabel)

        panelSizer.Add(messageSizer)
        panelSizer.Add(self.panel, 1, wx.EXPAND | wx.ALL, 10)    

        self.SetSizer(panelSizer)         
        
    def onExit(self, event):
        self.stopProgram()      
        
    def setOutputTime(self, event):
        if self.outputTimeCtrl.Value:
              self.waitTime = int(self.outputTimeCtrl.Value) * 0.001 
              if self.waitTime < 0.001:
                  self.displayMessage(" Warning sample delay set to minimum 10 mSec")
                  self.waitTime = 0.001
        else:
              self.waitTime = 0.1

    def switchLogging(self, event):
        if not self.logResults:
            self.startLogButton.SetLabel("Stop log")
            logFileName = self.logFileNameCtrl.Value
            if not ".csv" in logFileName:
                logFileName += ".csv"
            self.logFile = open(logFileName, "w")
            self.logResults = True
        else:
            self.startLogButton.SetLabel("Start log")
            self.logResults = False
            self.logFile.close()           
    
    def displayMessage(self, message):
        self.messageLabel.SetLabel(message)

    def displayColors(self, event):
        channel = int(self.colorChannelCtrl.Value)
        if channel < 0 or channel > len(self.colours):
            channel = 0  
        rgb = self.colours[channel]
        self.redValueCtrl.Value = str(rgb[0])
        self.greenValueCtrl.Value = str(rgb[1])
        self.blueValueCtrl.Value = str(rgb[2])

    def setLineWidth(self, event):
        self.lineWidth = int(self.lineWidthCtrl.Value)
        if self.lineWidth < 1 :
            self.lineWidth = 1
        if self.lineWidth > 100:
            self.lineWidth = 100
        
    def changeLineColor(self, event):
        self.displayMessage("Changed color")
        channel = int(self.colorChannelCtrl.Value)
        if channel < 0 or channel > len(self.colours):
            channel = 0           
        red = int(self.redValueCtrl.Value)
        blue = int(self.blueValueCtrl.Value) 
        green = int(self.greenValueCtrl.Value)
        if red < 0 or red > 255:
            red = 0
        if blue < 0 or blue > 255:
            blue = 0
        if green <0 or green > 255:
            green = 0
            
        self.colours[channel] = (red, green, blue)
 
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

    def stopProgram(self, event):
        self.programRunning = False
        self.running.value = False
        if self.logResults:
            self.logFile.close()
        if self.arduinoInit:
            self.arduino.close()        
        sys.exit()
        
    def setEEGScaler(self, event):
        self.eegScaler = int(self.eegScalerCtrl.Value)
        
    def setSkipSamples(self, event):
        self.skipSamples = int(self.skipSamplesCtrl.Value)
        if self.skipSamples <= 0:
            self.displayMessage("Warning: decimation set to minimum of 1")
            self.skipSamples = 1
        if self.skipSamples > 10:
            self.skipSamples = 10
            self.displayMessage ("INFO: Reduced skip value to max == 10")
       
    def startEEG(self, event):
        self.startEEGButton.Label = "Starting"
        self.startEEGButton.Disable()
        self.eegChannelsCtrl.Disable()
        self.accelChannelsCtrl.Disable()
        self.inSampleCtrl.Disable()
        self.eegChannels = int(self.eegChannelsCtrl.Value)
        self.sampleTime = float(self.inSampleCtrl.Value)
        if self.sampleTime < 0.1:
            self.displayMessage("Warning: sampleTime set to minimum of 100 mSec")
            self.sampleTime = 0.1
        if self.eegChannels > 16:
            self.eegChannels = 16
            self.displayMessage("Warning: EEG channels set to max 16")
        if self.eegChannels <=0:
            self.eegChannels = 1
            self.displayMessage("Warning: EEG channels set to minimum 1")
        self.accelChannels = int(self.accelChannelsCtrl.Value)
        if self.accelChannels > 3:
            self.accelChannels = 3
            self.displayMessage("Warning: max nbr accel channels set to 3")
        if self.accelChannels < 0:
            self.accelChannels = 0
            self.displayMessage("Warning: accel channels set to minimum 0")
        for index in range(self.eegChannels + self.accelChannels):
            self.newDataList.append([index])
        if not self.eegRunning:
            self.theEEG = EEG(self.eegChannels, self.accelChannels, self.sampleTime)
            self.eegProc = Process(target=self.theEEG.run, args=(self.running, self.requestNewData, self.newDataAvailable, self.newDataList, self.eegError))
            self.eegProc.start()         

        self.requestNewData.value = True
        while not self.running.value:
            pass
        if self.eegError.value:
            self.startEEGButton.SetBackgroundColour(wx.Colour(150, 50, 50))
            self.displayMessage("Error: EEG not initialized, press Stop to begin again")           
            self.stopButton.SetBackgroundColour(wx.Colour(150, 50, 50))   
        else:   
            self.startEEGButton.SetBackgroundColour(wx.Colour(50, 150, 50))
            self.newDataAvailable.value = False
            while not self.newDataAvailable.value:
                pass
            self.newDataAvailable.value = False    
            self.theValues = self.decimateData()
            self.scaleData()
            self.x_data = []
            for index in range(len(self.theValues[0])):
                self.x_data.append(index)
            self.graphBuffer = []
            for index in range(len(self.theValues)):
                self.graphBuffer.append(copy.deepcopy(self.theValues[index]))
            self.graphIndex = 0
            self.startOutButton.Enable()
            self.displayMessage("EEG has started")
            self.startEEGButton.Label = "Running"

    def startOutput(self, event):           
        self.startOutButton.Disable()
        self.sendValues()
        
    def sendValues(self):
        if self.programRunning:
          threading.Timer(self.waitTime, self.sendValues).start()
          self.sendDataToArduino(self.waitTime)
          self.fillBuffer()
          
    def decimateData(self):
        nextBuffer = []
        decimatedData = []
        thisBuffer = []
        tempBuffer = []

        for index in range(self.eegChannels + self.accelChannels):   
            thisBuffer.clear()
            tempBuffer.clear()
            nextBuffer.append(self.newDataList[index])
            avgIndex = 0
            while (avgIndex + self.skipSamples + 2) < len(nextBuffer[0]):
                partialSum = 0
                for i in range(self.skipSamples):
                    partialSum += nextBuffer[index][avgIndex + i]
                avg = partialSum / self.skipSamples
                tempBuffer.append(avg)
                avgIndex += self.skipSamples

            for element in tempBuffer:
                thisBuffer.append(element)
            decimatedData.append(copy.deepcopy(thisBuffer))            
        return decimatedData

    def scaleData(self): # scale to max reach of -1 to 1
        for index in range(self.eegChannels):  # scale the EEG data 
            maxValue = max(self.theValues[index])
            minValue = abs(min(self.theValues[index]))
            trueMax = max(maxValue, minValue)           
            self.theValues[index][:] = [x / trueMax for x in self.theValues[index]]        
        scaler = float(self.accelScalerCtrl.Value)         
        for index in  range(self.accelChannels):
            self.theValues[index + self.eegChannels][:] = [x * scaler for x in self.theValues[index + self.eegChannels]]
            minValue = abs(min(self.theValues[index + self.eegChannels])) + self.lineWidth/2 + 1
            self.theValues[index + self.eegChannels][:] = [x + minValue for x in self.theValues[index + self.eegChannels]]
            
    def fillBuffer(self):   
        if self.theValues:
            if len(self.theValues[0]) <= int(self.getNewDataCtrl.Value):
                self.requestNewData.value = True
                while not self.newDataAvailable.value:
                    pass   
                self.theValues = self.decimateData()    
                self.scaleData()                 
        else:
            self.displayMessage("ERROR in Filldata buffer does not exist")
              
    def sendDataToArduino(self, waitTime):
          if len(self.theValues[0]) > 0:
              scalerValue = 0.5 * self.eegScaler
              arduinoMessage = ''
              arduinoMessage += str((1000 * int(waitTime)))
              arduinoMessage += (';')
              arduinoMessage += str(self.eegChannels + self.accelChannels)
              arduinoMessage += (';')
              graphValues = []
              for index in range(self.eegChannels):  
                  thisValue = scalerValue * self.theValues[index].pop()  + scalerValue  # Send a percentage!                
                  graphValues.append(thisValue)
                  formattedValue = float("{:.1f}".format(thisValue))
                  arduinoMessage += str(formattedValue)
                  arduinoMessage += (';')
                  
              for index in range(self.accelChannels):
                  thisValue = self.theValues[index + self.eegChannels].pop()  # Send a percentage!                   
                  graphValues.append(thisValue) 
                  if thisValue >= 100:
                      thisValue = 100
                  formattedValue = float("{:.1f}".format(thisValue))
                  arduinoMessage += str(formattedValue)
                  arduinoMessage += (';')   
              
              for index in range(len(self.graphBuffer)): 
                  self.graphBuffer[index][self.graphIndex] = graphValues[index] 
              self.graphIndex += 1
              if self.graphIndex >= (len(self.graphBuffer[0]) - 1):
                  self.graphIndex = 0
              self.plotFromGraphBuffer()
              self.arduino.write(arduinoMessage.encode())           
              if self.logResults:
                  arduinoMessage1 = arduinoMessage + "\n"
                  self.logFile.writelines(arduinoMessage1)

          else:
              self.displayMessage("Warning: data output array Empty")
        
    def startArduino(self, event):        
        thePort = "COM" + self.comPortCtrl.Value
        theSpeed = self.comSpeedCtrl.Value
        self.startArduinoButton.Label = "Starting"
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
            self.displayMessage("Contact Arduino established")
            self.startArduinoButton.Disable()
            self.comPortCtrl.Disable()
            self.comSpeedCtrl.Disable()
            self.startEEGButton.Enable()
            self.arduinoInit = True            
            self.startArduinoButton.SetBackgroundColour(wx.Colour(50, 150, 50))
            self.startArduinoButton.Label = "Running"
            
        except Exception as e:
            self.displayMessage ("Something wrong in Arduino Setup: ")
            self.displayMessage(e) 
            self.startArduinoButton.SetBackgroundColour(wx.Colour(150, 50, 50))

if __name__ == '__main__':        
    app = wx.App()  
    mfbaseTitle = 'Pyo EEG Simulator GUI '
    mainFrame = CSSGui(None, title= mfbaseTitle , size = (1200, 800)) 
    mainFrame.Show()    
    
    app.MainLoop()
    
    
    
    
    
    
    
    
    
    