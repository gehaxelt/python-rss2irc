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
        self.__first_start = False
        self.color_num = self.__config.num_col
        self.color_date = self.__config.date
        self.color_feedname = self.__config.feedname
        self.color_url = self.__config.url
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
        welcome_msg = "Hi, I'm " + self.__get_colored_text('3',str(connection.get_nickname())) + " your bot. Send " + self.__get_colored_text(self.color_num,"!help") +" to get a list of commands."

        if not self.__first_start:
            connection.privmsg(self.__config.CHANNEL, welcome_msg)
            self.__on_connect_cb()
            self.__first_start = True

        if event.source.nick != connection.get_nickname():
            connection.privmsg(event.source.nick, welcome_msg)


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
                    answer += "#" + self.__get_colored_text(self.color_num,str(entry[0])) + ": " + entry[1] + ", " + self.__get_colored_text(self.color_url,str(entry[2])) + self.__get_colored_text(self.color_date,", updated every ") + self.__get_colored_text(self.color_num,str(entry[3])) + self.__get_colored_text(self.color_date," min") + "\n"

            # Print some simple stats (Feed / News count)
            elif msg == "!stats":
                feeds_count = self.__db.get_feeds_count()
                news_count = self.__db.get_news_count()
                answer = "Feeds: " + self.__get_colored_text(self.color_num,str(feeds_count)) + ", News: " + self.__get_colored_text(self.color_num,str(news_count))

            # Print last config.feedlimit news.
            elif msg == "!last":
                answer = ""
                items = self.__db.get_latest_news(self.__config.feedlimit)
                if not self.__config.feedorderdesc:
                    items = items[::-1]

                for entry in items:
                    answer += "#" + self.__get_colored_text(self.color_num,str(entry[0])) + ": " + entry[1] + ", " + self.__get_colored_text(self.color_url,str(entry[2])) + ", " + self.__get_colored_text(self.color_date,str(entry[3])) + "\n"

            # Print last config.feedlimit news for a specific feed
            elif msg.startswith("!lastfeed"):
                answer = ""
                try:
                    feedid = int(msg.replace("!lastfeed","").strip())
                except:
                    return self.__get_colored_text('1',"Wrong command: ") + msg + ", use: !lastfeed <feedid>"
                items = self.__db.get_news_from_feed(feedid, self.__config.feedlimit)
                if not self.__config.feedorderdesc:
                    items = items[::-1]
                for entry in items:
                    answer += "#" + self.__get_colored_text(self.color_num,str(entry[0])) + ": " + entry[1] + ", " + self.__get_colored_text(self.color_url,str(entry[2])) + ", " + self.__get_colored_text(self.color_date,str(entry[3])) + "\n"

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
            msg = self.__get_colored_text(self.color_feedname,str(feed_name)) + ": " + title + ", " + self.__get_colored_text(self.color_url,url) + ", " + self.__get_colored_text(self.color_date,str(date))
            self.send_msg(self.__config.CHANNEL, msg)
        except Exception as e:
            print e

    def __get_colored_text(self, color, text):
        if not self.__config.use_colors:
            return text

        return Colours(color, text).get()

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
        self.__missing_options = self.__check_config()
        if len(self.__missing_options) > 0:
            return None
        self.__db = FeedDB(self.__config)
        self.__feedupdater = FeedUpdater(self.__config, self.__db)
        self.__irc = IRCBot(self.__config, self.__db, self.on_started)
        self.__connected = False

    def __check_config(self):
        necessary_options = ["HOST", "PORT", "PASSWORD", "SSL", "CHANNEL", "NICK", "admin_nicks", "use_colors", 
                             "num_col", "date", "feedname", "shorturls", "dateformat", "feedlimit", "update_before_connecting",
                             "url", "feedorderdesc"]
        missing_options = []
        for key in necessary_options:
            if not hasattr(self.__config, key):
                missing_options.append(key)
        return missing_options

    def get_missing_options(self):
        return self.__missing_options

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
