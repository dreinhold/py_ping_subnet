#!/usr/bin/python3.8

import threading
import sys
from collections import OrderedDict
import time
import subprocess

CLEAR_PREV_LINE = "\x1b[1A\x1b[2K" # move up cursor and delete whole line

ip_status = OrderedDict()
lock = threading.Lock()
printed_lines = 0
running = True

class Device():
    CHECKING = 0
    COMPLETE = 1
    def __init__(self, ip):
        lock.acquire()
        self.ip = ip
        self.status = self.CHECKING
        self.message = None
        self.my_thread = None
        lock.release()

    def update_message(self, message):
        self.message = message
        self.status = self.COMPLETE

    def get_message(self):
        if self.status == self.COMPLETE:
            return f"{self.ip} : {self.message}"
        else:
            return f"{self.ip} : Checking.."

    def __str__(self):
        return self.get_message()

def display():
    global printed_lines
    lock.acquire()
    if sys.stdout.isatty():
        # Only clear screen if we are in a terminal
        curr_len = len(ip_status)
        if curr_len > printed_lines:
            for _ in range(0, curr_len - printed_lines):
                print("")
        printed_lines = curr_len
        for _ in range(0, curr_len):
            sys.stdout.write(CLEAR_PREV_LINE)
    for i in ip_status:
        print(ip_status[i])
    lock.release()

def display_thread():
    while running:
        if sys.stdout.isatty():
            display()
        time.sleep(.5)
    display()

def ping_device(device):

    ping_result = subprocess.run(["ping", "-c2", device.ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if ping_result.returncode == 0:
        device.update_message("Online")
    else:
        device.update_message("Offline")

def main():
    global running
    print("Started")
    dt = threading.Thread(target=display_thread, args=())
    dt.start()

    for i in range(0,10):
        ip = f"192.168.50.{i}"
        device = Device(ip)
        ip_status[ip] = device
        t = threading.Thread(target=ping_device, args=(device,))
        device.my_thread = t

    # start all pings
    for d in ip_status.values():
        d.my_thread.start()

    # wait for them all
    for d in ip_status.values():
        d.my_thread.join()
    running = False # we are done with all pings

    dt.join() # Wait for display_thread to run one last time


if __name__ == "__main__":
    main()