# OsrsHelper v8.1

Discord bot made mainly for Old school Runescape related commands, although nowadays it is pretty much an all-around 
project for a few Discord servers. This allows me to make quick changes and updates to meet the user base needs. There 
is a newer version of this bot, [OsrsHelper-rewrite](https://github.com/Visperi/OsrsHelper-rewrite), which has a goal 
of doing everything better from the beginning. Both versions will keep getting updates, although the old version in 
much more regular basis since it already has a live userbase.

There is **Very ugly code** at some places since this was my very first project in coding. Newer code, which is usually 
closer to the end of files, should be more pleasant to read. I'm not planning to fully translate this project 
into English since the Discord library version is outdated. However, I may sometimes rewrite some old functions for 
the sake of efficiency or my own sanity. 

### Main features
- Over 40 hard coded commands
- Full support for both Finnish and English
- Compact help messages for every command
- Up to 200 server specific custom commands
- Add keywords for tradeable items to check price
- Manage roles who can add or delete commands and item keywords
- Full Osrs clue support (excluding map and Falo steps)

# Source made with
- Python 3.6
- `Beautifulsoup4` version 4.6.0
- `discord.py` version 0.16.12 **not rewrite**
- `tabulate` version 0.8.2

# Installation
Unfortunately the bot is not guaranteed to work without downloading both finnish and english versions.

1. Download everything in this repository. move **all** files into the same directory with all .py files
2. Empty all data files you want. When you do this, leave one `{}` brackets in emptied .json files. Following files 
can safely be emptied without causing any differences in bot functionality:

   - Custom_commands.json
   - Item_keywords.json
   - Tracked_players.json
   - droprates.json
   - statsdb.json
   - streamers.json
   
3. Use `check_modules.py` to see if you meet the requirements
4. Register the bot into discord api with your account and copy your secret token into file Credentials.json
5. Add the bot into a server, run Main.py and get further help with command `!help`

#### Following permissions are needed for full functionality

- Manage roles (Only role bot can manage is `Streams` for command `!streamers`)
- Read text channels & See voice channels
- Send messages
- Read message history
- Add reactions (Bot will only react when subscribing or unsuscribing role Streams or tracking a player)

## Licence
MIT License

Full licence: [LICENCE](/LICENCE)
