"""
MIT License

Copyright (c) 2020 Visperi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# coding=utf-8

import aiohttp
import json
import datetime
from tabulate import tabulate
from dateutil.relativedelta import relativedelta
from typing import Union


def to_utf8(string):
    string = string.replace("Ã¤", "ä").replace("Ã¶", "ö").replace("/ae", "ä").replace("/oe", "ö").replace("Ã„", "Ä")\
        .replace("Ã–", "Ö").replace("Â§", "§").replace("/ss", "§")
    return string


def to_ascii(string):
    string = string.replace("ä", "/ae").replace("ö", "/oe").replace("Ä", "/AE").replace("Ö", "/OE").replace("§", "/ss")
    return string


async def make_request(session: aiohttp.ClientSession, url: str, timeout: int = 8) -> str:
    """
    A non-command function for making an asynchronous request.

    :param session: aiohttp.ClientSession that is used to make request
    :param url: Target url of the request
    :param timeout: Integer telling how long should be waited before timeouting the request
    :return: String containing the response
    """

    async with session.get(url, timeout=timeout) as r:
        response = await r.text()
        return response


async def get_item_data(itemname: str) -> Union[None, dict]:
    item_data = None

    with open("Data files/Tradeables.json", "r") as tradeables_file:
        tradeable_data = json.load(tradeables_file)

    try:
        item_data = tradeable_data[itemname.capitalize()]
        item_data["name"] = itemname.capitalize()
    except KeyError:
        with open("Data files/Item_keywords.json", "r", encoding="utf-8") as keywords_file:
            keywords_data = json.load(keywords_file)

        for key, keywords in keywords_data.items():
            if key == "All keywords":
                continue
            if itemname in keywords:
                item_data = tradeable_data[key]
                item_data["name"] = key
                break

    return item_data


def string_to_timedelta(time_string: str) -> relativedelta:
    """
    Convert string from format '[years][months][days][hours][minutes][seconds]' to relativedelta object. Any time unit
    can be left out if not needed.

    :param time_string: Relative time in string format
    :return: datetutil.relativedelta.relativedelta object
    """

    replace_dict = {"years": "yrs",
                    "yrs": "y",
                    "months": "mon",
                    "mon": "m",
                    "days": "d",
                    "hours": "H",
                    "h": "H",
                    "minutes": "min",
                    "min": "M",
                    "seconds": "sec",
                    "sec": "S",
                    "s": "S",
                    " ": ""}

    for old in replace_dict.keys():
        new = replace_dict[old]
        time_string = time_string.replace(old, new)

    time_units = {"y": 0, "m": 0, "d": 0, "H": 0, "M": 0, "S": 0}

    # Extract all different time units from string
    for char in time_string:
        if char not in list(time_units):
            continue

        char_idx = time_string.find(char)
        time_units[char] = int(time_string[:char_idx])

        target_substring = time_string[:char_idx + 1]
        time_string = time_string.replace(target_substring, "")

    years = time_units["y"]
    months = time_units["m"]
    days = time_units["d"]
    hours = time_units["H"]
    minutes = time_units["M"]
    seconds = time_units["S"]

    timedelta = relativedelta(years=years, months=months, days=days, hours=hours, minutes=minutes, seconds=seconds)
    return timedelta


async def make_scoretable(user_stats: list, username: str, account_type: str, gains: bool = False,
                          saved_ts: datetime.datetime = None) -> str:
    """
    A non-command function for other functions to ask for making user hiscores into a easy-to-read table.

    :param user_stats: List of list containing user hiscores
    :param username: Username of the user which hiscores are handled
    :param account_type: Acconut type of the user
    :param gains: Boolean that tells if requested table is for gains command
    :param saved_ts: Timestamp for the last time command !gains was used for this user. Needed only if gains == True!
    :return: String that has a tabulate table inside of a Discord command block
    """

    skillnames = ["Total", "Attack", "Defence", "Strength", "Hitpoints", "Ranged", "Prayer", "Magic", "Cooking",
                     "Woodcutting", "Fletching", "Fishing", "Firemaking", "Crafting", "Smithing", "Mining",
                     "Herblore", "Agility", "Thieving", "Slayer", "Farming", "Runecrafting", "Hunter",
                     "Construction"]
    cluenames = ["All", "Beginner", "Easy", "Medium", "Hard", "Elite", "Master"]

    skills = user_stats[:24]
    clues = user_stats[27:34]

    # Iterate through all hiscore data and separate thousands with comma, and add sign if gains
    for index, list_ in enumerate(user_stats):
        for index2, value in enumerate(list_):
            if gains:
                separated = f"{value:+,}"
            else:
                separated = f"{value:,}"
            user_stats[index][index2] = separated

    # Add skill and clue names
    for i, skill in enumerate(skills):
        skill.insert(0, skillnames[i])
    for i, clue in enumerate(clues):
        clue.insert(0, cluenames[i])

    skilltable = tabulate(skills, tablefmt="orgtbl", headers=["Skill", "Rank", "Level", "Xp"])
    cluetable = tabulate(clues, tablefmt="orgtbl", headers=["Clue", "Rank", "Amount"])

    if gains:
        utc_now = datetime.datetime.utcnow().replace(microsecond=0, second=0)
        utc_now = utc_now.strftime("%Y-%m-%d %H:%M")
        saved_ts = saved_ts.strftime("%Y-%m-%d %H:%M")
        table_header = "{:^50}\n{:^50}\n{}".format(f"Gains of {username.capitalize()}",
                                                   f"Account type: {account_type.capitalize()}",
                                                   f"Between {saved_ts} - {utc_now} UTC")
    else:
        if account_type.lower() == "normal":
            table_header = "{:^50}".format(f"Stats of {username.capitalize()}")
        else:
            table_header = "{:^54}".format(f"{account_type.capitalize()} Stats of {username.capitalize()}")

    scoretable = f"```{table_header}\n\n{skilltable}\n\n{cluetable}```"
    return scoretable


async def get_hiscore_data(username: str, aiohttp_session: aiohttp.ClientSession, acc_type: str = None) -> list:
    """
    A non-command function for commands to ask for hiscores of Osrs accounts. Request is sent to Osrs API and then if
    successful, answer is parsed from string to a list of integers for easier handling.

    :param username: Username which hiscores are wanted
    :param aiohttp_session: aiohttp.ClientSession that is used to make the request
    :param acc_type: Optional account type if other than normal hiscores are needed
    :return: List of lists that has user current hiscores in format [[rank, xp, level], [rank, xp, level], ...]
    """

    if len(username) > 12:
        raise ValueError("Username can't be longer than 12 characters.")

    if acc_type == "normal" or acc_type is None:
        header = "hiscore_oldschool"
    elif acc_type == "ironman":
        header = "hiscore_oldschool_ironman"
    elif acc_type == "uim":
        header = "hiscore_oldschool_ultimate"
    elif acc_type == "dmm":
        header = "hiscore_oldschool_deadman"
    elif acc_type == "seasonal":
        header = "hiscore_oldschool_seasonal"
    elif acc_type == "hcim":
        header = "hiscore_oldschool_hardcore_ironman"
    elif acc_type == "tournament":
        header = "hiscore_oldschool_tournament"
    else:
        raise ValueError(f"Unknown account type: {acc_type}")

    url = f"http://services.runescape.com/m={header}/index_lite.ws?player={username}"
    user_stats = await make_request(aiohttp_session, url)

    if "404 - Page not found" in user_stats:
        raise TypeError(f"Username {username} does not exist.")

    user_stats = user_stats.split()
    user_stats = [x.split(",") for x in user_stats]

    # Convert all data into integers
    for skill in user_stats:
        for i, value in enumerate(skill):
            if value == "-1":
                skill[i] = 0
            else:
                skill[i] = int(value)

    return user_stats