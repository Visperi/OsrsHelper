# OsrsHelper
Discord bot made mainly for Old school Runescape related commands, although nowadays it has several other commands too.

**Very spaghetti code btw** because this was my very first project in coding after an Python basics university course. I apologize for no documentation and the code being in finnish. I'll be updating things to be more understandable as fast as I can.

# Source made with
- Python 3.6
- `Beautifulsoup4` version 4.6.0
- `discord.py` version 0.16.12 **not rewrite**
- `pytz` version 2018.3
- `tabulate` version 0.8.2

Code should work with newer versions of these modules if no major updates are not made. Only exception is discord.py which will **not** work if updated to rewrite.

# Installation
Unfortunately the bot is not currently guaranteed to work without downloading both finnish and english versions. Also, timestamps are currently wrong if you live outside of gmt +2. These are the first things I will be working on as much as I have time.

1. Download everything in this repository. move **all** files into the same directory with all .py files
2. Empty all data files you want. When you do this, leave one `{}` brackets in emptied .json files. Following files can safely be emptied without causing any differences in bot functionality:
   - Custom_commands.json
   - Item_keywords.json
   - Tracked_players.json
   - droprates.json
   - statsdb.json
   - streamers.json
   
   You can safely modify the default settings in settings.ini if you know what you're doing.
3. Install Python 3.6+ and every needed module
4. Register the bot into discord api with your account and copy your token into file Credentials.json
5. Run Main.py

## Licence
MIT License

Full licence: [LICENCE](/LICENCE)
