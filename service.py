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

# Mapping of remote codes to blaster data
CODES = {
  # Volume Up
  73: b"\26\r\0\0\244\6\0\0\220\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\342\4\0\0\220\1\0\0\220\1\0\0\302\1\0\0\342\4\0\0\220\1\0\0\302\1\0\0\220\1\0\0\342\4\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\342\4\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\342\4\0\0\220\1\0\0\342\4\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\220\1\0\0\302\1\0\0\342\4\0\0\220\1\0\0\302\1\0\0\220\1\0\0\342\4\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\342\4\0\0\220\1\0\0\342\4\0\0\220\1\0\0\24\5\0\0\220\1\0\0\220\1\0\0\302\1\0\0\342\4\0\0\220\1\0\0\302\1\0\0\220\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\342\4\0\0\302\1\0\0\342\4\0\0\220\1\0\0\220\1\0\0\302\1\0\0\342\4\0\0\220\1\0\0\302\1\0\0\220\1\0\0\342\4\0\0\220\1\0\0\302\1\0\0\220\1\0\0",

  # Volume Down
  72: b"H\r\0\0r\6\0\0\220\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\342\4\0\0\220\1\0\0\220\1\0\0\302\1\0\0\342\4\0\0\302\1\0\0\220\1\0\0\220\1\0\0\342\4\0\0\302\1\0\0\220\1\0\0\302\1\0\0^\1\0\0\302\1\0\0\342\4\0\0\302\1\0\0\220\1\0\0\302\1\0\0^\1\0\0\302\1\0\0\342\4\0\0\302\1\0\0\260\4\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\220\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\220\1\0\0\220\1\0\0\302\1\0\0\342\4\0\0\302\1\0\0\220\1\0\0\220\1\0\0\342\4\0\0\302\1\0\0\220\1\0\0\302\1\0\0^\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\342\4\0\0\302\1\0\0^\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\260\4\0\0\302\1\0\0\342\4\0\0\302\1\0\0\260\4\0\0\302\1\0\0\220\1\0\0\302\1\0\0\342\4\0\0\220\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0^\1\0\0\302\1\0\0\342\4\0\0\302\1\0\0\260\4\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\220\1\0\0\342\4\0\0\302\1\0\0\220\1\0\0\302\1\0\0",

  # Green (Tivo input)
  201: b"\336\r\0\0r\6\0\0\364\1\0\0^\1\0\0&\2\0\0^\1\0\0\364\1\0\0\260\4\0\0&\2\0\0^\1\0\0\364\1\0\0\260\4\0\0&\2\0\0^\1\0\0\302\1\0\0\342\4\0\0\364\1\0\0\220\1\0\0\364\1\0\0^\1\0\0\364\1\0\0\342\4\0\0\302\1\0\0\220\1\0\0\364\1\0\0^\1\0\0\364\1\0\0\342\4\0\0\302\1\0\0\342\4\0\0\364\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\364\1\0\0^\1\0\0\364\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\364\1\0\0^\1\0\0\364\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\364\1\0\0\342\4\0\0\302\1\0\0\220\1\0\0\302\1\0\0\24\5\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\364\1\0\0\220\1\0\0\302\1\0\0\342\4\0\0\364\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\364\1\0\0\342\4\0\0\302\1\0\0\220\1\0\0\364\1\0\0\342\4\0\0\302\1\0\0\24\5\0\0\302\1\0\0\220\1\0\0\302\1\0\0\24\5\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\302\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\24\5\0\0\302\1\0\0\342\4\0\0\302\1\0\0\24\5\0\0\302\1\0\0\24\5\0\0\220\1\0\0\24\5\0\0\302\1\0\0\220\1\0\0\302\1\0\0",

  # Blue (Kodi input)
  202: b"\336\r\0\0r\6\0\0\364\1\0\0^\1\0\0\364\1\0\0^\1\0\0\364\1\0\0\342\4\0\0\364\1\0\0^\1\0\0&\2\0\0\260\4\0\0\364\1\0\0^\1\0\0\364\1\0\0\342\4\0\0\364\1\0\0^\1\0\0\364\1\0\0^\1\0\0\364\1\0\0\342\4\0\0\364\1\0\0^\1\0\0\364\1\0\0\220\1\0\0\302\1\0\0\342\4\0\0\364\1\0\0\342\4\0\0\364\1\0\0^\1\0\0\364\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\364\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\302\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\342\4\0\0\364\1\0\0\220\1\0\0\302\1\0\0\342\4\0\0\364\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\24\5\0\0\302\1\0\0\220\1\0\0\302\1\0\0\24\5\0\0\302\1\0\0\220\1\0\0\302\1\0\0\24\5\0\0\302\1\0\0\220\1\0\0\302\1\0\0\24\5\0\0\302\1\0\0\24\5\0\0\220\1\0\0\302\1\0\0\302\1\0\0\24\5\0\0\220\1\0\0\302\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\302\1\0\0\302\1\0\0\342\4\0\0\302\1\0\0\24\5\0\0\302\1\0\0\24\5\0\0\220\1\0\0\24\5\0\0\302\1\0\0\302\1\0\0\220\1\0\0\302\1\0\0\302\1\0\0",
}

# Minimal re-implementation of method from https://github.com/cz172638/v4l-utils/blob/master/utils/ir-ctl/ir-ctl.c
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

# Minimal re-implementation of method from https://github.com/cz172638/v4l-utils/blob/master/utils/ir-ctl/ir-ctl.c
def lirc_send (fd, device, carrier, cmd):
  if not int.from_bytes(FEATURES, "little") & LIRC_CAN_SEND_PULSE:
    sys.stderr.write(f"{device}: device cannot send raw ir\n")
    sys.exit(0)

  fcntl.ioctl(fd, LIRC_SET_SEND_MODE, struct.pack('=I', LIRC_MODE_PULSE))

  success = fcntl.ioctl(fd, LIRC_SET_SEND_CARRIER, struct.pack('=I', carrier))
  success = int.from_bytes(success, "little")

  if success < 0:
    sys.stderr.write(f"warning: {device}: failed to set carrier: {carrier}\n")

  os.write(fd, CODES[cmd])

# Thread to process IR blasting events
def consumer (fd):
  global KEEP_RUNNING

  while KEEP_RUNNING:
    try:
      cmd = EVENTS.get(timeout=1)
      lirc_send(fd, "/dev/lirc0", 38069, cmd)
    except queue.Empty:
      pass

if __name__ == '__main__':
  # Listen for events from Kodi
  monitor = xbmc.Monitor()

  # Unix socket location for listening to eventlircd
  listener = "/run/lirc/lircd"

  # Initialize some variables (they need to be something so they can be used in the "finally" block)
  consumer_thread = fd = sock = None

  try:
    # Open a file descriptor to the blaster device
    fd = open_lirc()

    # Start a thread to consume and process blaster events
    consumer_thread = Thread(target=consumer, args=(fd,))
    consumer_thread.start()

    # Connect to the eventlircd UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(1)
    sock.connect(listener)

    # Main runtime loop, continuing until Kodi tells us to stop
    while not monitor.abortRequested():
      try:
        # Read up to 64 bytes from the UDS
        data = sock.recv(64)

        # Decode the data as a UTF-8 string, tokenize on a space delimiter, and grab the first element
        try:
          cmd = int(data.decode("utf-8").split(" ")[0])
        except ValueError:
          continue

        # Queue the blaster to handle the button, if it's one we have defined, otherwise, print the key code to the Kodi log
        if cmd in CODES.keys():
          EVENTS.put(cmd)
        else:
          xbmc.log(f"Ignoring key code {cmd}", level=xbmc.LOGINFO)

      # Loop again if the socket connection times out
      except socket.timeout:
        pass

  finally:
    # Stop the consumer thread and close all file/socket handles
    if consumer_thread:
      KEEP_RUNNING = False
      consumer_thread.join(2)
    if fd:
      os.close(fd)
    if sock:
      sock.close()
