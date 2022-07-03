#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 17 22:01:27 2022

@author: viprorok
"""
import pyvisa
import time, os
import struct
import serial


class Hotplate(object):
    

    def __init__(self, name):
        
        ###establish the connection
        self.manager = serial.Serial(name, baudrate=9600, timeout = 3)  
        time.sleep(1)
        self._read_response()


        ### turn off the stirrer and hotplate
        self.speed = -1
        self.set_temp_voltage(-1)
        self.temp = -1
        self.set_speed_voltage(-1)
        
    def set_speed_voltage(self, speed_voltage):
        self.speed = speed_voltage
        command = f'1,1,{speed_voltage}.'
        self._send_command(command)
        
    def set_temp_voltage(self,temp_voltage):
        self.temp = temp_voltage
        command = f'2,1,{temp_voltage}.'
        self._send_command(command)
        
    def read_speed(self):
        self._send_command('1,2.')
        speed = self._read_response()[:-1]
        return speed
    
    def read_temp(self):
        self._send_command('2,2.')
        temp = self._read_response()[:-1]
        return temp
        
    def close(self):
        self.set_temp_voltage(-1)
        self.set_speed_voltage(-1)
        self.manager.close()
           
        
    def _send_command(self, command):            
        self.manager.write(command.encode('ascii'))
        
    def _read_response(self):            
        return self.manager.readline().decode('ascii')
        
        
