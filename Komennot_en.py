"""
MIT License

Copyright (c) 2018-2020 Visperi

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

import datetime
import json
import math
import os
import discord
import Settings
from fractions import Fraction
from bs4 import BeautifulSoup
from mathparse import mathparse
from dateutil.relativedelta import relativedelta
import asyncio
import numpy as np
from tabulate import tabulate
import aiohttp


def to_utf8(string):
    string = string.replace("Ã¤", "ä").replace("Ã¶", "ö").replace("/ae", "ä").replace("/oe", "ö").replace("Ã„", "Ä")\
        .replace("Ã–", "Ö")
    return string


def to_ascii(string):
    string = string.replace("ä", "/ae").replace("ö", "/oe").replace("Ä", "/AE").replace("Ö", "/OE")
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


async def command_help(message, keywords, client):
    command = " ".join(keywords).replace("!", "").replace("%", "").replace("&", "")
    if not command:
        msg = "`!info`: Basic info about the bot and latest updates\n" \
              "`!commands`: Get a list of all available commands\n" \
              "`!server commands`: Get a list of all custom commands for this server\n" \
              "`!help <command name>`: Get instructions for one command"
        await client.send_message(message.channel, msg)
        return
    with open("Data files/Help_en.json", encoding="utf-8") as data_file:
        data = json.load(data_file)
    for obj in data:
        if command in obj["function"]:
            name, description, additional, example = obj["name"], obj["description"], obj["additional"], obj["example"]
            await client.send_message(message.channel, f"**{name}**\n"
                                                       f"{description}\n\n"
                                                       f"**Additional:** {additional}\n"
                                                       f"**Example:** {example}")
            return
    await client.send_message(message.channel, "Could not find any command. Get a list of all available commands with "
                                               "`!commands`")


async def kayttajan_tiedot(message, client):

    try:
        avatar_url = message.author.avatar_url
        display_name = message.author.display_name

        created_at = message.author.created_at.replace(microsecond=0)
        joined_at = message.author.joined_at.replace(microsecond=0)

        roles = [str(role) for role in message.author.roles if str(role) != "@everyone"]
    except AttributeError:
        await client.send_message(message.channel, "This command doesn't work in direct messages.")
        return

    user_info = discord.Embed().set_author(name=display_name).set_thumbnail(url=avatar_url)\
        .add_field(name="Username", value=str(message.author))\
        .add_field(name="Id", value=message.author.id)\
        .add_field(name="User created", value=f"{created_at} UTC")\
        .add_field(name="Joined server", value=f"{joined_at} UTC")\
        .add_field(name="Roles in this server", value=", ".join(roles))
    await client.send_message(message.channel, embed=user_info)


async def commands(message, client):
    commands_dict = {"Discord commands": ["!info", "!help", "!calc", "!me", "!namechange", "!server commands",
                                          "!satokausi", "!beer", "!beerscores", "!korona", "!reminder"],
                     "Osrs commands": ["!wiki", "!stats", "!gains", "!track", "!xp", "!ehp", "!nicks", "!kill",
                                       "!update"],
                     "Item commands": ["!keys", "!limit", "!price"],
                     "Clue commands": ["!cipher", "!anagram", "!puzzle", "!cryptic", "!maps"],
                     "Mod commands": ["%addkey", "%delkey", "%addcom", "%delcom", "%editcom"],
                     "Settings commands": ["&language", "&settings", "&permit", "&unpermit", "&add commands",
                                           "&forcelang", "&defaultlang"]
                     }

    embed = discord.Embed(text="In case you need help in using commands, try !help <command>")
    embed.set_footer()

    for category in commands_dict.keys():
        category_commands = [command for command in commands_dict[category]]
        embed.add_field(name=category, value="\n".join(category_commands))

    await client.send_message(message.channel, embed=embed)


def get_iteminfo(itemname, default_names=False):
    """Searches for item name and id from local files.

    :param itemname: The name of the item in string format
    :param default_names: If set true, only default item names are accepted as itemname input
    :return: Original item name (str) and its id (int), None if not found
    """
    itemname = itemname.capitalize()
    with open("Data files/Tradeables.json") as data_file:
        data = json.load(data_file)
    if itemname in list(data.keys()):
        item_id = data[itemname]["id"]
        return itemname, item_id
    elif default_names:
        return
    else:
        itemname = to_ascii(itemname.lower())
        with open("Data files/Item_keywords.json") as data_file:
            keywords = json.load(data_file)
        if itemname in keywords["all nicks"]:
            for item in keywords:
                if itemname in keywords[item] and item != "all nicks":
                    itemname = to_utf8(item.capitalize())
                    item_id = data[itemname]["id"]
                    return itemname, item_id


async def search_wiki(message, hakusanat: list, client, get_html=False):
    baselink = "https://oldschool.runescape.wiki/w/"

    search = "_".join(hakusanat)
    search_link = baselink + search
    try:
        response = await make_request(client, search_link)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Wiki answered too slowly. Try again later..")
        return
    if f"This page doesn&#039;t exist on the wiki. Maybe it should?" in response:
        hyperlinks = []
        truesearch_link = f"https://oldschool.runescape.wiki/w/Special:Search?search={search}"
        try:
            truesearch_resp = await make_request(client, truesearch_link)
        except asyncio.TimeoutError:
            await client.send_message(message.channel, "Wiki answered too slowly. Try again later.")
            return

        # parse html
        results_html = BeautifulSoup(truesearch_resp, "html.parser")
        result_headings = results_html.findAll("div", class_="mw-search-result-heading")
        if len(result_headings) == 0:
            await client.send_message(message.channel, "Haullasi ei löytynyt yhtään sivua.")
            return
        for result in result_headings[:5]:
            link_end = result.find("a")["href"]
            if link_end[-1] == ")":
                link_end = list(link_end)
                link_end[-1] = "\\)"
                link_end = "".join(link_end)
            link_title = result.find("a")["title"]
            hyperlinks.append(f"[{link_title}](https://oldschool.runescape.wiki{link_end})")
        embed = discord.Embed(title="Tarkoititko jotain näistä", description="\n".join(hyperlinks))
        await client.send_message(message.channel, embed=embed)
    else:
        if get_html:
            return response
        await client.send_message(message.channel, f"<{search_link}>")
    kayttokerrat("Wiki")


async def search_cipher(message, search, client):
    search = " ".join(search).upper()
    partial_matches = []

    with open("Data files/Ciphers.json") as cipher_file:
        ciphers = json.load(cipher_file)

    for cipher in ciphers.keys():
        if search in cipher:
            partial_matches.append(cipher)
    if len(partial_matches) == 0:
        await client.send_message(message.channel, "Could not find any ciphers with your search. Please check the "
                                                   "spelling.")
    elif len(partial_matches) > 1:
        await client.send_message(message.channel, "Found {} ciphers with your search:\n{}"
                                  .format(len(partial_matches), "\n".join(partial_matches)))
    elif len(partial_matches) == 1:
        cipher = ciphers[partial_matches[0]]
        solution, location, answer, kuva = cipher["solution"], cipher["location"], cipher["answer"], cipher["kuva"]
        if not kuva:
            await client.send_message(message.channel, f"Solution: {solution}\nLocation: {location}\nAnswer: {answer}")
        else:
            await client.send_message(message.channel,
                                      f"Solution: {solution}\nLocation: {location}\nAnswer: {answer}\n{kuva}")
        kayttokerrat("cipher")


async def hae_puzzle(message, hakusanat, client, no_message=False):
    """ Linkkaa kuvan valmiista puzzlesta """

    u = " ".join(hakusanat).capitalize()
    if u in ["Zulrah", "Snake"]:
        puzzle = "http://i.imgur.com/6w15uIX.png"
    elif u in ["Gnome", "Gnome child"]:
        puzzle = "http://i.imgur.com/3vvjSpI.png"
    elif u in ["Cerberus"]:
        puzzle = "http://i.imgur.com/dWIRvYd.png"
    elif u in ["Troll"]:
        puzzle = "http://i.imgur.com/eOtjKiL.png"
    elif u in ["Tree"]:
        puzzle = "http://i.imgur.com/JSmP3bF.png"
    elif u in ["Castle"]:
        puzzle = "http://i.imgur.com/Kz8INkv.png"
    else:
        await client.send_message(message.channel, "Couldn't find any puzzles with your keyword.")
        return
    if no_message:
        return puzzle
    else:
        await client.send_message(message.channel, puzzle)


async def search_anagram(message, hakusanat, client):
    partial_matches = []
    search = " ".join(hakusanat)
    with open("Data files/Anagrams.json") as anagram_file:
        anagrams = json.load(anagram_file)

    try:
        anagram = anagrams[search]
        solution = anagram["solution"]
        location = anagram["location"]
        challenge_ans = anagram["challenge_ans"]
        puzzle = anagram["puzzle"]
        msg = f"Solution: {solution}\nLocation: {location}\nChallenge answer: {challenge_ans}\n{puzzle}"
        await client.send_message(message.channel, msg)
    except KeyError:
        for anagram in anagrams.keys():
            if search in anagram:
                partial_matches.append(anagram)
        matches = len(partial_matches)
        if matches == 1:
            anagram = anagrams[partial_matches[0]]
            solution = anagram["solution"]
            location = anagram["location"]
            challenge_ans = anagram["challenge_ans"]
            puzzle = anagram["puzzle"]
            msg = f"Solution: {solution}\nLocation: {location}\nChallenge answer: {challenge_ans}\n{puzzle}"
            await client.send_message(message.channel, msg)
        elif matches < 11:
            await client.send_message(message.channel, "Found {} anagrams with your search:\n{}\n\nTry giving a more "
                                                       "specific search.".format(matches, "\n".join(partial_matches)))
        elif matches > 10:
            await client.send_message(message.channel, "Found more than 10 anagrams with your search. Try giving a "
                                                       "more specific search.")
        else:
            await client.send_message(message.channel, "Could not find any anagrams.")


async def experiencelaskuri(message, hakusanat, client):
    x = "".join(hakusanat).replace("-", " ").replace("max", "127").split()

    with open("Data files/Experiences.txt", "r") as file:
        all_rows = file.readlines()
        experiences = []
        for row in all_rows:
            experiences.append(row.replace(",", "").split())
        if len(x) == 1:
            try:
                x[0] = int(x[0])
            except ValueError:
                await client.send_message(message.channel, "Level must be an integer.")
                return
            if int(x[0]) > 127:
                await client.send_message(message.channel, "You gave too big level. The maximum level is 127 or max.")
            else:
                for exp in experiences:
                    if str(x[0]) == exp[0]:
                        if exp[0] == "127":
                            await client.send_message(message.channel, "Xp needed for the max level: {:,}"
                                                      .format(int(exp[1])).replace(",", " "))
                        else:
                            await client.send_message(message.channel, "Xp needed for level {}: {:,}"
                                                      .format(x[0], int(exp[1])).replace(",", " "))
                        kayttokerrat("Xp")
        elif len(x) == 2:
            try:
                lvl_isompi = int(x[1])
                lvl_pienempi = int(x[0])
            except ValueError:
                await client.send_message(message.channel, "Levels must be integers.")
                return
            if lvl_isompi > 127 or lvl_pienempi > 127:
                await client.send_message(message.channel, "You gave too big level. The maximum level is 127 or max.")
                return
            if lvl_isompi >= lvl_pienempi:
                for exp in experiences:
                    if x[1] == exp[0]:
                        lvl_isompi = int(exp[1])
                    if x[0] == exp[0]:
                        lvl_pienempi = int(exp[1])
                xp_erotus = lvl_isompi - lvl_pienempi
                if x[1] == "127":
                    x[1] = "max"
                if x[0] == "127":
                    x[0] = "max"
                await client.send_message(message.channel, "Xp needed in level gap {}-{}: {:,}"
                                          .format(x[0], x[1], xp_erotus).replace(",", " "))
                kayttokerrat("Xp")
            else:
                await client.send_message(message.channel, "Never go full retard.")


async def laskin(message, hakusanat, client):
    equation = " ".join(hakusanat).replace("^", " ^ ").replace("**", " ^ ").replace(",", ".").replace("+", " + ") \
        .replace("-", " - ").replace("*", " * ").replace("/", " / ")
    try:
        solution = mathparse.parse(equation)
    except IndexError:
        await client.send_message(message.channel, "The equation was in unsupported format. Try again by putting some "
                                                   "parts in brackets or check the supported operations with "
                                                   "command `!help calc`.")
        return
    except ValueError:
        await client.send_message(message.channel, "The calculator could not evaluate some part of the equation. All "
                                                   "unsupported operations are not known yet, so try to put some parts "
                                                   "in brackets.")
        return
    except KeyError:
        await client.send_message(message.channel, "The equation had some factors that were not convertible to "
                                                   "numbers.")
        return
    except OverflowError:
        await client.send_message(message.channel, "The solution was too big to be calculated with this command.")
        return
    if type(solution) is str:
        solution_formatted = solution
    else:
        solution_formatted = f"{round(solution, 3):,}".replace(",", " ")
    await client.send_message(message.channel, solution_formatted)


async def ehp_rates(message, hakusanat, client):
    otsikko = hakusanat[0].capitalize()
    filename = "Ehp.txt"
    if message.content.startswith("!ironehp"):
        filename = "Ehp_ironman.txt"
    elif message.content.startswith("!skillerehp"):
        filename = "Ehp_skiller.txt"
    elif message.content.startswith("!f2pehp"):
        filename = "Ehp_free.txt"
    file = f"Data files/{filename}"

    with open(file, "r") as file:
        lines = file.read().split("\n\n")
        skills = []
        for skill in lines:
            skills.append(skill)
        for skill in skills:
            if otsikko in skill:
                taulukko = "\n".join(skill.replace("{}:\n".format(otsikko), "{}\n".format(otsikko)).split("\n"))
                await client.send_message(message.channel, taulukko)
                break


async def execute_custom_commands(message, user_input, client):
    try:
        server = message.server.id
    except AttributeError:
        return
    command = user_input.replace("!", "")

    with open("Data files/Custom_commands.json") as data_file:
        data = json.load(data_file)
    try:
        viesti = data[server]["!{}".format(to_ascii(command))]["message"]
    except KeyError:
        return
    await client.send_message(message.channel, to_utf8(viesti))
    kayttokerrat("custom")


async def addcom(message, words_raw, client):
    words = " ".join(words_raw)
    file = "Data files/Custom_commands.json"
    server = str(message.server.id)
    if not await Settings.get_settings(message, client, get_addcom=True):
        await client.send_message(message.channel, "Adding commands has been switched off.")
        return
    if len(words_raw) < 2:
        await client.send_message(message.channel, "Please give both the command and the message.")
        return

    def convert(string):
        a = string.find("\"")
        if a == -1 or string[-1] != "\"" or string.count("\"") < 2:
            return
        string_list = list(string)
        string_list[a], string_list[-1] = "[start]", "[end]"
        if string_list[a - 1] != " ":
            string_list[a - 1] += " "
        string = "".join(string_list)
        start = string.find("[start]") + 7
        end = string.find("[end]")
        viesti_raw = to_ascii(string[start:end]).replace("\\n", "\n")
        komento_raw = to_ascii(" ".join(string[:start - 8].split(" ")[0:]))
        komento = komento_raw.replace("!", "")
        try:
            if not komento[0].isalpha() and not komento[0].isdigit():
                komento = list(komento)
                komento[0] = "!"
                komento = "".join(komento)
            elif komento[0].isalpha() or komento[0].isdigit():
                komento = "!" + komento
            return komento.lower(), viesti_raw, komento_raw
        except IndexError:
            raise IndexError

    try:
        command, viesti, command_raw = convert(words)
        if len(command_raw) > 30:
            raise ValueError
        if "[end]" in command and "start]" in command:
            await client.send_message(message.channel, "You gave an incorrect input. Give the command first and then "
                                                       "the message inside quotation marks. For help use command "
                                                       "`!help addcom`.")
            return
    except TypeError:
        await client.send_message(message.channel, "The message of command must begin and end with quotation marks. "
                                                   "Give the command first and then the message. Don't include "
                                                   "anything else into your message.")
        return
    except IndexError:
        await client.send_message(message.channel, "The command's name can't consist only of exclamation marks. "
                                                   "They will be always removed and thus this command would be an "
                                                   "empty string.")
        return
    except ValueError:
        await client.send_message(message.channel, f"The maximum length for command is 30 characters. Yours was "
                                                   f"{len(command_raw)}.")
        return
    with open(file) as data_file:
        data = json.load(data_file)
    try:
        server_commands = list(data[server])
        if command in server_commands:
            await client.send_message(message.channel, f"Command `{command}` already exists.")
            return
        elif len(server_commands) > 199:
            await client.send_message(message.channel, "Maximum amount of commands is 200. This has already been "
                                                       "reached in this guild.")
            return
    except KeyError:
        data[server] = {}
    data[server][command] = {"message": viesti}

    with open(file, "w") as data_file:
        json.dump(data, data_file, indent=4)
    await client.send_message(message.channel, "Command `{}` added.".format(to_utf8(command)))
    if (command_raw[0] == "!" and command_raw.count("!") > 1) or (command_raw[0] != "!" and command_raw.count("!") > 0):
        await client.send_message(message.channel, "Command's name cannot have any exclamation marks and they were "
                                                   "removed automatically.")
    kayttokerrat("addcom")


async def get_custom_commands(message, client):
    try:
        server = message.server.id
    except AttributeError:
        await client.send_message(message.channel, "This command can't be used in direct messages.")
        return
    custom_commands = []
    with open("Data files/Custom_commands.json") as data_file:
        data = json.load(data_file)
    custom_commands_raw = list(data[server])
    if len(custom_commands_raw) == 0:
        await client.send_message(message.channel, "Server doesn't have any custom commands.")
        return
    for command in custom_commands_raw:
        custom_commands.append(to_utf8(command))
    embed = discord.Embed(title=f"Custom commands for {str(message.server).capitalize()}")
    embed.set_footer(text=f"Total amount of commands: {len(custom_commands)}")

    # Separates all custom commands into lists of 15 commands
    field_list = []
    list_index = 0
    field_amount = math.ceil(len(custom_commands) / 15)
    for x in range(field_amount):
        field_list.append([])
    for command in custom_commands:
        current_list = field_list[list_index]
        current_list.append(command)
        if len(current_list) == 15:
            list_index += 1
    for field in field_list:
        embed.add_field(name=f"{field_list.index(field) + 1}", value="\n".join(field))
    await client.send_message(message.channel, embed=embed)


async def cryptic(message, hakusanat, client):
    user_input = " ".join(hakusanat).lower()
    keys_found = []

    with open("Data files/cryptic_clues.json") as data_file:
        data = json.load(data_file)
    for key in data.keys():
        if user_input in key.lower():
            keys_found.append(key)
    if len(keys_found) == 1:
        solution = data[keys_found[0]]["solution"]
        image = data[keys_found[0]]["image"]
        await client.send_message(message.channel, f"{solution}\n{image}")
        kayttokerrat("cryptic")
    elif len(keys_found) == 0:
        await client.send_message(message.channel, "Couldn't find any clues with your keyword.")
        return
    else:
        if len("\n".join(keys_found)) > 2000:
            await client.send_message(message.channel, "Found several clues and they wont fit into one message field. "
                                                       "Try to particularize your search.")
            return
        await client.send_message(message.channel, "Found {} clues with your search:\n\n{}"
                                  .format(len(keys_found), "\n".join(keys_found)))
        return


async def mapit(message, client):
    await client.send_message(message.channel, "<https://oldschool.runescape.wiki/w/Treasure_Trails/Guide/Maps>")


async def delcom(message, words_raw, client):
    komento = " ".join(words_raw)
    server = message.server.id
    file = "Data files/Custom_commands.json"
    if not komento[0].isalpha() and not komento[0].isdigit():
        komento = list(komento)
        komento[0] = "!"
        komento = "".join(komento)
    elif komento[0].isalpha() or komento[0].isdigit():
        komento = "!" + komento
    komento = to_ascii(komento)
    with open(file) as data_file:
        data = json.load(data_file)
    if komento in list(data[server]):
        del data[server][komento]
        with open(file, "w") as data_file:
            json.dump(data, data_file, indent=4)
            await client.send_message(message.channel, "Command `{}` deleted.".format(to_utf8(komento)))
            kayttokerrat("delcom")
    else:
        await client.send_message(message.channel, "That command doesn't exist")


async def get_buylimit(message, keywords, client):
    keyword = " ".join(keywords)
    iteminfo = get_iteminfo(keyword)
    if not iteminfo:
        await client.send_message(message.channel, "Could not find any items with your keyword.")
        return
    else:
        itemname = iteminfo[0]
    with open("Data files/Buy_limits.json") as data_file:
        data = json.load(data_file)
    try:
        buy_limit = data[itemname]
    except KeyError:
        await client.send_message(message.channel, "Didn't find any buy limit for this item. If you find a mistake, "
                                                   "please inform about it and it will be fixed.")
        return
    await client.send_message(message.channel, f"Four hour buy limit for {itemname}: {buy_limit} pcs.")
    kayttokerrat("Limit")


def kayttokerrat(function_used):
    command = function_used.capitalize()
    current_date = datetime.datetime.now().strftime("%d/%m/%Y")
    with open("Data files/Times_used.json") as data_file:
        data = json.load(data_file)
    times = data[command]
    data[command] = times + 1
    if data["date_start"] == "":
        data["date_start"] = current_date
    data["date_now"] = current_date
    with open("Data files/Times_used.json", "w") as data_file:
        json.dump(data, data_file, indent=4)


async def change_name(message, hakusanat, client):
    tiedosto = "Data files/Tracked_players.json"
    nimet = " ".join(hakusanat).replace(", ", ",")

    async def confirm_change(vanha, uusi):
        bot_message = await client.send_message(message.channel, "Are you sure you want to change name {} -> {}?"
                                                .format(vanha, uusi))
        await client.add_reaction(bot_message, "✅")
        await client.add_reaction(bot_message, "❌")
        answer = await client.wait_for_reaction(emoji=["✅", "❌"], message=bot_message, user=message.author, timeout=5)
        if not answer:
            await client.edit_message(bot_message, "No answer. Name change cancelled.")
            return
        elif answer.reaction.emoji == "✅":
            await client.edit_message(bot_message, "Name changed successfully!")
            return True
        elif answer.reaction.emoji == "❌":
            await client.edit_message(bot_message, "Name change cancelled.")
            return

    if "," not in nimet:
        await client.send_message(message.channel, "Please separate the old and new name with comma.")
        return
    nimet = nimet.split(",")
    old_name = nimet[0]
    new_name = nimet[1]
    old_name = old_name.lower()
    new_name = new_name.lower()
    with open(tiedosto) as data_file:
        data = json.load(data_file)
    if new_name in list(data):
        await client.send_message(message.channel, "The new name is already in lists.")
    elif old_name in list(data):
        try:
            check_name = await make_request(client, f"http://services.runescape.com/m=hiscore_oldschool/index_lite.ws"
                                                    f"?player={new_name}")
        except asyncio.TimeoutError:
            await client.send_message(message.channel, "Osrs API answered too slowly. Try again later.")
            return
        if "404 - Page not found" in check_name:
            await client.send_message(message.channel, "User with the new name not found.")
            return
        confirmed = await confirm_change(old_name, new_name)
        if confirmed:
            old_names = data[old_name]["previous_names"]
            if old_name not in old_names:
                old_names.append(old_name)
            data[new_name] = data.pop(old_name)
            with open(tiedosto, "w") as data_file:
                json.dump(data, data_file, indent=4)
            with open("Data files/statsdb.json") as data_file:
                stats_data = json.load(data_file)
            stats_data[new_name] = stats_data.pop(old_name)
            with open("Data files/statsdb.json", "w") as data_file:
                json.dump(stats_data, data_file, indent=4)
        else:
            return
    else:
        await client.send_message(message.channel,
                                  "The old name is not tracked. For users not tracked before use command `!track`. If "
                                  "you think you shouldn't get this message, contact the bot owner.")


async def addkey(message, keywords, client):
    keywords = " ".join(keywords).replace(", ", ",").split(",")
    itemname = keywords[0].capitalize()
    new_keys = keywords[1:]
    denied_msg = ""
    approved_keys = []
    discarded_keys = 0
    with open("Data files/Tradeables.json") as tradeables:
        all_tradeables = json.load(tradeables)
    with open("Data files/Item_keywords.json") as data_file:
        data = json.load(data_file)
    if itemname not in all_tradeables.keys():
        await client.send_message(message.channel, "Could not find any items with your keyword.")
        return
    if len(new_keys) == 0:
        await client.send_message(message.channel, "Please give at least one new keyword for the item.")
        return
    if itemname not in data.keys():
        data[itemname.lower()] = []
    for key in new_keys:
        key = to_ascii(key)
        if "*" in key:
            discarded_keys += 1
            continue
        elif key not in data["all nicks"] and key not in all_tradeables.keys():
            data["all nicks"].append(key)
            data[itemname.lower()].append(key)
            approved_keys.append(to_utf8(key))
    if discarded_keys > 0:
        denied_msg = f"{discarded_keys} of the keys were discarded because they contained `*` signs."
    if len(approved_keys) == 0:
        await client.send_message(message.channel, f"Kaikki antamasi avainsanat ovat varattuja. {denied_msg}")
        return
    else:
        with open("Data files/Item_keywords.json", "w") as data_file:
            json.dump(data, data_file, indent=4)
            await client.send_message(message.channel, "Added following items for {}: `{}`. {}"
                                      .format(itemname, ", ".join(approved_keys), denied_msg))
    kayttokerrat("Addkey")


async def delkey(message, keywords, client):
    file = "Data files/Item_keywords.json"
    keywords = " ".join(keywords).replace(", ", ",").split(",")
    itemname = keywords[0]
    deletelist = keywords[1:]
    deleted_keys = []
    item_info = get_iteminfo(itemname, default_names=True)
    if not item_info:
        await client.send_message(message.channel, "Could not find any items with your keyword.")
        return
    if len(deletelist) == 0 or deletelist[0] == "":
        await client.send_message(message.channel, "Please give at least one keyword for the item you want to delete.")
        return
    with open(file) as data_file:
        data = json.load(data_file)
    try:
        item_keys = data[itemname]
        delete_keys = []
    except KeyError:
        await client.send_message(message.channel, "Item has not been set any keywords.")
        return
    for keyword in deletelist:
        keyword = to_ascii(keyword)
        if keyword in item_keys:
            delete_keys.append(keyword)
    if len(delete_keys) == 0:
        await client.send_message(message.channel, "None of the keywords are set for this item.")
        return
    for key in delete_keys:
        data[itemname].remove(key)
        data["all nicks"].remove(key)
        deleted_keys.append(to_utf8(key))
    if len(data[itemname]) == 0:
        data.pop(itemname)
    deleted_keys = ", ".join(deleted_keys)
    with open(file, "w") as data_file:
        json.dump(data, data_file, indent=4)
    await client.send_message(message.channel,
                              f"The following keywords were deleted from {itemname.capitalize()}: `{deleted_keys}`.")
    kayttokerrat("Delkey")


async def find_itemname(message, hakusanat, client, vanilla_names=False):
    print(hakusanat)
    itemname = to_ascii(" ".join(hakusanat)).capitalize()
    print(itemname)
    with open("Data files/Tradeables.json") as data_file:
        data = json.load(data_file)
    try:
        item_id = data[itemname]["id"]
        return itemname, item_id
    except KeyError:
        if not vanilla_names:
            with open("Data files/Item_keywords.json") as nicks_file:
                nicks_dict = json.load(nicks_file)
            if itemname in nicks_dict["all nicks"]:
                for item in nicks_dict:
                    if itemname in nicks_dict[item] and item != "all nicks":
                        itemname = item.capitalize()
                        item_id = data[itemname]
                        return itemname, item_id
            else:
                await client.send_message(message.channel, "Couldn't find any items with your keyword.")
                return
        else:
            await client.send_message(message.channel, "Item not found.")


async def get_keys(message, hakusanat, client):
    itemname = " ".join(hakusanat).lower()
    nicks_utf8 = []
    iteminfo = get_iteminfo(itemname, default_names=True)
    if not iteminfo:
        await client.send_message(message.channel, "Could not find any items with your keyword.")
        return
    with open("Data files/Item_keywords.json") as data_file:
        data = json.load(data_file)
    try:
        nicks_ascii = data[itemname]
        for nick in nicks_ascii:
            nicks_utf8.append(to_utf8(nick))
        embed = discord.Embed(title=f"Keywords for {itemname.capitalize()}", description="\n".join(nicks_utf8))
        await client.send_message(message.channel, embed=embed)
    except KeyError:
        await client.send_message(message.channel, "This item has not been set any keywords.")


async def latest_update(message, client):
    news_articles = {}
    articles = []

    link = "http://oldschool.runescape.com/"
    try:
        osrs_response = await make_request(client, link)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Osrs frontpage answered too slowly. Try again later.")
        return

    osrs_response_html = BeautifulSoup(osrs_response, "html.parser")

    for div_tag in osrs_response_html.findAll("div", attrs={"class": "news-article__details"}):
        p_tag = div_tag.p
        h3_tag = div_tag.h3

        # Somehow the article types always end in space
        article_type = div_tag.span.contents[0][:-1]
        article_link = p_tag.a["href"]
        article_number = p_tag.a["id"][-1]
        article_title = h3_tag.a.text
        article_date = div_tag.time["datetime"]

        news_articles[article_number] = {"link": article_link, "type": article_type}
        articles.append(f"**{article_title}** ({article_type}) ({article_date})\n<{article_link}>")

    await client.send_message(message.channel, "\n\n".join(articles))


async def editcom(message, words_raw, client):
    words = " ".join(words_raw)
    file = "Data files/Custom_commands.json"
    server = str(message.server.id)
    with open(file) as data_file:
        data = json.load(data_file)

    def convert(string):
        a = string.find("\"")
        if a == -1 or string[-1] != "\"" or string.count("\"") < 2:
            return
        string_list = list(string)
        string_list[a], string_list[-1] = "[start]", "[end]"
        if string_list[a - 1] != " ":
            string_list[a - 1] += " "
        string = "".join(string_list)
        start = string.find("[start]") + 7
        end = string.find("[end]")
        viesti_raw = to_ascii(string[start:end]).replace("\\n", "\n")
        komento = to_ascii(" ".join(string[:start - 8].split(" ")[0:])).replace("!", "")
        if not komento[0].isalpha() and not komento[0].isdigit():
            komento = list(komento)
            komento[0] = "!"
            komento = "".join(komento)
        elif komento[0].isalpha() or komento[0].isdigit():
            komento = "!" + komento
        return komento.lower(), viesti_raw

    try:
        command, viesti_edited = convert(words)
    except TypeError:
        await client.send_message(message.channel, "The message of command must begin and end with quotation marks. "
                                                   "Give the command first and then the message. Don't include anything"
                                                   " else into your message.")
        return
    try:
        if command in list(data[server]):
            old_message = data[server][command]["message"]
            if viesti_edited != old_message:
                data[server][command]["message"] = viesti_edited
            else:
                await client.send_message(message.channel, "The new message can't be same as before.")
                return
        else:
            await client.send_message(message.channel, "That command doesn't exist.")
            return
    except KeyError:
        await client.send_message(message.channel, "Server has not set any custom commands.")
        return
    with open(file, "w") as data_file:
        json.dump(data, data_file, indent=4)
    await client.send_message(message.channel, "Edited command `{}`.".format(command))


async def get_old_nicks(message, hakusanat, client):
    search = " ".join(hakusanat)
    with open("Data files/Tracked_players.json") as data_file:
        data = json.load(data_file)
    try:
        old_nicks = data[search]["previous_names"]
    except KeyError:
        await client.send_message(message.channel, "This user is not tracked.")
        return
    if len(old_nicks) == 0:
        await client.send_message(message.channel, "Could not find any old nicknames for this user.")
        return
    embed = discord.Embed(title=f"Stored old nicks for {search}", description="\n".join(old_nicks))
    await client.send_message(message.channel, embed=embed)


async def get_times_used(message, client):
    commands_list = []
    with open("Data files/Times_used.json") as data_file:
        data = json.load(data_file)
    dates = "{} - {}".format(data["date_start"], data["date_now"])
    for item in data:
        if item == "date_start" or item == "date_now":
            continue
        commands_list.append(f"{item}: {data[item]}")
    await client.send_message(message.channel, "```{}\n\n{}```".format(dates, "\n".join(commands_list)))


async def bot_info(message, client, release_notes=False) -> None:
    """
    A command function for command !info to get basic bot info.

    :param message:
    :param client:
    :param release_notes:
    """

    with open("Data files/changelog_en.txt", "r", encoding="utf-8") as file:
        changelog = file.read()
    if release_notes:
        embed = discord.Embed(title="Latest updates", description=changelog)
    else:
        appinfo = await client.application_info()
        bot_name = appinfo.name
        bot_owner = appinfo.owner
        last_modified = datetime.datetime.fromtimestamp(os.path.getmtime("Main.py")).strftime("%d/%m/%Y")
        created_at = client.user.created_at.replace(microsecond=0)
        embed = discord.Embed(title=bot_name, description=f"Developer: {bot_owner.mention}\n"
                                                          f"Updated: {last_modified}\nSource code: Python 3.6 "
                                                          f"([Source](https://github.com/Visperi/OsrsHelper))\n"
                                                          f"Created at: {created_at} UTC")
        embed.add_field(name="Credits",
                        value="[discord.py](https://github.com/Rapptz/discord.py) (Source code)\n"
                              "[Crystalmathlabs](http://www.crystalmathlabs.com/tracker/) (EHP rates)\n"
                              "[Old school runescape](http://oldschool.runescape.com/) (Highscores, G.E. prices, Game "
                              "news)\n"
                              "[OSRS Wiki](https://oldschool.runescape.wiki) (Wiki)", inline=False)
        embed.add_field(name="Latest updates", value=changelog)
        embed.set_thumbnail(url=appinfo.icon_url)
    await client.send_message(message.channel, embed=embed)
    kayttokerrat("Info")


async def sub_to_role(message, client, unsub=False):
    sub_role = "streams"
    server_roles = {}
    user_roles = message.author.roles

    for server_role in message.server.roles:
        server_roles[str(server_role).lower()] = server_role
    try:
        if unsub:
            if server_roles[sub_role] not in user_roles:
                return
            await client.remove_roles(message.author, server_roles[sub_role])
        elif not unsub:
            if server_roles[sub_role] in user_roles:
                return
            await client.add_roles(message.author, server_roles[sub_role])
        await client.add_reaction(message, "\N{THUMBS UP SIGN}")
    except KeyError:
        await client.send_message(message.channel, "This server doesn't have role Streams.")
    except discord.errors.Forbidden:
        await client.send_message(message.channel, "My role doesn't have permission to manage roles or react to "
                                                   "messages. Role has to be added and removed manually.")
    except AttributeError:
        await client.send_message(message.channel, "This command does not work in direct messages.")


async def get_streamers(message, client):
    final_list = []

    def streamer_display_name(user_id):
        name = discord.utils.get(message.server.members, id=user_id).display_name
        return name

    with open("Data files/streamers.json") as data_file:
        data = json.load(data_file)
    try:
        streamers_list = data[message.server.id]
    except KeyError:
        await client.send_message(message.channel, "This server doesn't have any streamers listed.")
        return
    for streamer in streamers_list:
        display_name = streamer_display_name(streamer)
        username = streamers_list[streamer]["username"]
        stream_link = streamers_list[streamer]["stream_link"]
        final_list.append(f"- {display_name} ({username}) [Stream link]({stream_link})")
    embed = discord.Embed(title=f"Listed streamers for {message.server.name}",
                          description="\n".join(final_list))
    await client.send_message(message.channel, embed=embed)


async def add_droprate(message, keywords, client):
    keywords = " ".join(keywords).replace(", ", ",").split(",")
    try:
        if len(keywords) == 2:
            dropper, itemname, droprate = "Misc", keywords[0].capitalize(), Fraction(keywords[1].replace(" ", ""))
        else:
            dropper, itemname, droprate = keywords[0].capitalize(), keywords[1].capitalize(), \
                                          Fraction(keywords[2].replace(" ", ""))
    except ValueError:
        await client.send_message(message.channel, "Please give first the name of the thing that gives the drop "
                                                   "(if there is any). After that give the itemname and droprate. "
                                                   "Separate the three parameters with commas.")
        return
    with open("Data files/droprates.json") as data_file:
        data = json.load(data_file)
    try:
        if itemname in data[dropper]:
            await client.send_message(message.channel, "This entity already has a droprate for this item.")
            return
    except KeyError:
        data[dropper] = {}

    if droprate > 1:
        droprate = Fraction(1, droprate)
    data[dropper][itemname] = str(droprate)

    with open("Data files/droprates.json", "w") as data_file:
        json.dump(data, data_file, indent=4)
    await client.send_message(message.channel, f"Saved droprate into a file:\n\n**Dropper**: {dropper}\n"
                                               f"**Itemname**: {itemname}\n**Droprate**: {droprate}")


async def loot_chance(message, keywords, client):

    def calculate_chance(attempts: int, rate: float):
        """
        Calculate the chance for a drop with given attempts and drop rate.

        :param attempts: Amount of kills/tries as an int
        :param rate: Drop rate for the drop as a float
        :return: String that has the chance to get the drop in percents
        """
        chance = (1 - (1 - rate) ** attempts) * 100
        if chance < 0.01:
            chance = "< 0.01%"
        elif chance > 99.99:
            chance = "> 99.99%"
        else:
            chance = f"{chance:.2f}%"
        return chance

    with open("Data files/droprates.json") as rates_file:
        drop_rates_dict = json.load(rates_file)

    target_input_list = keywords
    try:
        amount = int(target_input_list[0])
        boss_name = " ".join(target_input_list[1:])
    except ValueError:
        await client.send_message(message.channel, "The amount of kills must be an integer. Give kills first and then "
                                                   "the boss name.")
        return

    # Convert some most common nicknames to the full names
    if boss_name in ["corp", "corpo"]:
        boss_name = "corporeal beast"
    elif boss_name == "cerb":
        boss_name = "cerberus"
    elif boss_name == "sire":
        boss_name = "abyssal sire"
    elif boss_name == "kq":
        boss_name = "kalphite queen"
    elif boss_name in ["bando", "bandos"]:
        boss_name = "general graardor"
    elif boss_name == "mole":
        boss_name = "giant mole"
    elif boss_name == "kbd":
        boss_name = "king black dragon"
    elif boss_name in ["kreearra", "arma"]:
        boss_name = "kree'arra"
    elif boss_name == "thermo":
        boss_name = "thermonuclear smoke devil"
    elif boss_name == "vetion":
        boss_name = "vet'ion"
    elif boss_name in ["zilyana", "sara", "zily"]:
        boss_name = "commander zilyana"
    elif boss_name == "zammy":
        boss_name = "k'ril tsutsaroth"
    elif boss_name == "hydra":
        boss_name = "alchemical hydra"
    elif boss_name in ["cox", "raid", "raids", "raids 1", "olm"]:
        boss_name = "chambers of xeric"

    try:
        boss_rates = drop_rates_dict[boss_name]
    except KeyError:
        await client.send_message(message.channel, "Could not find a boss with that name.")
        return

    # Loop through all item drop rates for boss and add them to list
    drop_chances = []
    for item_drop_rate in boss_rates.items():
        itemname = item_drop_rate[0]
        drop_rate_frac = Fraction(item_drop_rate[1])
        drop_rate = float(drop_rate_frac)
        if boss_name == "chambers of xeric":
            drop_rate = float(drop_rate_frac) * 30000
        drop_chance = calculate_chance(amount, drop_rate)
        drop_chances.append(f"**{itemname}:** {drop_chance}")

    drop_chances_joined = "\n".join(drop_chances)
    await client.send_message(message.channel, f"Chances to get loot in {amount} kills from {boss_name.capitalize()}:"
                                               f"\n\n{drop_chances_joined}")


async def delete_droprate(message, keywords, client):
    keywords = " ".join(keywords).replace(", ", ",").split(",")
    with open("Data files/droprates.json") as data_file:
        data = json.load(data_file)
    if len(keywords) == 2:
        target, itemname = keywords[0].capitalize(), keywords[1].capitalize()
        if target in data:
            try:
                del data[target][itemname]
            except KeyError:
                await client.send_message(message.channel, "Droprate for this item has not been saved for this target.")
                return
        else:
            await client.send_message(message.channel, "The target doesn't have any droprates saved.")
            return
        with open("Data files/droprates.json", "w") as data_file:
            json.dump(data, data_file, indent=4)
        await client.send_message(message.channel, f"Removed droprate {itemname} from {target}.")
    elif len(keywords) == 1:
        try:
            if keywords[0].capitalize() in data["Misc"]:
                del data["Misc"][keywords[0].capitalize()]
                with open("Data files/droprates.json", "w") as data_file:
                    json.dump(data, data_file, indent=4)
                await client.send_message(message.channel, f"Removed droprate {keywords[0].capitalize()}.")
                return
        except KeyError:
            await client.send_message(message.channel, "This item doesn't have droprate or you forgot to give a "
                                                       "target which drops it.")
            return
        await client.send_message(message.channel, "Removing a whole categories is not in use yet. You can delete "
                                                   "droprates one at a time if you give the target name first.")


async def itemspecs(message, hakusanat, client) -> None:
    """
    Soon to be deprecated/rewritten command function for command !iteminfo. Attempts to find any stats or data of given
    item. If successful, sends all gathered data in an Discord embed.

    :param message:
    :param hakusanat:
    :param client:
    :return:
    """

    footer = ""
    ignore_list = ["Toxic blowpipe (empty)", "Trident of the seas (full)", "Trident of the seas (empty)",
                   "Serpentine helm (uncharged)"]

    def check_aliases(name):
        correct_name = name
        if name == "Lava cape":
            correct_name = "Fire cape"
        elif name == "Tentacle whip":
            correct_name = "Abyssal tentacle"
        return correct_name

    with open("Data files/itemstats.json") as data_file:
        data = json.load(data_file)
    try:
        itemname, item_id = get_iteminfo(" ".join(hakusanat))
        tradeable = True
        if itemname in ignore_list:
            raise TypeError
    except TypeError:
        itemname = check_aliases(" ".join(hakusanat).capitalize())
        tradeable = False
    try:

        itemdata = data[itemname]  # Löytyy tiedostosta itemstats.json
        itemstats = itemdata["stats"]
        description = itemdata["description"]
        members = itemdata["members"]
        icon = itemdata["icon"]
    except KeyError:
        if tradeable:
            link = f"http://services.runescape.com/m=itemdb_oldschool/api/catalogue/detail.json?item={item_id}"
            try:
                geapi_resp = await make_request(client, link)
            except asyncio.TimeoutError:
                await client.send_message(message.channel, "Osrs API answered too slowly and no item stats could be"
                                                           " gathered.")
                return
            itemdata = json.loads(geapi_resp)["item"]
            description = itemdata["description"]
            members = itemdata["members"].capitalize()
            icon = itemdata["icon_large"]
        else:
            description, members, icon = "-", "-", ""

        wiki_resp = await search_wiki(message, itemname.split(), client, get_html=True)
        try:
            soup = BeautifulSoup(wiki_resp, "html.parser")
        except TypeError:
            await client.send_message(message.channel, "Could not find any items with your search. Untradeable items "
                                                       "dont support using keywords.")
            return
        headings = soup.findAll("td", class_="smwprops")
        itemstats = None
        for a in headings:
            b = a.text.replace(" ", "").strip("+")
            if b.startswith("{") and b.endswith("}"):
                try:
                    itemstats = json.loads(b)
                    break
                except json.decoder.JSONDecodeError:
                    footer = "Could not parse the item stats. This is probably because the item has multiple " \
                             "variations of it in game and needs to be added manually."
        if type(itemstats) is dict:
            data[itemname] = {"description": description,
                                  "members": members,
                                  "icon": icon,
                                  "stats": itemstats
                              }
            with open("Data files/itemstats.json", "w") as data_file:
                json.dump(data, data_file, indent=4)
    embed = discord.Embed(title=itemname).add_field(name="Description", value=description, inline=False)
    attack_speed = ""
    members = members
    itemslot = ""
    icon = icon

    if not itemstats and description == "-":
        await client.send_message(message.channel, "Found an untradeable item with no stats with your search. "
                                                   "This embed would be empty.")
        return
    elif itemstats:
        astab = itemstats["astab"]
        aslash = itemstats["aslash"]
        acrush = itemstats["acrush"]
        amagic = itemstats["amagic"]
        arange = itemstats["arange"]
        dstab = itemstats["dstab"]
        dslash = itemstats["dslash"]
        dcrush = itemstats["dcrush"]
        dmagic = itemstats["dmagic"]
        drange = itemstats["drange"]
        str_ = itemstats["str"]
        rstr = itemstats["rstr"]
        mdmg = itemstats["mdmg"]
        prayer = itemstats["prayer"]
        slot = itemstats["slot"]
        itemslot = f"Slot: {slot}"

        try:
            speed = itemstats["speed"]
            attack_speed = f"Speed: {speed} (Hit interval {round(int(speed) * 0.6, 2)}s)"
        except KeyError:
            attack_speed = ""

        offensive = f"Stab: {astab}\n" \
            f"Slash: {aslash}\n" \
            f"Crush: {acrush}\n" \
            f"Magic: {amagic}\n" \
            f"Ranged: {arange}"
        defensive = f"Stab: {dstab}\n" \
            f"Slash: {dslash}\n" \
            f"Crush: {dcrush}\n" \
            f"Magic: {dmagic}\n" \
            f"Ranged: {drange}"
        other = f"Str bonus: {str_}\n" \
            f"Ranged str: {rstr}\n" \
            f"Magic damage: {mdmg}\n" \
            f"Prayer bonus: {prayer}"

        embed.add_field(name="Attack bonuses", value=offensive)
        embed.add_field(name="Defence bonuses", value=defensive)
        embed.add_field(name="Other bonuses", value=other)

    misc = f"Members: {members}\n" \
        f"{itemslot}\n" \
        f"{attack_speed}"
    embed.add_field(name="Misc", value=misc)
    if icon != "":
        embed.set_thumbnail(url=icon)
    embed.set_footer(text=footer)
    await client.send_message(message.channel, embed=embed)


async def item_price(message, hakusanat, client) -> None:
    """
    A command function for command !price to get current item price and price changes from Osrs API. If successful,
    sends the data in an Discord embed. Also supports multipliers for calculating price for multiple pieces of
    same item, e.g. '!price item * 10'.

    :param message: Message that invoked this command
    :param hakusanat: Message content as a list
    :param client: Bot client that is responsible of work between code and Discord client
    :return:
    """

    search = " ".join(hakusanat).replace(" * ", "*").split("*")
    try:
        itemname, itemid = get_iteminfo(search[0])
    except TypeError:
        await client.send_message(message.channel, "Could not find any items with your search.")
        return
    api_link = f"http://services.runescape.com/m=itemdb_oldschool/api/graph/{itemid}.json"
    try:
        multiplier = search[1]
        if multiplier[-1] == "k":
            multiplier = int(multiplier[:-1]) * 1000
        elif multiplier[-1] == "m":
            multiplier = int(multiplier[:-1]) * 1000000
        else:
            multiplier = int(multiplier)
    except IndexError:
        multiplier = 1
    except ValueError:
        await client.send_message(message.channel, "Unsupported character in coefficient. The coefficient supports "
                                                   "only abbreviations `k` and `m`.")
        return
    try:
        resp = await make_request(client.aiohttp_session, api_link)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Osrs API answered too slowly. Kokeile myöhemmin Try again later.")
        return

    data = json.loads(resp)
    daily_data = data["daily"]
    timestamps = list(daily_data.keys())
    latest_ts = timestamps[-1]
    day_ts = timestamps[-2]
    week_ts = timestamps[-7]
    month_ts = timestamps[-31]
    latest_price = int(daily_data[latest_ts])

    latest_price_formal = f"{latest_price:,}".replace(",", " ")
    latest_price_total = f"{latest_price * multiplier:,}".replace(",", " ")

    pc_month = "{:+,}".format(latest_price - int(daily_data[month_ts])).replace(",", " ")
    pc_week = "{:+,}".format(latest_price - int(daily_data[week_ts])).replace(",", " ")
    pc_day = "{:+,}".format(latest_price - int(daily_data[day_ts])).replace(",", " ")
    if multiplier != 1:
        pcs = f"({multiplier} kpl)"
        price_ea = f" ({latest_price_formal} ea)"
    else:
        pcs = ""
        price_ea = ""

    embed = discord.Embed(title=f"{itemname} {pcs}")
    embed.add_field(name="Latest price", value=f"{latest_price_total} gp{price_ea}", inline=False)
    embed.add_field(name="Price changes", value=f"In a month: {pc_month} gp\n"
                                                  f"In a week: {pc_week} gp\n"
                                                  f"In a day: {pc_day} gp", inline=False)
    embed.set_footer(text=f"Latest price from {datetime.datetime.utcfromtimestamp(int(latest_ts) / 1e3)} UTC")
    await client.send_message(message.channel, embed=embed)


async def add_drinks(message, client) -> None:
    """
    A command function for command !drink/!beer to increment user drinks in server hiscores.

    :param message: Message that invoked this command
    :param client: Bot client responsible of work between code and Discord client
    """

    user_id = message.author.id
    try:
        server_id = message.server.id
    except AttributeError:
        await client.send_message(message.channel, "This command doesn't support direct messages.")
        return

    with open("Data files/drinks.json", "r") as data_file:
        drink_data = json.load(data_file)

    try:
        server_data = drink_data[server_id]
    except KeyError:
        drink_data[server_id] = {}
        server_data = drink_data[server_id]

    try:
        server_data[user_id] += 1
    except KeyError:
        server_data[user_id] = 1

    with open("Data files/drinks.json", "w") as output_file:
        json.dump(drink_data, output_file, indent=4)

    await client.add_reaction(message, "a:BeerTime:689922747606106227")

    user_drinks = server_data[user_id]
    mod50 = user_drinks % 50
    mod100 = user_drinks % 100

    if mod50 == 0 and mod100 != 0:
        await client.send_message(message.channel, f"{message.author.display_name} achieved {user_drinks} drinks "
                                                   f"milestone <a:blobbeers:693529052371222618>")
    elif mod100 == 0:
        await client.send_message(message.channel, f"\U0001F973 {message.author.display_name} achieved "
                                                   f"{user_drinks} drinks milestone! \U0001F973")


async def drink_highscores(message, client) -> None:
    """
    A command function for command !beerscores to display server specific drink hiscores.

    :param message: Message that invoked this command
    :param client: Bot client responsible of work between code and Discord client
    """

    try:
        server_id = message.server.id
    except AttributeError:
        await client.send_message(message.channel, "This command doesn't support direct messages.")
        return

    with open("Data files/drinks.json", "r") as data_file:
        drink_data = json.load(data_file)

    try:
        server_data = drink_data[server_id]
    except KeyError:
        await client.send_message(message.channel, "No alcohol have been drunk in this server yet "
                                                   "<:feelsbad:333731708405022721>")
        return

    sorted_scores = sorted(server_data, key=server_data.get, reverse=True)
    highscores = []

    for pos, user_id in enumerate(sorted_scores):
        if pos > 9:
            break

        try:
            member = message.server.get_member(user_id)
            display_name = member.display_name
        except AttributeError:
            display_name = "Unknown"

        if pos == 0:
            pos = "\N{FIRST PLACE MEDAL}"
        elif pos == 1:
            pos = "\N{SECOND PLACE MEDAL}"
        elif pos == 2:
            pos = "\N{THIRD PLACE MEDAL}"
        else:
            pos = f"{pos + 1}."

        highscores.append(f"{pos} {display_name} ({server_data[user_id]})")

    embed = discord.Embed(title="Users with the most alcohol drinked in this server", description="\n".join(highscores))

    await client.send_message(message.channel, embed=embed)


async def remove_drinks(message, client) -> None:
    """
    A command function for command !undrink/!unbeer to remove a drink from user in drink hiscores.

    :param message: Message that invoked this command
    :param client: Bot client that is responsible of work between code and Discord client
    """

    user_id = message.author.id
    try:
        server_id = message.server.id
    except AttributeError:
        await client.send_message(message.channel, "This command doesn't support direct messages.")
        return

    with open("Data files/drinks.json", "r") as data_file:
        drink_data = json.load(data_file)

    try:
        server_data = drink_data[server_id]
    except KeyError:
        await client.send_message(message.channel, "This server doesn't have any saved drinks.")
        return

    try:
        server_data[user_id] -= 1
    except KeyError:
        await client.send_message(message.channel, "You have not drank any drinks.")
        return

    if server_data[user_id] == 0:
        del server_data[user_id]
        if len(server_data) == 0:
            del drink_data[server_id]

    with open("Data files/drinks.json", "w") as output_file:
        json.dump(drink_data, output_file, indent=4)

    await client.add_reaction(message, "a:emiTreeB:693788789042184243")


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


async def add_reminder(message, client, hakusanat) -> None:
    """
    A command function for command !reminder to set a user specifid reminder. This reminder then mentions its owner
    with given custom messaage after given time interval. Supported time units are years, months, days, hours, minutes
    and seconds. Minimum reminder time is 10 seconds.

    :param message: Message that invoked this command
    :param client: Bot client that is responsible of work between code and Discord client
    :param hakusanat: Message content as a list
    :return:
    """

    # Minimum reminder time in seconds for easy and quick modifications
    min_secs = 10
    reminder_file = "Data files/reminders.json"
    ts_now = datetime.datetime.utcnow().replace(microsecond=0)
    user_string = " ".join(hakusanat)

    # Find the start and end indexes of reminder message
    i1, i2 = user_string.find("\""), user_string.rfind("\"")
    if i1 == i2:
        await client.send_message(message.channel, "The message needs to be in quotes.")
        return
    elif i1 < 1:
        await client.send_message(message.channel, "Please give a time for the timer")
        return

    time_string = user_string[:i1].rstrip()
    reminder_message = user_string[i1 + 1:i2]

    # Escape all mentions in the message to prevent mention spamming
    if reminder_message.count("@") > 0:
        escape_indexes = [i for i, char in enumerate(reminder_message) if char == "@"]
        escaped_message = list(reminder_message)
        offset = 0
        for idx in escape_indexes:
            escaped_message.insert(idx + offset, "\\")
            offset += 1
        reminder_message = "".join(escaped_message)

    try:
        # Set reminder time in minutes if time unit not specified
        reminder_time = relativedelta(minutes=int(time_string))
    except ValueError:
        try:
            reminder_time = string_to_timedelta(time_string)
        except ValueError:
            await client.send_message(message.channel, "Given time was not in supported format.")
            return

    # Convert the reminder time from relativedelta to datetime.datetime object so total seconds can be extracted
    reminder_time = ((ts_now + reminder_time) - ts_now)
    if reminder_time.total_seconds() < min_secs:
        await client.send_message(message.channel, f"The reminder time must be at least {min_secs} seconds.")
        return

    with open(reminder_file) as data_file:
        reminder_data = json.load(data_file)

    try:
        trigger_time = str(ts_now + reminder_time)
    except OverflowError:
        await client.send_message(message.channel, "Too big timer value :(")
        return
    try:
        ts_reminders = reminder_data[trigger_time]
    except KeyError:
        reminder_data[trigger_time] = []
        ts_reminders = reminder_data[trigger_time]

    ts_reminders.append({"channel": message.channel.id, f"message": reminder_message, "author": message.author.id})
    with open(reminder_file, "w") as data_file:
        json.dump(reminder_data, data_file, indent=4, ensure_ascii=False)

    await client.send_message(message.channel, f"Reminder set. I will remind you at {trigger_time} UTC")


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


async def get_user_stats(message: discord.Message, keywords: str, client: discord.Client) -> None:
    """
    A command function for command !stats to get current hiscores of given username. Hiscore type can be specified with
    giving more specific command invokation to get more accurate rankings (All users are always at least in normal
    hiscores). These user stats are then send in a nice tabulate table.

    :param message: Message that invoked this command
    :param keywords: Message content as a list
    :param client: Bot client responsible of all work in between code and Discord client
    """

    keywords = keywords.split()
    invoked_with = keywords[0]
    username = " ".join(keywords[1:])

    if invoked_with == "!stats":
        account_type = "normal"
    elif invoked_with == "!ironstats":
        account_type = "ironman"
    elif invoked_with == "!uimstats":
        account_type = "uim"
    elif invoked_with == "!dmmstats":
        account_type = "dmm"
    elif invoked_with == "!seasonstats":
        account_type = "seasonal"
    elif invoked_with == "!hcstats":
        account_type = "hcim"
    else:
        await client.send_message(message.channel, f"Unknown account type with invokation: {invoked_with}")
        return

    try:
        user_stats = await get_hiscore_data(username, client.aiohttp_session, acc_type=account_type)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Osrs API answered too slowly. Try again later..")
        return
    except TypeError:
        await client.send_message(message.channel, "Could not find hiscores for user with given account type.")
        return
    except ValueError:
        await client.send_message(message.channel, "Username can't be longer than 12 characters.")
        return

    scoretable = await make_scoretable(user_stats, username, account_type)
    await client.send_message(message.channel, scoretable)


async def get_user_gains(message: discord.Message, keywords: list, client: discord.Client) -> None:
    """
    A command function for getting progress of given username since usage of !track or last usage of this command. Given
    username must be tracked with command !track first to use this command. Right hiscore data are calculated based on
    given account type while tracking user. Additional argument '-noupdate' can be used to bypass overwriting the saved
    data in tracked players file.

    :param message: Message that invoked this command
    :param keywords: Message content as a list
    :param client: Bot client responsible of all work in between code and Discord client
    """

    keywords = " ".join(keywords)
    update = True

    arg_idx = keywords.find("-")
    if arg_idx != -1:
        keywords = keywords.split("-")
        argument = keywords[1]
        username = keywords[0].rstrip(" ")
        update = False
        if argument.lower() != "noupdate":
            await client.send_message(message.channel, f"Invalid argument: `{argument}`")
            return
    else:
        username = keywords

    with open("Data files/statsdb.json", "r") as db_file:
        data = json.load(db_file)
    try:
        saved_data = data[username]
    except KeyError:
        # Username is not in tracked players
        await client.send_message(message.channel, "This user is not tracked.")
        return

    account_type = saved_data["account_type"]
    saved_stats = saved_data["past_stats"]
    saved_ts = datetime.datetime.fromtimestamp(saved_data["saved"])

    try:
        new_stats = await get_hiscore_data(username, client.aiohttp_session, acc_type=account_type)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Osrs API answered too slowly. Try again later.")
        return

    len_diff = len(new_stats) - len(saved_stats)
    if len_diff > 0:
        for _ in range(len_diff):
            saved_stats.append([0, 0])

    new_skills_arr = np.array(new_stats[:24], dtype=int)
    new_minigames_arr = np.array(new_stats[24:], dtype=int)

    saved_skills_arr = np.array(saved_stats[:24], dtype=int)
    saved_minigames_arr = np.array(saved_stats[24:], dtype=int)

    skills_difference = new_skills_arr - saved_skills_arr
    minigames_difference = new_minigames_arr - saved_minigames_arr

    skills_difference[:, 0] *= -1
    minigames_difference[:, 0] *= -1

    gains = skills_difference.tolist() + minigames_difference.tolist()
    scoretable = await make_scoretable(gains, username, account_type, gains=True, saved_ts=saved_ts)

    # Overwrite saved user data if argument -noupdate was used
    if update is True:
        saved_data["past_stats"] = new_stats
        saved_data["saved"] = int(datetime.datetime.utcnow().replace(microsecond=0, second=0).timestamp())

        with open("Data files/statsdb.json", "w") as output_file:
            json.dump(data, output_file, indent=4)

    await client.send_message(message.channel, scoretable)


async def track_username(message: discord.Message, keywords: list, client: discord.Client) -> None:
    """
    A command function for command !track to add an username and its current info into tracked players. Progress for
    this user can be then calculated just by using command !gains <username>.

    :param message: Message that invoked this command
    :param keywords: Message content as a list
    :param client: Bot client which is responsible of all work between this code and Discord client
    :return:
    """

    user_data = {"past_stats": [], "account_type": None, "saved": None}
    username = " ".join(keywords).replace("_", " ")

    with open("Data files/statsdb.json", "r") as data_file:
        tracked_players_data = json.load(data_file)

    if username in tracked_players_data.keys():
        await client.send_message(message.channel, "This user is already tracked.")
        return

    account_types = ["Normal", "Ironman", "Ultimate Ironman", "Hardcore Ironman", "Deadman", "Peruuta"]
    reactions = []
    type_options = []

    for i, type_ in enumerate(account_types):
        if i == len(account_types) - 1:
            reaction = "\N{CROSS MARK}"
        else:
            reaction = f"{i + 1}\u20e3"

        reactions.append(reaction)
        type_options.append(f"{reaction} {type_}")

    acc_type_embed = discord.Embed(title=f"What is the account type of {username}?",
                                   description="\n".join(type_options))
    acc_type_embed.set_footer(text=f"Your answer will be registered only after all  {len(reactions)} reactions "
                                   f"have been loaded!")
    acc_type_query = await client.send_message(message.channel, embed=acc_type_embed)

    for reaction in reactions:
        await client.add_reaction(acc_type_query, reaction)

    acc_type_answer = await client.wait_for_reaction(emoji=reactions, user=message.author, timeout=8,
                                                     message=acc_type_query)
    # Embed that is used to edit previous embed when command finishes, exceptions or not
    finish_embed = discord.Embed()
    if not acc_type_answer:
        finish_embed.title = "No answer. Command canceled."
        await client.edit_message(acc_type_query, embed=finish_embed)
        return

    answer_reaction_idx = reactions.index(acc_type_answer.reaction.emoji)
    if answer_reaction_idx == len(reactions) - 1:
        finish_embed.title = "Command canceled."
        await client.edit_message(acc_type_query, embed=finish_embed)
        return
    account_type_formal = account_types[answer_reaction_idx]

    if account_type_formal == "Ultimate Ironman":
        account_type = "uim"
    elif account_type_formal == "Hardcore Ironman":
        account_type = "hcim"
    elif account_type_formal == "Deadman":
        account_type = "dmm"
    else:
        account_type = account_type_formal.lower()

    try:
        getting_stats_embed = discord.Embed(title=f"Gathering stats of {username}...")
        await client.edit_message(acc_type_query, embed=getting_stats_embed)
        initial_stats = await get_hiscore_data(username, client.aiohttp_session, account_type)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Osrs API answered too slowly and user could not be tracked. "
                                                   "Try again later.")
        return
    except TypeError:
        finish_embed.title = f"Could not fins hiscores for user {username} with account type {account_type_formal}."
        await client.edit_message(acc_type_query, embed=finish_embed)
        return
    except ValueError as e:
        if e.args[0].startswith("Username"):
            finish_embed.title = "Usernames can't be longer than 12 characters."
        else:
            finish_embed.title = "ValueError: Unknown account type."
        await client.edit_message(acc_type_query, embed=finish_embed)
        return

    user_data["past_stats"] = initial_stats
    user_data["account_type"] = account_type
    user_data["saved"] = int(datetime.datetime.utcnow().replace(microsecond=0, second=0).timestamp())
    tracked_players_data[username] = user_data

    with open("Data files/statsdb.json", "w") as data_file:
        json.dump(tracked_players_data, data_file, indent=4)

    finish_embed.title = f"Started tracking user {username}. Account type: {account_type_formal}"
    await client.edit_message(acc_type_query, embed=finish_embed)


if __name__ == "__main__":
    print("Dont run this module as a independent process as it doesn't do anything. Run Main.py instead.")
    exit()
