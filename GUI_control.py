# -*- coding: utf-8 -*-
"""
Created on Sun Feb 20 16:05:29 2022

@author: vipro
"""
import sys
from PyQt5 import QtWidgets, uic


from instruments.pumps.tecan_pump import Pump
from instruments.hotplates.hotplate_ard import Hotplate
from instruments.thorlabs.powermeter.TLPM import TLPM

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


from PyQt5.QtGui import QPixmap
import random


#shutter control
from pylabinstrument.thorlabs.motion import KCubeSolenoid as kds
from pylabinstrument.thorlabs.motion import KCubeDCServo as kdc
from pylabinstrument.thorlabs.spectrometer import CCS

from ctypes import cdll,c_long,c_uint32,c_uint16,c_uint8,byref,create_string_buffer,c_bool, c_char, c_char_p,c_int,c_int16,c_int8,c_double,c_float,sizeof,c_voidp, Structure






sh_serial = 68250554
power_name = b"USB0::0x1313::0x807B::220201226::INSTR"
pump_name = 'ASRL1::INSTR'
spect_name = r'USB::0x1313::0x8089::M00802700::RAW'
hotplate_name = "COM7"
  

class SecondWindow(QtWidgets.QMainWindow):
    def __init__(self, sp_type):
        #type 0 - power; 1 - UV-VIS, 2- PL
        
         super(SecondWindow, self).__init__()
         self.update_type(sp_type)
             
         
         self.main_widget = QtWidgets.QWidget()
         self.setCentralWidget(self.main_widget)
         save_data_B = QtWidgets.QPushButton("Save data")
         save_plot_B = QtWidgets.QPushButton("Save plot")

         layout_main = QtWidgets.QVBoxLayout(self.main_widget)
         
         self.canvas = MyMplCanvas(self.main_widget, width = 300, height = 200)
         layout_main.addWidget(self.canvas)
         
         layout_btn = QtWidgets.QHBoxLayout()
         layout_btn.addWidget(save_data_B)
         layout_btn.addWidget(save_plot_B)
         
     
         
         layout_main.addLayout(layout_btn)
         
         save_plot_B.clicked.connect(self.save_plot)
         save_data_B.clicked.connect(self.save_data)
    
    def update_type(self, sp_type):
        self.sp_type = sp_type
        if sp_type == 0:
            self.setWindowTitle('Power spectrum')
        if sp_type == 1:
            self.setWindowTitle('UV-VIS spectrum')
        if sp_type == 2:
            self.setWindowTitle('PL spectrum')
        
    
    def save_plot(self):
        dialog = QtWidgets.QFileDialog()
        fileName, ext = dialog.getSaveFileName(None, "Save plot", "", "PNG (*.png);;JPEG (*.jpeg)", options=QtWidgets.QFileDialog.DontUseNativeDialog)
        
        if  (fileName  == '') :
            return
        if ext == 'PNG (*.png)':
            fileName = fileName + '.png'
        if ext == 'JPEG (*.jpeg)':
            fileName = fileName + '.jpeg'
        
        self.canvas.fig.savefig(fileName)

        
    def save_data(self):
        dialog = QtWidgets.QFileDialog()
        fileName, ext = dialog.getSaveFileName(None, "Save data", "", "CSV (*.csv)", options=QtWidgets.QFileDialog.DontUseNativeDialog)
        
        fileName = fileName + '.csv'
        
        self.canvas.data.to_csv(fileName, index = False)

         
         

class MyMplCanvas(FigureCanvas):

    def __init__(self, parent=None, width= 300, height= 200):
        self.fig = Figure(figsize=(width, height))
        self.axes = self.fig.add_subplot(111)

        
        parameters = {'xtick.labelsize': 10,
                  'ytick.labelsize': 10,
                  'font.family':'sans-serif',
                  'font.sans-serif':['Arial']}
        plt.rcParams.update(parameters)
        

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_figure(self, sp_type, x,y, st_dev = 0, bounds = [0,0]):

        
        self.axes.set_xlabel('Wavelength, nm', fontsize=10)
        
        if sp_type == 0:
            self.axes.set_ylabel('Power, mW', fontsize=10)
            columns = ['Wavelenth, nm', 'Power, W','st_dev']

        if sp_type == 1:
            self.axes.set_ylabel('Absorbance', fontsize=10)
            columns = ['Wavelenth, nm', 'Absorbance','st_dev']
        if sp_type == 2:
            self.axes.set_ylabel('PL intensity', fontsize=10)
            columns = ['Wavelenth, nm', 'PL intensity','st_dev']
        
        self.fig.set_tight_layout(True)

        
        self.data = pd.DataFrame(columns=columns)
        
        self.data.iloc[:,0] = x
        self.data.iloc[:,1] = y
        self.data.iloc[:,2] = st_dev
        
        
        self.axes.fill_between(x, y-st_dev, y+st_dev, alpha=0.2, edgecolor='#CC4F1B', facecolor='#FF9848', linestyle= "None")
        self.axes.scatter(x, y, s = 2, c = 'Black')
        if bounds[0] < x.min():
            xmin = x.min()
        else:
           xmin = bounds[0]
        
        if bounds[1] > x.max():
            xmax = x.max()
        else:
           xmax = bounds[1]
        
        self.axes.set_xlim(xmin, xmax)



class MainWindow(QtWidgets.QMainWindow):
    
    

    def __init__(self, *args, **kwargs):
        
        super().__init__(*args, **kwargs)
        uic.loadUi("gui/Setup_control.ui", self)
        self.LED_ON = QPixmap('gui/icons/led_green.png')
        self.LED_OFF = QPixmap('gui/icons/led_grey.png')
        self.LED_ALARM = QPixmap('gui/icons/led_red.png')
        
        self.shutter_LED.setPixmap(self.LED_OFF)
        self.power_LED.setPixmap(self.LED_OFF)
        self.spectr_LED.setPixmap(self.LED_OFF)
        self.pump_LED.setPixmap(self.LED_OFF)
        self.shutter_state = False
        self.connectSignalsSlots()
        
        

        
        
        
        
    def connectSignalsSlots(self):
        ###Pump_control
        self.init_pump_B.clicked.connect(self.init_pump)
        self.close_pump_B.clicked.connect(self.close_pump)

        self.pull_10B.clicked.connect(self.pull_10)
        self.pull_100B.clicked.connect(self.pull_100)
        self.pull_maxB.clicked.connect(self.pull_max)
        self.pull_customB.clicked.connect(self.pull_custom)
        
        self.push_10B.clicked.connect(self.push_10)
        self.push_100B.clicked.connect(self.push_100)
        self.push_maxB.clicked.connect(self.push_max)
        self.push_maxB.clicked.connect(self.push_max)
        self.push_customB.clicked.connect(self.push_custom)
        
        self.speedB.clicked.connect(self.set_speed)
        
        self.cmdB.clicked.connect(self.send_command)
        
        ###Setup control
        
        #init
        self.init_setup_B.clicked.connect(self.init_setup)
        self.close_setup_B.clicked.connect(self.close_setup)
        
        #shutter control
        
        self.shutter_B.clicked.connect(self.shutter_change)
        
        #powermeter control
        self.power_measure_B.clicked.connect(self.power_measure)
        self.power_spectr_B.clicked.connect(self.power_spectrum)
        
        #spectrometer
        self.spectr_measure_B.clicked.connect(self.spectr_spectrum)
        
        #hotplate
        self.hotplate_set_speed_B.clicked.connect(self.hotplate_set_speed)
        self.hotplate_check_speed_B.clicked.connect(self.hotplate_read_speed)
        
        self.hotplate_set_temp_B.clicked.connect(self.hotplate_set_temp)
        self.hotplate_check_temp_B.clicked.connect(self.hotplate_read_temp)
         
        
    def pull_10(self):
        self.port = self.valve.value()
        self.pump.load(self.port, 10)
        self.update_pump()
    
    def pull_100(self):
        self.port = self.valve.value()
        self.pump.load(self.port, 100)
        self.update_pump()
        
    def pull_max(self):
        self.port = self.valve.value()
        self.pump.load_all(self.port)
        self.update_pump()
        
    def pull_custom(self):
        self.port = self.valve.value()
        volume = self.pull_vol.value()
        self.pump.load(self.port, volume)
        self.update_pump()
        
    def push_10(self):
        self.port = self.valve.value()
        self.pump.inject(self.port, 10)
        self.update_pump()
    
    def push_100(self):
        self.port = self.valve.value()
        self.pump.inject(self.port, 100)
        self.update_pump()
        
    def push_max(self):
        self.port = self.valve.value()
        self.pump.inject_all(self.port)
        self.update_pump()
        
    def push_custom(self):
        self.port = self.valve.value()
        volume = self.push_vol.value()
        self.pump.inject(self.port, volume)
        self.update_pump()
    
    def init_pump(self):
        self.pump = Pump(pump_name, syringe_volume = 2500)
        self.volume_group.setEnabled(True)
        self.speed_group.setEnabled(True)
        self.command_group.setEnabled(True)
        self.close_pump_B.setEnabled(True)
        self.init_pump_B.setEnabled(False)
        self.update_pump()
        self.pump_LED.setPixmap(self.LED_ON)

        
    def set_speed(self):
        self.pump.set_speed(self.speed_num.value())
        self.update_pump()
        
    def update_pump(self):
        volume = int(self.pump.volume(self.pump.cur_position))
        self.vol_text.setText(f'{volume} uL')
        self.vol_Bar.setValue(int(volume)/self.pump.volume_max*100)        
        self.speed_L.setText(f'Current speed is {self.pump.speed} Inc/s')

        
    def close_pump(self):
        self.pump.close()
        self.volume_group.setEnabled(False)
        self.speed_group.setEnabled(False)
        self.command_group.setEnabled(False)
        self.closeB.setEnabled(False)
        self.initB.setEnabled(True)
        self.pump_LED.setPixmap(self.LED_OFF)
        

        
    def send_command(self):
        cmd = self.cmd_In.text()
        response = self.pump.send_command(cmd)
        self.cmd_Out.setText(response)
        
        
    ###setup control
    
            
    def init_setup(self):
        
        #shutter initialization
        typename='ksc'
        result = kdc.discover(typename)
        
        self.sh = kds.Motor(sh_serial)
        
        self.sh.open()
        self.shutter_state = False
        self.shutter_change()
        self.shutter_LED.setPixmap(self.LED_ON)
        self.shutter_group.setEnabled(True)

            #self.shutter_LED.setPixmap(LED_ALARM)
        
        #powermeter initialization
        self.pm = TLPM()
        
        self.pm.open(create_string_buffer(power_name), c_bool(True), c_bool(True))
        self.power_LCD.display(0)
        self.power_label.setText('mW')
        self.power_group.setEnabled(True)
    
        
        self.power_LED.setPixmap(self.LED_ON)
        
        
        #spectrometer initialization
        self.sp = CCS.CCS(spect_name)  
        self.sp.open()
        self.spectr_LED.setPixmap(self.LED_ON)
        
        
        self.spectr_group.setEnabled(True)
        self.close_setup_B.setEnabled(True)
        self.init_setup_B.setEnabled(False)
        self.update_setup(init = True)
        
        
        #hotplate initialization
        self.hp = Hotplate(hotplate_name)        
        self.hotplate_LED.setPixmap(self.LED_ON)
        self.hotplate_group.setEnabled(True)
        self.hotplate_set_speed_B.setEnabled(True)
        self.hotplate_set_temp_B.setEnabled(True)
        self.hotplate_check_speed_B.setEnabled(True)
        self.hotplate_check_temp_B.setEnabled(True)
        
        

        
                
    def close_setup(self):
        self.pump.close()
        self.pm.close()
        self.sp.close()
        self.power_group.setEnabled(False)
        self.shutter_group.setEnabled(False)
        self.spectr_group.setEnabled(False)
        self.close_setup_B.setEnabled(False)
        self.init_setup_B.setEnabled(True)
        
        self.shutter_LED.setPixmap(self.LED_OFF)
        self.power_LED.setPixmap(self.LED_OFF)
        self.spectr_LED.setPixmap(self.LED_OFF)
    
    
    #shutter
    def shutter_change(self):
        self.shutter_state = self.shutter_B.isChecked()
        if self.shutter_state:
            state = 'on'
        else:
            state = 'off'
                
        self.sh.shutterTo(state)
        self.update_setup()
        
    def update_setup(self, init = False):
        if self.shutter_state:
            self.shutter_B.setText('Open')
        else:
            self.shutter_B.setText('Closed')
        if init:
            self.shutter_B.setChecked(self.shutter_state)
            
    #powermeter
    def power_measure(self):
        wl = self.power_wl.value()
        wavelength = c_double(wl)     
        self.pm.setWavelength(wavelength)
        
        power =  c_double()
        self.pm.measPower(byref(power))
        #print(power.value)
        
        
        signal = power.value
        
        if signal < 0:
            signal = 0
        
        if signal < 0.001:
            self.power_label.setText('uW')
            signal = signal*1000000
        else:
            self.power_label.setText('mW')
            signal = signal*1000
            
        self.power_LCD.display(signal)
        
    def power_spectrum(self):
            
        wl_st = self.power_st_wl.value()
        wl_end = self.power_end_wl.value()
        repeats = self.power_repeat.value()
        step = 1
        
        length = int((wl_end-wl_st)/step)
        x = np.linspace(wl_st, wl_end, length)
        
        p = np.empty([length, repeats])
        print(p.shape)

        print(repeats)  
        
        for i in range(repeats):
            y = []
            for j, wl in enumerate(x):
                wavelength = c_double(wl)     
                self.pm.setWavelength(wavelength)            
                power =  c_double()
                self.pm.measPower(byref(power))
                signal = power.value
                if signal < 0:
                    signal = 0
                
                p[j,i] = signal*1000

        
        
        ###mean 
        y = np.mean(p, axis = 1)
        
        ### st_dev = zeros
        y_err = np.std(p, axis = 1)
         
        sp_type = 0
        self.plot(sp_type ,x, y, st_dev = y_err, bounds = [wl_st,wl_end])
        print('Spectrum done')

        
    #spectrometer
    def spectr_spectrum(self):
        wl_st = self.spectr_st_wl.value()
        wl_end = self.spectr_end_wl.value()
        int_time = self.spectr_intT.value()/1000
        repeats = self.spectr_repeats.value()
        repeats = 1
        self.sp.setIntegrationTime(int_time)
        
        z, x = self.sp.sweep(avgN=repeats)
        
        x = np.asarray(x)            
        z = np.reshape(z, [x.shape[0], repeats])

        ###mean        
        y = np.mean(z, axis = 1)
        ###mean 
        y_err = np.std(z, axis = 1)
        
           
        if self.shutter_state:
            sp_type = 1
        else:
            sp_type = 2
        
        self.plot(sp_type ,x, y, st_dev = y_err, bounds = [wl_st, wl_end])
        print('Spectrum done')

        
    
    def plot(self, sp_type, x, y, st_dev = 0, bounds = [0,1100]):
        try:
            self.SW.canvas.axes.clear()
            if not(sp_type == self.SW.sp_type):
                self.SW.update_type(sp_type)
            self.SW.canvas.compute_figure(self.SW.sp_type, x,y, st_dev = st_dev, bounds = bounds)
            self.SW.canvas.draw()

        except:
            self.SW = SecondWindow(sp_type)
            self.SW.resize(450,350)
            self.SW.move(1000, 300)
            self.SW.canvas.compute_figure(sp_type, x, y, st_dev = st_dev, bounds = bounds)
            self.SW.show()
    
    
    def hotplate_set_speed(self):
        speed = self.stirrer_speed.value()
        self.hp.set_speed_voltage(speed)
        
        
    def hotplate_read_speed(self):        
        speed_val = self.hp.read_speed()
        self.stirrer_LCD.display(speed_val)
        
    def hotplate_set_temp(self):
        temp = self.plate_temp.value()
        self.hp.set_temp_voltage(temp)
        
        
    def hotplate_read_temp(self):        
        temp_val = self.hp.read_temp()
        self.temp_LCD.display(temp_val)
        
        
        
    
    def closeEvent(self, event):
        self.pm.close()
        self.sp.close()
        self.hp.close()

        
            
        

            
        
        




def main():

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
        
                 
if __name__ == "__main__":
    main()