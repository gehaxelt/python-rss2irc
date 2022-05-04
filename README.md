Python RSS-2-IRC bot
====

This is a simple bot which fetches RSS feeds and posts them to an IRC channel.

# Requirements

- python3
- pip3
- venv (`Available by default in Python 3.3+`)

# Features

- Saves feeds and news items in a sqlite database
- Fetches every feed in a separate thread
- Posts new news items to an IRC channel
- Sends information via private messages
- SSL connection support
- Full utf-8 support
- Nick login support
- Delayed post during conversation
- Keywords in news title filtering support
- Customizable post colors
- Automatic join to channel on kick

# Bot's commands:

```
Help:
    Send all commands as a private message
    - !help         Prints this help
    - !list         Prints all feeds
    - !stats        Prints some statistics
    - !last         Prints the last 10 entries
    - !lastfeed <feedid> Prints the last 10 entries from a specific feed
```

# Setup 

Clone this repository and change into the directory. Create a new virtualenv and activate it:

```
python3 -m venv venv
source venv/bin/activate
```

Proceed with the installation of all dependencies:

```
pip3 install -r requirements.txt
```

Copy the sample files:

```
cp config.py.sample config.py
cp feeds.sql.sample feeds.sql
```

Edit `config.py` to fit your needs and IRC settings. All feeds from `feeds.sql` will be imported on the first start.

You might want to update all feeds before connecting to the IRC server to prevent spamming the channel (and optionally a ban from your IRC server). Either set `update_before_connecting = True` in the `config.py` or run the update script before starting the bot:

```
python3 feedupdater.py
```

To start the bot, run:
```
python3 main.py
```
    or in background:
```
python3 main.py 2>&1 > newsbot.log &
```

If you want to run this as a systemd service, you can use the `rss2irc.service` file after adjusting the paths in there.

# Adding feeds
To add a new feed, edit the `feeds.sql` and import it to your sqlite database:

```
sqlite3 feeds.db < feeds.sql
```

And restart the bot.

# License

See [LICENSE](./LICENSE.md) for more information.
