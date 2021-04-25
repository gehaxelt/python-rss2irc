import ssl
import threading
import irc.bot
import irc.client
import irc.connection
import time
import re
import sys
import feedparser
import datetime
import requests
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
        self.color_feedname = self.__config.feedname
        self.color_newstitle = self.__config.newstitle
        self.color_url = self.__config.url
        self.color_date = self.__config.date
        self.shorturls = self.__config.shorturls
        self.dateformat = self.__config.dateformat
        self.filterkeywords = self.__config.filterkeywords

        if self.__config.SSL:
            ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
            print(datetime.datetime.now(), "Starting SSL connection.")
            sys.stdout.flush()
            super(IRCBot, self).__init__(self.__servers, self.__config.NICK, self.__config.NICK, connect_factory=ssl_factory)

        else:
            print(datetime.datetime.now(), "Starting connection.")
            sys.stdout.flush()
            super(IRCBot, self).__init__(self.__servers, self.__config.NICK, self.__config.NICK)

    def on_welcome(self, connection, event):
        """Login"""
        if self.__config.NICKPASS:
            print(datetime.datetime.now(), "Starting authentication.")
            sys.stdout.flush()
            self.send_msg("NickServ", "IDENTIFY {}".format(self.__config.NICKPASS))

        """Join the correct channel upon connecting"""
        if irc.client.is_channel(self.__config.CHANNEL):
            print(datetime.datetime.now(), "Joining to channel.")
            sys.stdout.flush()
            connection.join(self.__config.CHANNEL)

    def on_join(self, connection, event):
        """Say hello to other people in the channel. """
        if not self.__first_start:
            self.send_msg(self.__config.CHANNEL, self.welcome_msg())
            self.__on_connect_cb()
            self.__first_start = True

    def welcome_msg(self):
        msg = "Hi, I'm the channel " + self.get_bolded_text(self.__get_colored_text(self.color_feedname,"RSS")) + " news publishing bot v2.1. Send " + self.__get_colored_text(self.color_num,"!help") + " to receive a command list in private message (PM). If you find me annoying, you can to use " + self.__get_colored_text(self.color_num,"/IGNORE " + self.connection.get_nickname()) + " to stop reading me."
        time.sleep(1)
        return msg

    def on_kick(self, connection, event):
        """Join the correct channel again"""
        banned_nick = event.arguments[0].lower().strip()
        botnick = self.connection.get_nickname().lower()
        if irc.client.is_channel(self.__config.CHANNEL) and banned_nick == botnick:
            time.sleep(31)
            print(datetime.datetime.now(), "Joining to channel again.")
            sys.stdout.flush()
            connection.join(self.__config.CHANNEL)

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
                    answer += "# " + self.__get_colored_text(self.color_num,str(entry[0]) + "- ") + self.get_bolded_text(self.__get_colored_text(self.color_feedname,entry[1] + " > ")) + self.__get_colored_text(self.color_url,entry[2] + ",") + " updated every " + self.__get_colored_text(self.color_num,str(entry[3])) + " minutes." + "\n"

            # Print some simple stats (Feed / News count)
            elif msg == "!stats":
                feeds_count = self.__db.get_feeds_count()
                news_count = self.__db.get_news_count()
                answer = "Feeds: " + self.get_bolded_text(self.__get_colored_text(self.color_num,str(feeds_count))) + ", News: " + self.get_bolded_text(self.__get_colored_text(self.color_num,str(news_count)))

            # Print last config.feedlimit news.
            elif msg == "!last":
                answer = ""
                items = self.__db.get_latest_news(self.__config.feedlimit)
                if not self.__config.feedorderdesc:
                    items = items[::-1]

                for entry in items:
                    answer += "# " + self.__get_colored_text(self.color_num,str(entry[0]) + "- ") + self.get_bolded_text(self.__get_colored_text(self.color_newstitle,entry[1] + " > ")) + self.__get_colored_text(self.color_url,entry[2] + ", ") + self.__get_colored_text(self.color_date,str(entry[3])) + "\n"

            # Print last config.feedlimit news for a specific feed
            elif msg.startswith("!lastfeed"):
                answer = ""
                try:
                    feedid = int(msg.replace("!lastfeed","").strip())
                except:
                    return self.__get_colored_text('1',"Wrong command. ") + msg + ". Send !lastfeed <feedid>"
                items = self.__db.get_news_from_feed(feedid, self.__config.feedlimit)
                if not self.__config.feedorderdesc:
                    items = items[::-1]
                for entry in items:
                    answer += "# " + self.__get_colored_text(self.color_num,str(entry[0]) + "- ") + self.get_bolded_text(self.__get_colored_text(self.color_newstitle,entry[1] + " > ")) + self.__get_colored_text(self.color_url,entry[2] + ", ") + self.__get_colored_text(self.color_date,str(entry[3])) + "\n"

            # Else tell the user how to use the bot
            else:
                answer = "Send !help to see the available commands."
        except Exception as e:
            print(datetime.datetime.now(), e)
            sys.stdout.flush()
            answer = "Something was wrong."
        return answer

    def on_privmsg(self, connection, event):
        """Handles the bot's private messages"""
        if len(event.arguments) < 1:
            return

        # Get the message and return an answer
        msg = event.arguments[0].lower().strip()
        print(datetime.datetime.now(), msg, "command from", event.source.nick)
        sys.stdout.flush()
        answer = self.__handle_msg(msg)
        self.send_msg(event.source.nick, answer)
        time.sleep(5)

    def on_pubmsg(self, connection, event):
        Config.lastpubmsg = time.time()
        """Handles the bot's public (channel) messages"""
        if len(event.arguments) < 1:
            return
        # Get the message. We are only interested in "!help" or botnick
        msg = event.arguments[0].lower().strip()
        botnick = self.connection.get_nickname()
        # Send the answer as a private message
        if msg == "!help":
            self.send_msg(event.source.nick, self.__help_msg())
        # Send the answer as a public message
        if botnick.lower() in msg:
            self.send_msg(self.__config.CHANNEL, self.welcome_msg())

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
                    time.sleep(2) # Don't flood the target
                    self.connection.privmsg(target, sub_line)
        except Exception as e:
            print(datetime.datetime.now(), e)
            sys.stdout.flush()

    def post_news(self, feed_name, title, url, date):
        """Cancel post if filter keyword is in title"""
        for keyword in self.filterkeywords:
            if keyword in title.lower():
                print(datetime.datetime.now(), "Found", keyword, "keyword in title. Aborting post.")
                sys.stdout.flush()
                return
        """Try shortening url"""
        if self.__config.shorturls:
            try:
                post_url = self.shorten(url)
                if ("error" in post_url.lower()):
                    post_url = url
            except Exception as e:
                post_url = url
                print(datetime.datetime.now(), e)
                sys.stdout.flush()
        else:
            post_url = url
        """Posts a new announcement to the channel"""
        try:
            msg = self.__get_colored_text(self.color_feedname,feed_name + ": ") + self.get_bolded_text(self.__get_colored_text(self.color_newstitle,title)) + " > " + self.__get_colored_text(self.color_url,post_url + ", ") + self.__get_colored_text(self.color_date,str(date))
            self.send_msg(self.__config.CHANNEL, msg)
        except Exception as e:
            print(datetime.datetime.now(), e)
            sys.stdout.flush()

    def shorten(self, url):
        try: # Trying to shorten URL
            sresponse = requests.get('https://v.gd/create.php?format=json&url=' + url)
            surl = sresponse.json()['shorturl']
        except Exception as err:
            print('A shortening error occurred.')
            surl = url
        return surl

    def __get_colored_text(self, color, text):
        if not self.__config.use_colors:
            return text

        return Colours(color, text).get()

    def get_bolded_text(self, string):
        """Returns the string bolded."""
        return "\002" + string + "\002"

    def __help_msg(self):
        """Returns the help/usage message"""
        return """\
Help:
    - /IGNORE """ + self.connection.get_nickname() + """ - Lets you stop reading the bot.

  You can send these commands in private message (PM) to """ + self.connection.get_nickname() + """:
    - !help - Show this help message.
    - !stats - Show some statistics.
    - !list - Show all feeds.
    - !last - Show last news published in all feeds.
    - !lastfeed <feedid> - Show last news published in a specific feed.
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
        necessary_options = ["HOST", "PORT", "PASSWORD", "SSL", "CHANNEL",
        "use_colors", "num_col", "feedname", "newstitle", "url", "date", "shorturls", "dateformat", "feedlimit",
        "postdelay", "feedorderdesc", "update_before_connecting", "filterkeywords"]
        missing_options = []
        for key in necessary_options:
            if not hasattr(self.__config, key):
                missing_options.append(key)
        return missing_options

    def get_missing_options(self):
        return self.__missing_options

    def start(self):
        """Starts the IRC bot"""
        print(datetime.datetime.now(), "Starting bot.")
        sys.stdout.flush()
        threading.Thread(target=self.__irc.start).start()

    def initial_feed_update(self):
        def print_feed_update(feed_title, news_title, news_url, news_date):
            print(datetime.datetime.now(), "[+]: {}||{}||{}||{}".format(feed_title, news_title, news_url, news_date))
            sys.stdout.flush()

        if self.__config.update_before_connecting:
            print(datetime.datetime.now(), "Starting offline update.")
            sys.stdout.flush()
            self.__feedupdater.update_feeds(print_feed_update, False)

    def on_started(self):
        """Gets executed after the IRC thread has successfully established a connection."""
        if not self.__connected:
            print(datetime.datetime.now(), "Starting feeds periodic update...")
            sys.stdout.flush()
            self.__feedupdater.update_feeds(self.__irc.post_news, True)
            self.__connected = True
