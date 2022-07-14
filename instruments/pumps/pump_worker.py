# -*- coding: utf-8 -*-
"""
Created on Wed Jul 13 17:14:14 2022

@author: Kumaheva AI
"""

from PyQt5.QtCore import QThread, pyqtSignal



class Pump_worker(QThread):
    finished = pyqtSignal()
    #progress = pyqtSignal(str)
    
    def __init__(self, pump, cmd, values = []):
        super().__init__()
        self.pump = pump
        self.cmd = cmd
        self.values = values
        
        

    def run(self):
        
        ###pull
        if self.cmd == 1:
            ### values = [port, vol]
            port = self.values[0]
            vol = self.values [1]
            
            if vol == -1:
                self.pump.load_all(port)
            else:
                self.pump.load(port, vol)
            
        ###push
        if self.cmd == 2:
            ### values = [port, vol]
            port = self.values[0]
            vol = self.values [1]
            if vol == -1:
                self.pump.inject_all(port)
            else:
                self.pump.inject(port, vol)
           
            
        self.finished.emit()