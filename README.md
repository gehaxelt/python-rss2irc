Python RSS-2-IRC bot
====

This is a simple bot which fetches RSS feeds and posts them to an IRC channel.

# Requirements

- python2
- pip
- virtualenv (`pip2 install virtualenv`)

# Features

- Saves feeds and newsitems in a sqlite database
- Fetches every feed in a seperate thread
- Posts new newsitems to an IRC channel
- Sends information via private messages

# Bot's commands:

```
Help:
    Send all commands as a private message to Feed
    - !help         Prints this help
    - !list         Prints all feeds
    - !stats        Prints some statistics
    - !last         Prints the last 25 entries
    - !lastfeed <feedid> Prints the last 25 entries from a specific feed
```

# Setup 

Clone this repository and change into the directory. Create a new virtualenv and activate it:

```
virtualenv venv
. venv/bin/activate
```

Proceed with the installation of all dependencies:

```
pip install -r requirements.txt
```

Copy the sample files:

```
cp config.py.sample config.py
cp feeds.sql.sample feeds.sql
```

Edit `configs.py` to fit your needs and IRC settings. All feeds from `feeds.sql` will be imported one the first start.

To start the bot, run:

```
python2 main.py
```

# Adding feeds
To add a new feed, edit the `feeds.sql` and import it to your sqlite database:

```
sqlite3 feeds.db < feeds.sql
```

And restart the bot.