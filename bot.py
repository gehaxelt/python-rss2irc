#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import irc.client
import tinyurl
import time
import re
import feedparser
from colour import Colours
from db import FeedDB
from config import Config

class IRCBot(irc.client.SimpleIRCClient):
    def __init__(self, config, db, on_connect_cb):
        irc.client.SimpleIRCClient.__init__(self)
        self.__config = config
        self.__db = db
        self.connect(self.__config.HOST, self.__config.PORT, self.__config.NICK)
        self.__on_connect_cb = on_connect_cb
        self.num_col = self.__config.num_col
        self.date = self.__config.date
        self.feedname = self.__config.feedname

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
                for entry in self.__db.get_latest_news()[::-1]:
                    answer += "#" + Colours(self.num_col,str(entry[0])).get() + ": " + entry[1] + ", " + Colours('',str(entry[2])).get() + ", " + Colours(self.date,entry[3]).get() + "\n"

            # Print last 25 news for a specific feed
            elif msg.startswith("!lastfeed"):
                answer = ""
                try:
                    feedid = int(msg.replace("!lastfeed","").strip())
                except:
                    return Colours('1',"Wrong command: ").get() + msg + ", use: !lastfeed <feedid>"
                for entry in self.__db.get_news_from_feed(feedid)[::-1]:
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
            msg = Colours(self.feedname,str(feed_name)).get() + ": " + title + ", " + url + ", " + Colours(self.date,str(date)).get()
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
    - !last         Prints the last 25 entries
    - !lastfeed <feedid> Prints the last 25 entries from a specific feed
"""

class Bot(object):
    def __init__(self):
        self.__db = FeedDB()
        self.__config = Config()
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
                    newsurl = tinyurl.create_one(newsitem.link) # Create a short link
                    if newsurl == "Error": #If that fails, use the long version
                        newsurl = newsitem.link
                    newsurl = Colours('', newsurl).get()

                    # Try to get the published date. Otherwise set it to 'no date'
                    try:
                        newsdate = newsitem.published
                    except Exception as e:
                        try:
                            newsdate = newsitem.updated
                        except Exception as e:
                            newsdate = "no date"

                    # Update the database. If it's a new issue, post it to the channel
                    is_new = self.__db.insert_news(feed_info[0], newstitle, newsurl, newsdate)
                    if is_new:
                        self.__irc.post_news(feed_info[1], newstitle, newsurl, newsdate)

                print Colours('7',"Updated: ").get() + feed_info[1]
            except Exception as e:
                print e
                print Colours('1',"Failed: ").get() + feed_info[1]

            # sleep frequency minutes
            time.sleep(int(feed_info[3])*60) 
