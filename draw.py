import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import time
import os
import sys
import serial
import serial.tools.list_ports

#import struct

import com.portUI 

from com.serClass import COM
import threading
from time import sleep, ctime
from com.port_var import *
from com.portUI import *

from  PyQt5.QtWidgets import QPushButton,QApplication,QMainWindow,QLineEdit,QFormLayout,QWidget,QTextEdit,QVBoxLayout
from PyQt5.QtGui import QIntValidator,QDoubleValidator,QRegExpValidator,QFont
from PyQt5.QtCore import  QRegExp,Qt

import com.uiVar as uiVar

openFlag = False
testCom = COM()

#define a cooking process
#Send the door close S3
#check the water switch S2,if not full,open the Y1
#Send the gas generator heater open H2
#get the heater temperature B4,when the temperature to pre-setting
#start heating send the heating open H1 and get the B4 temperature
#enable M1 Forward rotation/Reverse rotation
#get humidity pressure value
cooking_Table = [0x01,0x02,0x03,0x04,0x05,0x06,\
                0x07,0x08,0x09,0x0A,0x0B,0x0C]
Phase_Timer = [0x03,0x03,0x03,0x03,0x03,0x0A,0x0A,0x0A,0x03,0x03,0x03,0x03]
# time,command,length,data
Phase_Table_One = [0x03,0x01,0x00]    # 01:enable/disable valve
Phase_Table_Two = [0x03,0x01,0x01]     
Phase_Table_Three = [0x03,0x02,0x00]   # 02:enable/disable heater
Phase_Table_Four = [0x03,0x02,0x01]       
Phase_Table_Five = [0x03,0x03,0x00,0x00,0x00]   # 03:enable/disable motor  RPM
Phase_Table_Six = [0x03,0x03,0x00,0x05,0x78]         #1400 = 0x578 Forward
Phase_Table_Seven = [0x03,0x03,0x01,0x05,0x78]         #1400 = 0x578 Reverse
Phase_Table_Eight = [0x03,0x04,0x00]   # 04:enable/disable air pump
Phase_Table_Nine = [0x03,0x04,0x01] 
def ReadFileSize():
    #filepath='D:\\App.bin'
    #data = np.fromfile(filepath,dtype=np.uint16,count=128,offset=0)
    #binfile = open(filepath, 'rb') #打开二进制文件
    #size = os.path.getsize(filepath) #获得文件大小
    # for i in range(size):
    #     data = binfile.read(1) #每次输出一个字节
    #     print(data[4,2])
    print(data)
    #     print(data[4,2])
    # binfile.close()
    #return size

def testFun(serCom,sendCommand,sendData):
    
    if sendCommand == 0:
        testCom.txSendData(serCom,Phase_Table_One[1],0,\
                              Phase_Table_One[2])
    elif sendCommand == 1:
        testCom.txSendData(serCom,Phase_Table_Two[1],0,\
                              Phase_Table_Two[2])
    elif sendCommand == 2:
        testCom.txSendData(serCom,Phase_Table_Three[1],0,\
                              Phase_Table_Three[2])
    elif sendCommand == 3:
        testCom.txSendData(serCom,Phase_Table_Four[1],0,\
                              Phase_Table_Four[2])
    elif sendCommand == 4:
        testCom.txSendBuf(serCom,Phase_Table_Five[1],\
                              Phase_Table_Five[2],\
                              Phase_Table_Five[3],\
                              Phase_Table_Five[4])
    elif sendCommand == 5:
        testCom.txSendBuf(serCom,Phase_Table_Six[1],\
                              Phase_Table_Six[2],\
                              Phase_Table_Six[3],\
                              Phase_Table_Six[4])
    elif sendCommand == 6:
        testCom.txSendBuf(serCom,Phase_Table_Seven[1],\
                              Phase_Table_Seven[2],\
                              Phase_Table_Seven[3],\
                              Phase_Table_Seven[4])
    elif sendCommand == 11:
        data1 = sendData >> 8
        data2 = sendData & 0xFF
        testCom.txSendData(serCom,sendCommand,data1,data2)
        print("send humidity")
    elif sendCommand == 12:
        data1 = sendData >> 8
        data2 = sendData & 0xFF
        testCom.txSendData(serCom,sendCommand,data1,data2)
        print("send temperature")
    else:
        testCom.txSendData(serCom,2,3,1)
def main_task(serCom,enflag):
    while 1:
        if enflag == 1:
            testCom.unpack(serCom)
            # testCom.unpack(serCom)
            # # testFunPort2(serCom) 
            # if  varPort.testStart == 1:
            #     testFunPort1(serCom) 
            # elif varPort.testPort == 2: # test port 2
            #     testFunPort2(serCom)            
        sleep(0.1)

def main_task2(serCom):
    #ReadFileSize()
    while 1:
        if varPort.startCooking != 0:  #start cooking
            if varPort.sendHumidity != varPort.cookingHumidity:
                varPort.sendHumidity = varPort.cookingHumidity
                testFun(serCom,11,varPort.sendHumidity)   #send humidity
            elif varPort.sendTemp != varPort.cookingTemperature:
                varPort.sendTemp = varPort.cookingTemperature
                testFun(serCom,12,varPort.cookingTemperature) #send temp
            elif varPort.cookingPhaseTimer >= Phase_Timer[varPort.cookingPhase]*5:
                if varPort.cookingPhase == 5:
                    varPort.cookingPhase = 4
                elif varPort.cookingPhase == 6:
                    varPort.cookingPhase = 4
                elif varPort.cookingPhase == 4:
                    if varPort.fanDirection == 0:
                        varPort.cookingPhase = 5
                        varPort.fanDirection = 1
                    else:
                        varPort.cookingPhase = 6
                        varPort.fanDirection = 0
                else:
                    varPort.cookingPhase += 1
                varPort.cookingPhaseTimer = 0 
                testFun(serCom,varPort.cookingPhase,0) 
                
            else:
                varPort.cookingPhaseTimer += 1
            
        else:
            if varPort.startCooking == 1:
                testFun(serCom,0,0) 
                varPort.startCooking = 0
        sleep(0.2)

def main_task1(main):
    portTestValue = 0
    varPort.testPhase = 0
    varPort.testStart = 0
    while 1:    
        main.fn_t_100ms()
        sleep(1)  #handle one tiem per 5 seconds

def main_t_100ms():
    mt_100ms = threading.Timer(0.1,main_t_100ms)
    mt_100ms.start()

import sys
#from mainwindow import Ui_MainWindow
from PyQt5 import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem, QHBoxLayout
class MainUI(Ui_MainWindow, QMainWindow):
    def __init__(self, parent=None):
        super(MainUI, self).__init__(parent)
        self.setupUi(self)    
if __name__ == "__main__":
    ser,openFlag = testCom.refresh()
    
    if openFlag:
        print("send start")
    maintask2 = threading.Thread(target=main_task2,args=(ser,))
    maintask2.start()

    maintask = threading.Thread(target=main_task,args=(ser,openFlag,))
    maintask.start()
   
    app = QApplication(sys.argv)
    main = MainUI()
    maintask1 = threading.Thread(target=main_task1,args=(main,))
    maintask1.start()
    main.show()
    sys.exit(app.exec_())

    

    

 