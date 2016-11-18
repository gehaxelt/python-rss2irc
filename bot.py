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

class IRCBot(irc.bot.SingleServerIRCBot):
    def __init__(self, config, db, on_connect_cb):
        self.__config = config
        self.__db = db
        self.__on_connect_cb = on_connect_cb
        self.__servers = [irc.bot.ServerSpec(self.__config.HOST, self.__config.PORT, self.__config.PASSWORD)]
        self.color_num = self.__config.num_col
        self.color_date = self.__config.date
        self.color_feedname = self.__config.feedname
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
        connection.privmsg(self.__config.CHANNEL, "Hi, I'm " + self.__get_colored_text('3',str(connection.get_nickname())) + " your bot. Send " + self.__get_colored_text(self.color_num,"!help") +" to get a list of commands.")
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
                    answer += "#" + self.__get_colored_text(self.color_num,str(entry[0])) + ": " + entry[1] + ", " + self.__get_colored_text('',str(entry[2])) + self.__get_colored_text(self.color_date,", updated every ") + self.__get_colored_text(self.color_num,str(entry[3])) + self.__get_colored_text(self.color_date," min") + "\n"

            # Print some simple stats (Feed / News count)
            elif msg == "!stats":
                feeds_count = self.__db.get_feeds_count()
                news_count = self.__db.get_news_count()
                answer = "Feeds: " + self.__get_colored_text(self.color_num,str(feeds_count)) + ", News: " + self.__get_colored_text(self.color_num,str(news_count))

            # Print last 25 news.
            elif msg == "!last":
                answer = ""
                for entry in self.__db.get_latest_news(self.__config.feedlimit)[::-1]:
                    answer += "#" + self.__get_colored_text(self.color_num,str(entry[0])) + ": " + entry[1] + ", " + self.__get_colored_text('',str(entry[2])) + ", " + self.__get_colored_text(self.color_date,entry[3]) + "\n"

            # Print last 25 news for a specific feed
            elif msg.startswith("!lastfeed"):
                answer = ""
                try:
                    feedid = int(msg.replace("!lastfeed","").strip())
                except:
                    return self.__get_colored_text('1',"Wrong command: ") + msg + ", use: !lastfeed <feedid>"
                for entry in self.__db.get_news_from_feed(feedid, self.__config.feedlimit)[::-1]:
                    answer += "#" + self.__get_colored_text(self.color_num,str(entry[0])) + ": " + entry[1] + ", " + self.__get_colored_text('',str(entry[2])) + ", " + self.__get_colored_text(self.color_date,str(entry[3])) + "\n"

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
            msg = self.__get_colored_text(self.color_feedname,str(feed_name)) + ": " + title + ", " + self.__get_colored_text('',url) + ", " + self.__get_colored_text(self.color_date,str(date))
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
        self.__db = FeedDB(self.__config)
        self.__irc = IRCBot(self.__config, self.__db, self.on_started)
        self.__threads = []
        self.__connected = False

    def start(self):
        """Starts the IRC bot"""
        threading.Thread(target=self.__irc.start).start()

    def on_started(self):
        """Gets executed after the IRC thread has successfully established a connection."""
        if not self.__connected:
            print "Connected!"

            # Start one fetcher thread per feed
            for feed in self.__db.get_feeds():
                t = threading.Thread(target=self.__fetch_feed, args=(feed,))
                t.start()
                self.__threads.append(t)
            print "Started fetcher threads!"
            self.__connected = True

    def __fetch_feed(self, feed_info):
        """Fetches a RSS feed, parses it and updates the database and/or announces new news."""
        while 1:
            try:
                # Parse a feed's url
                news = feedparser.parse( feed_info[2] )

                # Reverse the ordering. Oldest first.
                for newsitem in news.entries[::-1]:
                    newstitle = newsitem.title
                    if self.__config.shorturls:
                        newsurl = tinyurl.create_one(newsitem.link) # Create a short link
                        if newsurl == "Error": #If that fails, use the long version
                            newsurl = newsitem.link
                    else:
                        newsurl = newsitem.link

                    # Try to get the published or updated date. Otherwise set it to 'no date'
                    try:
                        # Get date and parse it
                        newsdate = dateutil.parser.parse(newsitem.published)
                        # Format date based on 'dateformat' in config.py
                        newsdate = newsdate.strftime(self.__config.dateformat)

                    except Exception as e:
                        try:
                            # Get date and parse it
                            newsdate = dateutil.parser.parse(newsitem.updated)
                            # Format date based on 'dateformat' in config.py
                            newsdate = newsdate.strftime(self.__config.dateformat)

                        except Exception as e:
                            newsdate = "no date"

                    # Update the database. If it's a new issue, post it to the channel
                    is_new = self.__db.insert_news(feed_info[0], newstitle, newsitem.link, newsdate)
                    if is_new:
                        self.__irc.post_news(feed_info[1], newstitle, newsurl, newsdate)
                print "Updated: " + feed_info[1]
            except Exception as e:
                print e
                print "Failed: " + feed_info[1]

            # sleep frequency minutes
            time.sleep(int(feed_info[3])*60)
