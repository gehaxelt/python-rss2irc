#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ssl
import threading
import irc.bot
import irc.client
import irc.connection
import tinyurl
import time
import re
import feedparser
import datetime
import dateutil.parser
from colour import Colours
from db import FeedDB
from config import Config
from feedupdater import FeedUpdater

class IRCBot(irc.bot.SingleServerIRCBot):
    def __init__(self, config, db, on_connect_cb):
        self.__config = config
        self.__db = db
        self.__on_connect_cb = on_connect_cb
        self.__servers = [irc.bot.ServerSpec(self.__config.HOST, self.__config.PORT, self.__config.PASSWORD)]
        self.num_col = self.__config.num_col
        self.date = self.__config.date
        self.feedname = self.__config.feedname
        self.shorturls = self.__config.shorturls
        self.dateformat = self.__config.dateformat

        if self.__config.SSL:
            ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
            super(IRCBot, self).__init__(self.__servers, self.__config.NICK, self.__config.NICK, connect_factory=ssl_factory)
        else:
            super(IRCBot, self).__init__(self.__servers, self.__config.NICK, self.__config.NICK)

    def on_welcome(self, connection, event):
        """Join the correct channel upon connecting"""
        if irc.client.is_channel(self.__config.CHANNEL):
            connection.join(self.__config.CHANNEL)

    def on_join(self, connection, event):
        """Say hello to other people in the channel. """
        connection.privmsg(self.__config.CHANNEL, "Hi, I'm " + Colours('3',str(connection.get_nickname())).get() + " your bot. Send " + Colours(self.num_col,"!help").get() +" to get a list of commands.")
        self.__on_connect_cb()

    def __handle_msg(self, msg):
        """Handles a cmd private message."""
        try:
            # Print help
            if msg == "!help":
                answer = self.__help_msg()

            # List all subscribed feeds
            elif msg == "!list":
                answer = ""
                for entry in self.__db.get_feeds():
                    answer += "#" + Colours(self.num_col,str(entry[0])).get() + ": " + entry[1] + ", " + Colours('',str(entry[2])).get() + Colours(self.date,", updated every ").get() + Colours(self.num_col,str(entry[3])).get() + Colours(self.date," min").get() + "\n"

            # Print some simple stats (Feed / News count)
            elif msg == "!stats":
                feeds_count = self.__db.get_feeds_count()
                news_count = self.__db.get_news_count()
                answer = "Feeds: " + Colours(self.num_col,str(feeds_count)).get() + ", News: " + Colours(self.num_col,str(news_count)).get()

            # Print last 25 news.
            elif msg == "!last":
                answer = ""
                for entry in self.__db.get_latest_news(self.__config.feedlimit)[::-1]:
                    answer += "#" + Colours(self.num_col,str(entry[0])).get() + ": " + entry[1] + ", " + Colours('',str(entry[2])).get() + ", " + Colours(self.date,entry[3]).get() + "\n"

            # Print last 25 news for a specific feed
            elif msg.startswith("!lastfeed"):
                answer = ""
                try:
                    feedid = int(msg.replace("!lastfeed","").strip())
                except:
                    return Colours('1',"Wrong command: ").get() + msg + ", use: !lastfeed <feedid>"
                for entry in self.__db.get_news_from_feed(feedid, self.__config.feedlimit)[::-1]:
                    answer += "#" + Colours(self.num_col,str(entry[0])).get() + ": " + entry[1] + ", " + Colours('',str(entry[2])).get() + ", " + Colours(self.date,str(entry[3])).get() + "\n"

            # Else tell the user how to use the bot
            else:
                answer = "Use !help for possible commands."
        except Exception as e:
            print e
            answer = "Something went wrong :("

        return answer

    def on_privmsg(self, connection, event):
        """Handles the bot's private messages"""
        if len(event.arguments) < 1:
            return

        # Get the message and return an answer
        msg = event.arguments[0].lower().strip()
        print msg

        answer = self.__handle_msg(msg)
        self.send_msg(event.source.nick, answer)

    def on_pubmsg(self, connection, event):
        """Handles the bot's public (channel) messages"""
        if len(event.arguments) < 1:
            return

        # Get the message. We are only interested in "!help"
        msg = event.arguments[0].lower().strip()

        # Send the answer as a private message
        if msg == "!help":
            self.send_msg(event.source.nick, self.__help_msg())

    def on_nicknameinuse(self, connection, event):
        """Changes the nickname if necessary"""
        connection.nick(connection.get_nickname() + "_")

    def send_msg(self, target, msg):
        """Sends the message 'msg' to 'target'"""
        try:
            # Send multiple lines one-by-one
            for line in msg.split("\n"):
                # Split lines that are longer than 510 characters into multiple messages.
                for sub_line in re.findall('.{1,510}', line):
                    self.connection.privmsg(target, sub_line)
                    time.sleep(1) # Don't flood the target
        except Exception as e:
            print e

    def post_news(self, feed_name, title, url, date):
        """Posts a new announcement to the channel"""
        try:
            msg = Colours(self.feedname,str(feed_name)).get() + ": " + title + ", " + Colours('',url).get() + ", " + Colours(self.date,str(date)).get()
            self.send_msg(self.__config.CHANNEL, msg)
        except Exception as e:
            print e

    def __help_msg(self):
        """Returns the help/usage message"""
        return """\
Help:
    Send all commands as a private message to """ + self.connection.get_nickname() + """
    - !help         Prints this help
    - !list         Prints all feeds
    - !stats        Prints some statistics
    - !last         Prints the last 10 entries
    - !lastfeed <feedid> Prints the last 10 entries from a specific feed
"""

class Bot(object):
    def __init__(self):
        self.__config = Config()
        self.__db = FeedDB(self.__config)
        self.__feedupdater = FeedUpdater(self.__config, self.__db)
        self.__irc = IRCBot(self.__config, self.__db, self.on_started)
        self.__connected = False

    def start(self):
        """Starts the IRC bot"""
        threading.Thread(target=self.__irc.start).start()

    def initial_feed_update(self):
        def print_feed_update(feed_title, news_title, news_url, news_date):
            print("[+]: {}||{}||{}||{}".format(feed_title, news_title, news_url, news_date))

        if self.__config.update_before_connecting:
            print "Started pre-connection updates!"
            self.__feedupdater.update_feeds(print_feed_update, False)
            print "DONE!"

    def on_started(self):
        """Gets executed after the IRC thread has successfully established a connection."""
        if not self.__connected:
            print "Connected!"
            self.__feedupdater.update_feeds(self.__irc.post_news, True)
            print "Started feed updates!"
            self.__connected = True