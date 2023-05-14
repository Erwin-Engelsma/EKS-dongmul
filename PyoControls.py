# -*- coding: utf-8 -*-
"""
Created on Wed Nov 23 14:53:02 2022

@author: Erwin
"""

import wx
import pyo
from pyo import PyoGuiGrapher


class channelNames(wx.Frame):
    def __init__(self,  channels, callBack):        
        wx.Frame.__init__(self)      
        self.frame = wx.Frame(None, -1, "channel names")
        size = (360, int(channels) * 22 + 70)
        self.frame.SetSize((size)) 
        self.callBack = callBack
        self.channels = channels
        self.channelNamesList = []
        self.namesList = []
        for index in range(int(channels)):
            self.channelNamesList.append(wx.TextCtrl(self.frame, 2,  style = wx.TE_PROCESS_ENTER,  value = str(index), size = (60, 22)))
            self.channelNamesList[index].SetPosition((1, 24 + index * 22))
            self.channelNamesList[index].SetSize(280, 20)
        
        namesButton = wx.Button(self.frame, -1, 'names set', pos = (1,1), name='names')
        namesButton.Bind(wx.EVT_BUTTON, self.namesButtonCallBack)  
        
        self.frame.Show(True) 
    
    def setNames(self, names):
        for index in range(len(self.channelNamesList)):
            self.channelNamesList[index].Value = names[index]
            
    def getNames(self):
        return self.namesList
            
    def namesButtonCallBack(self, event):       
        for index in range(int(self.channels)):
            self.namesList.append(self.channelNamesList[index].GetValue())        
        self.frame.Close()
        self.callBack()   

class flexSlider(wx.Frame):
    def __init__(self,  frameName, index, callBack, thePos = (1300, 10), size = (100, 580)):        
        wx.Frame.__init__(self) 
        self.callBack = callBack
        self.frameName = frameName

        self.index = index
        self.multiplier = 0.1
        self.offset = 0
        self.value = 0.7
        self.frame = wx.Frame(None, -1, frameName)
        self.frame.SetPosition(thePos)
        self.frame.SetSize((size)) 
        
        self.Slider = wx.Slider(self.frame,  value=1, minValue=0, maxValue=20, size = (20, size[1] - 60), style=wx.SL_VERTICAL) #init=[(0.0, 0.0), (8191, 0.0)]
        self.maxValueCtrl = wx.TextCtrl( self.frame, 2,  style = wx.TE_PROCESS_ENTER,  value = "20", size = (60, 22)) 
        self.minValueCtrl = wx.TextCtrl( self.frame, 3,  style = wx.TE_PROCESS_ENTER,  value = "1", size = (60, 22)) 
        self.multiplierCtrl = wx.TextCtrl( self.frame, 4,style = wx.TE_PROCESS_ENTER,  value = "0.1", size = (60, 22))
        self.offsetCtrl = wx.TextCtrl( self.frame, 5,style = wx.TE_PROCESS_ENTER,  value = "0", size = (60, 22))
        self.result = wx.StaticText( self.frame, label = "0.7", size = (40,22)) 
        self.stepSize = wx.StaticText( self.frame, label = str(size[1] - 80), size = (60,22)) 
        
        self.frame.Bind(wx.EVT_SIZE, self.sizeChanged)
        self.Slider.Bind(wx.EVT_SCROLL_CHANGED, self.onSliderChanged)  #EVT_SCROLL_CHANGED
        self.maxValueCtrl.Bind(wx.EVT_TEXT_ENTER, self.setSliderMax, id = 2)
        self.minValueCtrl.Bind(wx.EVT_TEXT_ENTER, self.setSliderMin, id = 3)     
        self.multiplierCtrl.Bind(wx.EVT_TEXT_ENTER, self.setMultiplier, id = 4)
        self.offsetCtrl.Bind(wx.EVT_TEXT_ENTER, self.setBasisValue, id = 5)        
        self.Slider.SetPosition((1,20))
        self.setValue(int(self.value/self.multiplier))
        self.maxValueCtrl.SetPosition((20,size[1] - 80))
        self.minValueCtrl.SetPosition((20,25))  
        self.multiplierCtrl.SetPosition((20, 50))
        self.offsetCtrl.SetPosition((20, 75))
        self.result.SetPosition((1,1))  
        self.stepSize.SetPosition((50, 1))
        self.frame.Show(True) 

    def sizeChanged(self, event):
        width,self.height = event.GetSize() 
        self.Slider.SetSize(20, self.height - 60)
        self.maxValueCtrl.SetPosition((20, self.height - 80))
        self.changeStepSize()
        
    def changeStepSize(self):
        sliderRange = self.Slider.GetMax() - self.Slider.GetMin()       
        step = sliderRange / (self.height - 80)
        step *= self.multiplier
        self.stepSize.Label = str(step)[0:8]
        
    def setSliderMax(self, event):
        self.Slider.SetMax(int(self.maxValueCtrl.Value))
        self.changeStepSize()

    def setSliderMin(self, event):
        self.Slider.SetMin(int(self.minValueCtrl.Value))
        self.changeStepSize()   
        
    def setMultiplier(self, event):
        self.multiplier = float(self.multiplierCtrl.Value)
        self.changeStepSize()      

    def setBasisValue(self, event):
        self.offset = float(self.offsetCtrl.Value)        
    
    def onSliderChanged(self, event):
        self.sliderChanged()
        
    def sliderChanged(self):
        self.value = int(self.Slider.GetValue())
        self.value*= self.multiplier
        self.value+=self.offset
        
        self.result.SetLabel(str(self.value)[0:6])
        self.callBack()  
        
    def setValue(self, value):
        self.Slider.SetValue(value)

    def getValue(self):
        theValue = float("{:.6f}".format(self.value))
        return theValue

    def getInfo(self):       
        theValue = self.Slider.GetValue() 
        maxVal = self.maxValueCtrl.Value
        minVal = self.minValueCtrl.Value    
        multiVal = self.multiplierCtrl.Value
        offset = self.offsetCtrl.Value 
        theTuple =  (self.frameName, self.index, theValue, maxVal, minVal, multiVal, offset)
        return theTuple
    
    def setInfo(self, theTuple):
        self.frameName = theTuple[0]
        self.index = theTuple[1]                          
        self.Slider.SetValue(theTuple[2])
        self.maxValueCtrl.Value = theTuple[3]
        self.Slider.SetMax(int(theTuple[3]))
        self.minValueCtrl.Value = theTuple[4]
        self.Slider.SetMin(int(theTuple[4]))
        self.multiplierCtrl.Value = theTuple[5]
        self.multiplier = float(theTuple[5])
        self.offsetCtrl.Value = theTuple[6]
        self.offset = float( theTuple[6])
        self.value = int(theTuple[2])
        self.value*= self.multiplier
        self.value+=self.offset
        self.result.SetLabel(str(self.value)[0:6])
        self.callBack()
        
    def setCallBack(self, callBack):
        self.callBack = callBack
        
    def closePanel(self):
        self.Hide()
        self.Destroy()        
        
class flexGraph(wx.Frame):
    def __init__(self, frameName, index, callBack, position = (10, 10),  size = (250, 250), elements = 8192, vertRange = (-1.0, 1.0)):
        wx.Frame.__init__(self)  
        self.callBack = callBack
        self.frameName = frameName
        self.index = index
        self.frame = wx.Frame(None, -1, frameName)
        self.frame.SetPosition(position)
        self.frame.SetSize((size))        
        self.pyoGraph = PyoGuiGrapher(self.frame, xlen=elements, yrange=vertRange)  #, init=[(0, 0.0), (8191, 0.0)]
        self.pyoGraph.setValues([(0,0.0), (elements - 1, 0.0)])
        self.graphPoints = []
        self.pyoGraph.SetPosition((1,2))
        self.frame.Bind(wx.EVT_SIZE, self.sizeChanged)
        self.shortValues = []
        self.pyoGraph.Bind(pyo.EVT_PYO_GUI_GRAPHER, self.graphChanged)  

        self.frame.Show(True)
              
    def sizeChanged(self, event):
        width,height = event.GetSize() 
        self.pyoGraph.SetSize((width - 15, height - 40))
        
    def graphChanged(self, event):
        self.updateShortValues()    
        self.callBack(self.index)   # self.graphPoints
        
    def setValues(self, values):
        self.pyoGraph.setValues(values)

    def updateShortValues(self):
        print("updating the short values")
        self.shortValues.clear()
        for valuePair in self.pyoGraph.getValues():
            yValue =  float("{:.6f}".format(valuePair[1]))
            xValue = valuePair[0]
            newPair = (xValue, yValue)
            self.shortValues.append(newPair)            
        
    def getValues(self):            
        return self.shortValues
    
    def findEquivalencePosition(self, x):
        index = 0
        if not self.shortValues:
            self.updateShortValues()
        while self.shortValues[index][0] < x:
            index += 1
        return index - 1
            
    def calculateY(self, index, thisX):
        beginX = self.shortValues[index][0]
        beginY = self.shortValues[index][1]
        endX = self.shortValues[index+1][0]
        endY = self.shortValues[index+1][1]
        distance = thisX - beginX
        fraction = distance / (endX - beginX)
        return beginY + fraction * (endY-beginY)

    def getAllPoints(self, beginX, EndX, Skip):
        line = []
        if Skip <= 0:
            Skip = 1
            
        for thisX in range(beginX, EndX, Skip):
            eqIndex = self.findEquivalencePosition(thisX)
            yValue = self.calculateY(eqIndex, thisX)
            line.append(yValue)
        line.reverse()    
        return line
          
    def setCallBack(self, callBack):
        self.callBack = callBack

    def getInfo(self):
        theTuple = (self.frameName, self.index, self.getValues())
        return theTuple
    
    def setInfo(self, inputTuple):
        self.frameName = inputTuple[0]
        self.index = inputTuple[1]
        self.setValues(inputTuple[2])
        self.frame.SetTitle(self.frameName)
    
    def setName(self, name):
        self.frame.SetTitle(name)
        self.frameName = name
        
    def getName(self):
        return self.frameName
        
    def closePanel(self):
        print("Hiding this panel")
        self.Hide()
        self.Destroy()