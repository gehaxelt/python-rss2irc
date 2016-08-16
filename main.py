#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bot import Bot
import os
import signal

def signal_handler(signal, frame):
    print "Caught SIGINT, terminating."
    os._exit(0)

if __name__ == "__main__":
    bot = Bot()
    bot.start()
    signal.signal(signal.SIGINT, signal_handler)
    while True:
        signal.pause()
