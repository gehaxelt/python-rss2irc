#!/usr/bin/env python3

from bot import Bot
from feedupdater import FeedUpdater
from config import Config
import os
import signal
import datetime
import sys

def signal_handler(signal, frame):
    print(datetime.datetime.now() , "Received SIGINT signal, finishing bot.")
    sys.stdout.flush()
    os._exit(0)

if __name__ == "__main__":
    bot = Bot()

    missing_config_keys = bot.get_missing_options()
    if not len(missing_config_keys) == 0:
        for key in missing_config_keys:
            print(datetime.datetime.now(), "The '{}' option isn't set up! Check configuration.".format(key))
            sys.stdout.flush()
        os._exit(1)

    bot._Bot__irc.connection.buffer_class.errors = 'replace' # prevent utf-8 error in jaraco.stream
    bot.initial_feed_update()
    bot.start()
    signal.signal(signal.SIGINT, signal_handler)
    while True:
        signal.pause()
