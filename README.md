# OsrsHelper v6.2

**Update on 28/11/2018:
I have now started rewriting this bot into newest discord.py (rewrite) and decided that no major feature updates will be made into this one. I will upload the rewrite version as soon as its somewhat working and applicable enough.**

Discord bot made mainly for Old school Runescape related commands, although nowadays it has several other commands too. It was started in october 2015 as a very small project just to check item prices in G.E. Things got bigger and now it has commands for clues, users stats and gains, custom item keywords and custom server commands. I thought long about publishing this code, but now I finally decided to do it.

**Very spaghetti code btw** because this was my very first project in coding after a Python basics university course. I apologize that there is no documentation and the code is in finnish. I'll be updating things to be more understandable as much as I can. However, the bot works and it has pretty straightforward help commands.

### Main features
- 41 hard coded commands ([Full list](/commands_list.txt), bad formatting but somewhat readable)
- Compact but straightforward help messages for every command
- Up to 200 server specific custom commands
- Add keywords for tradeable items to check price
- Manage roles who can add or delete commands and keywords
- Full Osrs clue support (excluding map and Falo steps)

All my available free time goes currently into rewriting the bot instead of improving this one. An exception can be made if something very good comes into my mind. Maintaining this version is guaranteed at least as long as the rewrite version is uploaded.

# Source made with
- Python 3.6
- `Beautifulsoup4` version 4.6.0
- `discord.py` version 0.16.12 **not rewrite**
- `tabulate` version 0.8.2

Code should work with newer versions of these modules if no major updates are not made. Only exception is discord.py which will **not** work if updated to rewrite.

# Installation
Unfortunately the bot is not currently guaranteed to work without downloading both finnish and english versions.

1. Download everything in this repository. move **all** files into the same directory with all .py files
2. Empty all data files you want. When you do this, leave one `{}` brackets in emptied .json files. Following files can safely be emptied without causing any differences in bot functionality:
   - Custom_commands.json
   - Item_keywords.json
   - Tracked_players.json
   - droprates.json
   - statsdb.json
   - streamers.json
   
   You can safely modify the default settings in settings.ini if you know what you're doing.
3. Install Python 3.6+ and every needed module (Use `check_modules.py` to see which modules are not installed in your system)
4. Register the bot into discord api with your account and copy your secret token into file Credentials.json
5. Add the bot into a server, run Main.py and get further help with command `!help`

#### Following permissions are needed for full functionality

- Manage roles (Only role bot can manage is `Streams` for command `!streamers`)
- Read text channels & See voice channels
- Send messages
- Read message history
- Add reactions (Bot will only react when subscribing or unsuscribing role Streams or tracking a player)

# Todo
- [x] Fix timestamps to work in any timezone  **Done. Timestamps are always in UTC now.**
- [] Translate the code into english
- [] Make the code work without downloading finnish version
- [] Make the prefix customizable
- [] More server specific settings

Incomplete todos are so far cancelled for this project. However, they will be supported in the rewrite version.

## Licence
MIT License

Full licence: [LICENCE](/LICENCE)
