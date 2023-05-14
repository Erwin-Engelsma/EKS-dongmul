# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 19:49:21 2022

@author: Erwin
workbook = xlsxwriter.Workbook('Example2.xlsx')
worksheet = workbook.add_worksheet()
 
# Start from the first cell.
# Rows and columns are zero indexed.
row = 0
column = 0
 
content = ["ankit", "rahul", "priya", "harshita",
                    "sumit", "neeraj", "shivam"]
 
# iterating through content list
for item in content :
 
    # write operation perform
    worksheet.write(row, column, item)
 
    # incrementing the value of row by one
    # with each iterations.
    row += 1
     
workbook.close()
"""

import tkinter as tk
from tkinter import ttk
import xlsxwriter
import serial


class GUI(tk.Tk):
   
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initTheGui() 
        self.arduinoStarted = False
        self.arduino = serial.Serial()
        self.sheets = 1
        self.excelOpen = False
        
    def openExcelSheet(self):
        self.thisWorkbook = self.excelFilename.get() + '.xlsx' 
        self.workbook = xlsxwriter.Workbook(self.thisWorkbook)
        self.excelOpen = True
        
    def startCalib (self):
        worksheet = self.workbook.add_worksheet(self.sheetName.get() + str(self.sheets))
        self.sheets += 1
        row = 0
        column = 0
        content = ["ankit", "rahul", "priya", "harshita",
                    "sumit", "neeraj", "shivam"]
 
        for item in content :         
            worksheet.write(row, column, item)         
            row += 1

        
    def stop(self):
        if self.arduinoStarted == True:
            self.arduino.close()
        if self.excelOpen == True:
            self.workbook.close()    
        self.destroy()

    def startArduino(self):
        self.port = self.portEntry.get()
        self.speed = self.speedEntry.get()
        
        try:
            self.arduino = serial.Serial(self.port, self.speed)
            self.arduino.reset_input_buffer()          
            response = str(self.arduino.read().decode())
            while not 'i' in response:
                response = str(self.arduino.read().decode())
            print("Connection to " + self.port + " established succesfully!\n")

            self.arduino.timeout = 0.5
            self.arduino.flush()  # make sure buffer is emptied. There may be noise on the line due to USB connection
            #self.response_label.config(text="Serial started")
            #self.startUsbButton["state"] = tk.DISABLED
            #self.sendCalib()
            self.arduinoStarted = True # inform main loop that serial communication is there
            
        except Exception as e:
            print(e)  
            
    def initTheGui(self):
        self.title("Volume Calibrator")
        self.geometry("600x600")
        self.resizable(width = True, height = True)
        self.attributes("-topmost", True)         
        
        """
        Administration
        """ 
        fileNameLabel =tk.Label(self, text = "File Name: ")
        fileNameLabel.grid(column = 1, row = 5, sticky ='nwe')
        self.excelFilename = tk.Entry()        
        self.excelFilename.insert(0, "VolumeCalibration")
        self.excelFilename.grid(column=2,row=5,sticky='we')
        sheetLabel =tk.Label(self, text = "Sheet: ")
        sheetLabel.grid(column = 3, row = 5, sticky ='nwe')
        self.sheetName = tk.Entry()        
        self.sheetName.insert(0, "Measurement")
        self.sheetName.grid(column=4,row=5,sticky='we')     
        self.excelButton = ttk.Button(self, text="Open Excelsheet", command = self.openExcelSheet)        
        self.excelButton.grid(column = 5, row = 5, sticky = 'we', padx=10, pady= 2 )          
        """
        Serial Port
        """
        portLabel =tk.Label(self, text = "Port")
        portLabel.grid(column = 1, row = 10, sticky ='nwe')
        self.portEntry =  tk.Entry(self)
        self.portEntry.grid(column = 2, row = 10, sticky ='nwe')
        self.portEntry.insert( -1, "COM4")
        speedLabel =tk.Label(self, text = "Speed")
        speedLabel.grid(column = 3, row = 10, sticky ='nwe')
        self.speedEntry =  tk.Entry(self)
        self.speedEntry.grid(column = 4, row = 10, sticky ='nwe')
        self.speedEntry.insert(-1, "115200")
        self.arduinoButton = ttk.Button(self, text="Start Arduino", command = self.startArduino)        
        self.arduinoButton.grid(column = 5, row = 10, sticky = 'we', padx=10, pady=2 )   
        
        """
        Measurement params
        """       
        intervalLabel =tk.Label(self, text = "Interval: ")
        intervalLabel.grid(column = 3, row = 15, sticky ='nwe')
        self.interval = tk.Entry()        
        self.interval.insert(0, 200)
        self.interval.grid(column=4,row=15,sticky='we')  
        
        minPWMLabel =tk.Label(self, text = "Min PMW: ")
        minPWMLabel.grid(column = 1, row = 15, sticky ='nwe')
        self.minPWM = tk.Entry()        
        self.minPWM.insert(0, '65')
        self.minPWM.grid(column=2,row=15,sticky='we')        
        maxPWMLabel =tk.Label(self, text = "Max PMW: ")
        maxPWMLabel.grid(column = 1, row = 20, sticky ='nwe')
        self.maxPWM = tk.Entry()        
        self.maxPWM.insert(0, '110')
        self.maxPWM.grid(column=2,row=20,sticky='we') 
        stepPWMLabel =tk.Label(self, text = "PMW stepsize: ")
        stepPWMLabel.grid(column = 1, row = 25, sticky ='nwe')
        self.stepPWM = tk.Entry()        
        self.stepPWM.insert(0, '5')
        self.stepPWM.grid(column=2,row=25,sticky='we')           
        self.startButton = ttk.Button(self, text="Start Calibration", command = self.startCalib)        
        self.startButton.grid(column = 5, row = 15, sticky = 'we', padx=10, pady=2 )   

        self.stopButton = ttk.Button(self, text="Stop", command = self.stop)        
        self.stopButton.grid(column = 1, row = 45, sticky = 'we', padx=10, pady=10)   
        
        self.update()

       

if __name__ == '__main__':
    app = GUI()
    app.mainloop()