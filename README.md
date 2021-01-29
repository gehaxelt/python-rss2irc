Python RSS-2-IRC bot
====

This is a simple bot which fetches RSS feeds and posts them to an IRC channel.

# Requirements

- python2
- pip
- virtualenv (`pip2 install virtualenv`)

# Features

- Saves feeds and news items in a sqlite database
- Fetches every feed in a separate thread
- Posts new news items to an IRC channel
- Sends information via private messages
- Full utf-8 support
- Nick login support
- Post delayed during conversation
- Keywords in news title filtering support
- Customizable post colors
- Automatic join to channel on kick

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

If you get an error that `sqlite3worker` couldn't be installed, use 

```
pip install git+https://github.com/palantir/sqlite3worker#egg=sqlite3worker
```

and retry the installation.

Copy the sample files:

```
cp config.py.sample config.py
cp feeds.sql.sample feeds.sql
```

Edit `config.py` to fit your needs and IRC settings. All feeds from `feeds.sql` will be imported on the first start.

You might want to update all feeds before connecting to the IRC server to prevent spamming the channel (and optionally a ban from your IRC server). Either set `update_before_connecting = True` in the `config.py` or run the update script before starting the bot:

```
python2 feedupdater.py
```

To start the bot, run:
```
python2 main.py
```
    or
```
python2 main.py 2>&1 > newsbot.log &
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
