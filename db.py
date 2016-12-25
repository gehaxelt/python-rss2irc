#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlite3worker import Sqlite3Worker
import os

class FeedDB(object):
    def __init__(self, config):
        self.__db_path = "./feeds.db"
        self.__db_worker = None
        self.__config = config
        self.__initiate_db()

    def __initiate_db(self):
        """Create a DB connection"""

        # If the database doesn't exist, create and prepopulate it with feeds.sql
        if not os.path.exists(self.__db_path):
            self.__db_worker = Sqlite3Worker(self.__db_path)
            self.__db_worker.execute('CREATE TABLE feeds (id INTEGER PRIMARY KEY AUTOINCREMENT, name CHAR(200) UNIQUE, url CHAR(200) UNIQUE, frequency INTEGER(3))')
            self.__db_worker.execute('CREATE TABLE news (id INTEGER PRIMARY KEY AUTOINCREMENT, title CHAR(255), url CHAR(255), feedid INTEGER, published TEXT, FOREIGN KEY(feedid) REFERENCES feeds(id))')
            if os.path.exists("./feeds.sql"):
                f = open("./feeds.sql", "r")
                for insert in f.readlines():
                    self.__db_worker.execute(insert.strip())
                f.close()
        else:
            self.__db_worker = Sqlite3Worker(self.__db_path)

    def get_feeds(self):
        """Returns all feeds"""
        feeds = []
        for feed in self.__db_worker.execute("select id,name,url,frequency from feeds"):
            feeds.append(feed)
        return feeds

    def get_news_from_feed(self, feed_id, limit=10):
        """Returns 'limit' news from a specific feed"""
        news = []
        for item in self.__db_worker.execute("select id, title, url, published from news where feedid = :feedid order by id desc limit :limit", {'feedid': feed_id, 'limit':limit}):
            news.append(item)
        return news

    def get_latest_news(self, limit=10):
        """Returns 'limit' latest news"""
        news = []
        for item in self.__db_worker.execute("select id, title, url, published from news order by id desc limit :limit", {'limit':limit}):
            news.append(item)
        return news

    def get_feeds_count(self):
        """Returns the feed count"""
        count = self.__db_worker.execute("select count(id) from feeds")[0][0]
        return count

    def get_news_count(self):
        """Returns the news count"""
        count = self.__db_worker.execute("select count(id) from news")[0][0]
        return count

    def insert_news(self, feed_id, title, url, published):
        """Checks if a news item with the given information exists. If not, create a new entry."""
        exists = self.__db_worker.execute("select exists(select 1 FROM news WHERE feedid = :feedid and url = :url and published = :published LIMIT 1)", {'feedid': feed_id, 'url': url, 'published': published})[0][0]
        if exists:
            return False
        self.__db_worker.execute("INSERT INTO news (title, url, feedid, published) VALUES (:title, :url, :feedid, :published)", {'title': title, 'url': url, 'feedid': feed_id, 'published': published})
        return True
