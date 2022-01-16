#!/usr/bin/env python

import socket
import os
import sys
import time
import fcntl
import stat
import struct
import queue

from threading import Thread
from queue import Queue
from collections import deque

import xbmc

# This was obtained by a test C program consisting of "printf("%u", LIRC_GET_FEATURES)" (after include of linux/lirc.h)
LIRC_GET_FEATURES = 2147772672
LIRC_MODE_PULSE = 0x00000002
LIRC_CAN_SEND_PULSE = LIRC_MODE_PULSE
LIRC_SET_SEND_MODE = 1074030865
LIRC_SET_SEND_CARRIER = 1074030867
FEATURES = 0
KEEP_RUNNING = True
EVENTS = Queue()

def pulse2binary(indata):
  outdata = bytearray()

  # Iterate over the numbers in the pulse/space data 
  for i in indata.split(" "):
    # Strip off the +/- sign 
    i = i[1:]

    # Unpack the 32-bit value into 4 unsigned 8-bit integers 
    for b in struct.unpack("4B", struct.pack("I", int(i))): 
       # append each byte onto our new byte stream 
       outdata.append(b)

  return bytes(outdata)

class LIRC_CODES:
  VOL_UP = 73
  VOL_DN = 72
  VOL_MT = 71
  ONE = 201
  TWO = 202
  THREE = 203
    
# Get these from `ir-ctl -d /dev/lirc0 --receive` (ignoring the last number)
class IR_PULSE_DATA:
    VOL_UP = "+3450 -1600 +500 -300 +500 -350 +500 -1150 +500 -350 +500 -1200 +450 -350 +500 -1200 +450 -400 +450 -350 +500 -1200 +450 -350 +500 -350 +500 -1200 +450 -1200 +500 -350 +450 -400 +450 -350 +500 -350 +450 -400 +450 -400 +450 -350 +500 -350 +450 -1250 +450 -350 +450 -1250 +450 -350 +500 -350 +450 -400 +450 -400 +450 -350 +450 -400 +450 -400 +450 -1200 +450 -1250 +450 -1200 +450 -400 +450 -1200 +450 -400 +450 -400 +450 -400 +400 -400 +450 -1250 +450 -1200 +450 -400 +450 -1200 +450 -400 +450 -1250 +400 -400 +450"
    VOL_DN = "+3450 -1600 +500 -300 +500 -350 +500 -1200 +450 -350 +500 -1200 +500 -300 +500 -1200 +500 -350 +450 -350 +500 -1200 +450 -400 +450 -350 +500 -1200 +450 -1200 +500 -350 +450 -400 +450 -350 +500 -350 +450 -400 +450 -400 +450 -350 +500 -350 +450 -1250 +450 -350 +500 -1200 +450 -350 +500 -350 +450 -400 +450 -1200 +500 -350 +450 -400 +450 -400 +450 -1200 +450 -1250 +450 -1200 +450 -400 +450 -1200 +450 -400 +450 -400 +450 -350 +450 -400 +450 -1250 +400 -1250 +450 -400 +450 -400 +400 -400 +450 -1250 +450 -350 +450"
    VOL_MT = "+3400 -1600 +500 -350 +500 -300 +500 -1200 +500 -350 +450 -1200 +500 -350 +450 -1200 +500 -350 +500 -350 +450 -1200 +500 -350 +450 -400 +450 -1200 +450 -1250 +450 -350 +500 -350 +450 -400 +450 -350 +500 -350 +450 -400 +450 -400 +450 -350 +500 -1200 +450 -400 +450 -1200 +450 -400 +450 -400 +450 -350 +450 -400 +450 -1250 +450 -350 +450 -400 +450 -1200 +450 -1250 +450 -1200 +450 -400 +450 -1250 +400 -400 +450 -400 +450 -400 +450 -350 +450 -1250 +450 -1200 +450 -400 +450 -1250 +400 -1250 +450 -1250 +400 -400 +450 -12650 +3400 -1650 +450 -350 +450 -400 +450 -1250 +450 -350 +450 -1250 +450 -400 +400 -1250 +450 -400 +450 -350 +450 -1250 +450 -400 +400 -400 +450 -1250 +450 -1200 +450 -400 +450 -400 +450 -400 +400 -400 +450 -400 +450 -400 +400 -400 +450 -400 +450 -1250 +400 -400 +450 -1250 +450 -400 +400 -400 +450 -400 +450 -400 +400 -1250 +450 -400 +450 -400 +400 -1250 +450 -1250 +400 -1250 +450 -400 +450 -1200 +450 -400 +450 -400 +400 -450 +400 -400 +450 -1250 +400 -1250 +450 -400 +450 -1200 +450 -1250 +450 -1200 +450 -400 +450"
    INPUT_BD = "+3450 -1550 +500 -350 +500 -350 +500 -1150 +500 -350 +500 -1200 +450 -350 +500 -1200 +450 -350 +500 -350 +500 -1200 +450 -350 +500 -350 +450 -1250 +450 -1200 +450 -400 +450 -400 +450 -350 +500 -350 +450 -400 +450 -350 +500 -350 +450 -400 +450 -1200 +500 -350 +450 -1250 +450 -350 +450 -400 +450 -400 +450 -1200 +450 -400 +450 -400 +450 -350 +450 -1250 +450 -400 +450 -1200 +450 -1250 +400 -400 +450 -1250 +450 -400 +400 -400 +450 -400 +450 -400 +400 -1250 +450 -1250 +400 -1250 +450 -1250 +400 -1250 +450 -400 +400"
    INPUT_DVD = "+3400 -1600 +500 -350 +500 -350 +450 -1200 +500 -350 +500 -1150 +500 -350 +500 -1150 +500 -350 +500 -350 +450 -1200 +500 -350 +500 -350 +450 -1200 +500 -1200 +450 -350 +500 -350 +500 -350 +450 -400 +450 -350 +500 -350 +450 -400 +450 -400 +450 -1200 +450 -400 +450 -1200 +500 -350 +450 -400 +450 -350 +500 -350 +450 -400 +450 -400 +450 -350 +450 -1250 +450 -400 +450 -1200 +450 -1250 +450 -350 +450 -1250 +450 -350 +450 -400 +450 -400 +450 -400 +450 -1200 +450 -1250 +400 -400 +450 -1250 +450 -1200 +450 -400 +450"
    INPUT_CBL = "+3450 -1550 +500 -350 +500 -350 +500 -1150 +500 -350 +500 -1200 +450 -350 +500 -1200 +450 -350 +500 -350 +500 -1200 +450 -350 +500 -350 +500 -1200 +450 -1200 +450 -400 +450 -400 +450 -350 +500 -350 +450 -400 +450 -350 +500 -350 +450 -400 +450 -1200 +500 -350 +450 -1250 +450 -350 +500 -350 +450 -400 +450 -1200 +450 -1250 +450 -350 +500 -350 +450 -1250 +450 -350 +450 -1250 +450 -1200 +450 -400 +450 -1250 +400 -400 +450 -400 +450 -400 +450 -350 +450 -1250 +450 -1200 +450 -1250 +450 -400 +400 -1250 +450 -400 +450"
    INPUT_GAME = "+3400 -1600 +500 -350 +500 -300 +500 -1200 +500 -350 +500 -1150 +500 -350 +500 -1150 +500 -350 +500 -350 +450 -1200 +500 -350 +450 -400 +450 -1200 +500 -1200 +450 -350 +500 -350 +450 -400 +450 -400 +450 -350 +500 -350 +450 -400 +450 -350 +500 -1200 +450 -400 +450 -1200 +450 -400 +450 -400 +450 -350 +500 -1200 +450 -400 +450 -1200 +450 -400 +450 -1200 +450 -400 +450 -1200 +450 -1250 +450 -400 +450 -1200 +450 -400 +450 -400 +400 -400 +450 -400 +450 -1250 +400 -1250 +450 -1200 +450 -1250 +450 -400 +400 -400 +450"

CODES = {
    LIRC_CODES.VOL_UP: pulse2binary(IR_PULSE_DATA.VOL_UP),
    LIRC_CODES.VOL_DN: pulse2binary(IR_PULSE_DATA.VOL_DN),
    LIRC_CODES.VOL_MT: pulse2binary(IR_PULSE_DATA.VOL_MT),
    LIRC_CODES.ONE: pulse2binary(IR_PULSE_DATA.INPUT_BD),
    LIRC_CODES.TWO: pulse2binary(IR_PULSE_DATA.INPUT_GAME),
    LIRC_CODES.THREE: pulse2binary(IR_PULSE_DATA.INPUT_DVD),
}

def open_lirc (filename:str = "/dev/lirc0"):
  global FEATURES

  fd = os.open(filename, os.O_RDWR | os.O_CLOEXEC)
  st = os.fstat(fd)

  if stat.S_IFMT(st.st_mode) != stat.S_IFCHR:
    sys.stderr.write(f"{filename}: not character device\n")
    os.close(fd)
    sys.exit(1)

  FEATURES = fcntl.ioctl(fd, LIRC_GET_FEATURES, struct.pack('=I', 0))

  return fd

def lirc_send (fd, device, carrier, cmd):
  if not int.from_bytes(FEATURES, "little") & LIRC_CAN_SEND_PULSE:
    sys.stderr.write(f"{device}: device cannot send raw ir\n")
    sys.exit(0)

  fcntl.ioctl(fd, LIRC_SET_SEND_MODE, struct.pack('=I', LIRC_MODE_PULSE))

  success = fcntl.ioctl(fd, LIRC_SET_SEND_CARRIER, struct.pack('=I', carrier))
  success = int.from_bytes(success, "little")

  if success < 0:
    sys.stderr.write(f"warning: {device}: failed to set carrier: {carrier}\n")

  xbmc.log(f"sending key code {cmd}", level=xbmc.LOGINFO)
  try:
    os.write(fd, CODES[cmd])
  except OSError:
    xbmc.log(f"Failed to send key code {cmd}", level=xbmc.LOGINFO)

def consumer (fd):
  global KEEP_RUNNING

  while KEEP_RUNNING:
    try:
      cmd = EVENTS.get(timeout=1)
      lirc_send(fd, "/dev/lirc0", 38000, cmd)
    except queue.Empty:
      pass

if __name__ == '__main__':
  monitor = xbmc.Monitor()
  listener = "/run/lirc/lircd"
  consumer_thread = fd = sock = None

  try:
    fd = open_lirc()
    consumer_thread = Thread(target=consumer, args=(fd,))
    consumer_thread.start()

    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(1)
    sock.connect(listener)

    while not monitor.abortRequested():
      try:
        data = sock.recv(64)

        try:
          cmd = int(data.decode("utf-8").split(" ")[0])
        except ValueError:
          continue

        if cmd in CODES.keys():
          EVENTS.put(cmd)
        else:
          xbmc.log(f"Ignoring key code {cmd}", level=xbmc.LOGINFO)

      except socket.timeout:
        pass

  finally:
    if consumer_thread:
      KEEP_RUNNING = False
      consumer_thread.join(2)
    if fd:
      os.close(fd)
    if sock:
      sock.close()
