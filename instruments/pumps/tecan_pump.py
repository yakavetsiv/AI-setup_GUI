#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 17 21:50:08 2022

@author: viprorok
"""
import pyvisa
import time, os
import struct







class Pump(object):
    ### maximal number of steps for the syringe
    
    
    ports ={
        'waste':1,
        'device0':2,
        'device1':3,
        'device2':4,
        'device3':5,
        'device4':6,
        'device5':7,
        'device6':8,
        'device7':9,
        'drug1':10,
        'drug2':11,
        'drug3':12,
        }
    
    def __init__(self, name, address = 1, syringe_volume = 1000):
        
        self.address = str(address)
        self.header = '/' + chr(int(self.address, 16) + 49)
        self.volume_max = int(syringe_volume)
        self.footer = '\r'
        self.VMAX = 181490

        
        ###establish the connection
        self.manager = pyvisa.ResourceManager().open_resource(name)     
        self.manager.baud_rate = 9600
        self.manager.stop_bits = pyvisa.constants.StopBits.one
        self.manager.parity = pyvisa.constants.Parity.none
        self.manager.data_bits = 8
        self.manager.read_termination = '\x03\r\n'
        self.manager.timeout = 5000
              
        ###initialization
        self.send_command('K10') 
        self.send_command('k10')
        self.send_command('Z') 
        
        self.port = 1
        self.speed = 14
        
        self.set_speed(self.speed)
        #update the speeds and postition 

        self.cur_position = self.update_position()
        #self.update_top_speed()
        
    def send_command(self, command):    
        while not(self.query()):
                time.sleep(0.1)
        response = self._command(command +'R')
        #self.update_position()
        
        #self.manager.write(self.header + command + 'R' + self.footer)
        #response = self.manager.read_raw()
        #return response
        
    def _command(self, command):
      
        self.manager.write(self.header + command + self.footer)
        response = self.manager.read_raw()
        return response[3:-3], (response[3] // 32 - 2)
        
    
    ###injection of particular volume to the particular port
    def query(self):
        _, status = self._command('Q')
        return status

    
    ###injection of particular volume to the particular port
    def inject(self, port, volume):
        position = self._position(volume)
        
        if self.cur_position - position < 0:
            position = self.cur_position
            
            
        command = f'O{port}D{position}'
        self.cur_position -= position
        self.send_command(command)
        self.port = port
        print(f'{volume} mL injected in {port} port')
        self.cur_position = self.update_position()

    
    def inject_all(self, port):        
        volume = self.volume(self.cur_position)  
        self.send_command(f'O{port}A0') 
        self.port = port
        self.cur_position = 0
        print(f'{volume} mL injected in {port} port')
        self.cur_position = self.update_position()
        

    def update_position(self):
        while not(self.query()):
                time.sleep(0.1)
        data, _ = self._command('?')
        temp = str(data, 'UTF-8')
        pos = int(temp[1:])
        return pos
        
    ###loading of the syringe with particular volume from the particular port
    def load(self, port, volume):
        position = self._position(volume)
        if self.cur_position + position > self.VMAX:
            position = self.VMAX   
            self.cur_position = self.VMAX
        else:
            self.cur_position += position
            
        command = f'O{port}P{position}'
            
        self.send_command(command)
        self.port = port
        print(f'{volume} mL loaded from {port} port')
        self.cur_position = self.update_position()

    
    def load_all(self, port):
        volume = self.volume_max - self.volume(self.cur_position)    
        command = f'O{port}A{self.VMAX}'
        self.send_command(command)
        self.cur_position = self.VMAX
        self.port = port
        print(f'{volume} mL loaded from {port} port')
        self.cur_position = self.update_position()

    
    
    ###conventing the volume to the absolute position of the syringe
    def _position(self, volume):
        return int(round(volume*self.VMAX/self.volume_max))
    
    def volume(self, position):
        return round(position*self.volume_max/self.VMAX, 2)
    
    def set_speed(self, speed):  
        if 1 <= speed <= 50:
            command = f'S{speed}'
            self.send_command(command)
            self.speed = speed
            self.update_top_speed()
        else:
            print('Wrong number')
    
    
    def update_top_speed(self):
        data, _ = self._command('?7')
        temp = str(data, 'UTF-8')
        speed = int(temp[1:-2])
        print(speed)
    
 
    def close(self):
        self.manager.close()
        

    
        
    
    
        