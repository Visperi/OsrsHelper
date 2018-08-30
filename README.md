# OsrsHelper
Discord bot made mainly for Old school Runescape related commands, although nowadays it has several other commands too.

**Very spaghetti code btw** because this was my very first project in coding. I apologize for no documentation and the code being in finnish. I'll be updating things to be more understandable as fast as I can.

# Source made with
- Python 3.6
- `Beautifulsoup4` version 4.6.0
- `discord.py` version 0.16.12 **not rewrite**
- `pytz` version 2018.3
- `tabulate` version 0.8.2

Code should work with newer versions of these modules if no major updates are not made. Only exception is discord.py which will **not** work if updated to rewrite.

# Installation
Unfortunately the bot is not currently guaranteed to work without downloading both finnish and english versions. This is something im going to work on (+ adding your own languages)

1. Download everything and move files in data files into same directory with .py files
2. Empty all data files you want. When you do this, leave one `{}` brackets in emptied .json files. Following files can safely be emptied without causing any differences in bot functionality:
   - Custom_commands.json
   - Item_keywords.json
   - Tracked_players.json
   - droprates.json
   - statsdb.json
   - streamers.json
   
   You can safely modify the default settings in settings.ini if you know what you're doing.

## Licence
MIT License

Full licence: [LICENCE](/LICENCE)
