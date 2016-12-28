#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bot import Bot
from feedupdater import FeedUpdater
import os
import signal

def signal_handler(signal, frame):
    print "Caught SIGINT, terminating."
    os._exit(0)

if __name__ == "__main__":
    bot = Bot()

    missing_config_keys = bot.get_missing_options()
    if not len(missing_config_keys) == 0:
        for key in missing_config_keys:
            print "Config option '{}' is missing! Please check your config!".format(key)
        os._exit(1)

    bot._Bot__irc.connection.buffer_class.errors = 'replace' # prevent utf-8 error in jaraco.stream
    bot.initial_feed_update()
    bot.start()
    signal.signal(signal.SIGINT, signal_handler)
    while True:
        signal.pause()
