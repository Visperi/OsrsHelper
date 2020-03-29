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

import requests
import json
import discord
import os
import math
import datetime
import Settings
from fractions import Fraction
from bs4 import BeautifulSoup
from mathparse import mathparse

path = "{}/".format(os.path.dirname(__file__))
if path == "/":
    path = ""


def to_utf8(string):
    string = string.replace("Ã¤", "ä").replace("Ã¶", "ö").replace("/ae", "ä").replace("/oe", "ö").replace("Ã„", "Ä")\
        .replace("Ã–", "Ö")
    return string


def to_ascii(string):
    string = string.replace("ä", "/ae").replace("ö", "/oe").replace("Ä", "/AE").replace("Ö", "/OE")
    return string


def decode_cml(link):
    response = requests.get(link)
    response.encoding = "utf-8-sig"
    return response.text


async def function_help(message, keywords, client):
    command = " ".join(keywords).replace("!", "").replace("%", "").replace("&", "")
    if not command:
        msg = "`!info`: Basic info about the bot and latest updates\n" \
              "`!commands`: Get a list of all available commands\n" \
              "`!server commands`: Get a list of all custom commands for this server\n" \
              "`!help <command name>`: Get instructions for one command"
        await client.send_message(message.channel, msg)
        return
    with open(f"{path}Help_en.json", encoding="utf-8") as data_file:
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
    roles = []

    async def get_paivamaara(tiedot):
        kellonaika1 = tiedot[1].split(".")
        paivamaara1 = tiedot[0].split("-")
        paivamaara = f"{paivamaara1[2]}.{paivamaara1[1]}.{paivamaara1[0]}"
        kellonaika = kellonaika1[0]
        return paivamaara, kellonaika

    try:
        avatar = message.author.avatar_url
        created_at = " ".join(await get_paivamaara(str(message.author.created_at).split()))
        joined_at = " ".join(await get_paivamaara(str(message.author.joined_at).split()))
        display_name = message.author.display_name
        for role in message.author.roles:
            if str(role) == "@everyone":
                role = "\\@everyone"
            roles.append(str(role))
    except AttributeError:
        await client.send_message(message.channel, "This command doesn't work in direct messages.")
        return

    user_info = discord.Embed().set_author(name=display_name).set_thumbnail(url=avatar)\
        .add_field(name="Username", value=str(message.author))\
        .add_field(name="Id", value=message.author.id)\
        .add_field(name="User created", value=created_at)\
        .add_field(name="Joined server", value=joined_at)\
        .add_field(name="Roles in this server", value=", ".join(roles))
    await client.send_message(message.channel, embed=user_info)


async def commands(message, client):
    discord_commands = ["!info", "!help", "!calc", "!me", "!namechange", "!server commands", "!satokausi", "!beer",
                        "!beerscores"]
    osrs_commands = ["!wiki", "!stats", "!gains", "!track", "!xp", "!ehp", "!nicks", "!loot", "!update"]
    clue_commands = ["!cipher", "!anagram", "!puzzle", "!cryptic", "!maps"]
    item_commands = ["!keys", "!limit", "!price"]
    moderator_commands = ["%addkey", "%delkey", "%addcom", "%delcom", "%editcom"]
    settings_commands = ["&language", "&settings", "&permit", "&unpermit", "&add commands", "&forcelang",
                         "&defaultlang"]
    viesti = discord.Embed().add_field(name="Osrs commands", value="\n".join(osrs_commands)) \
        .add_field(name="Item commands", value="\n".join(item_commands))\
        .add_field(name="Discord commands", value="\n".join(discord_commands))\
        .add_field(name="Clue commands", value="\n".join(clue_commands))\
        .add_field(name="High permission commands", value="\n".join(moderator_commands))\
        .add_field(name="Settings commands", value="\n".join(settings_commands))\
        .set_footer(text="In case you need help in using commands, try !help <command>")
    await client.send_message(message.channel, embed=viesti)
    kayttokerrat("cipher")


def get_iteminfo(itemname, default_names=False):
    """Searches for item name and id from local files.

    :param itemname: The name of the item in string format
    :param default_names: If set true, only default item names are accepted as itemname input
    :return: Original item name (str) and its id (int), None if not found
    """
    itemname = itemname.capitalize()
    with open(f"{path}Tradeables.json") as data_file:
        data = json.load(data_file)
    if itemname in list(data.keys()):
        item_id = data[itemname]["id"]
        return itemname, item_id
    elif default_names:
        return
    else:
        itemname = to_ascii(itemname.lower())
        with open(f"{path}Item_keywords.json") as data_file:
            keywords = json.load(data_file)
        if itemname in keywords["all nicks"]:
            for item in keywords:
                if itemname in keywords[item] and item != "all nicks":
                    itemname = to_utf8(item.capitalize())
                    item_id = data[itemname]["id"]
                    return itemname, item_id


async def get_halch(itemname):
    """Searches high alchemy value for given item from local files or osrs wiki.

    :param itemname: Name of the item to search. Must be in string format
    :return: High alch value in int() default format
    """

    itemname = itemname.capitalize()
    with open(f"{path}Tradeables.json") as data_file:
        data = json.load(data_file)
    try:
        halch = data[itemname]["high_alch"]
    except KeyError:
        print("Annettua itemiä ei löydy listasta.")
        return
    if halch == "":
        link = "http://2007.runescape.wikia.com/wiki/{}".format(itemname.replace(" ", "_"))
        page = requests.get(link).text
        start = page.find("High Alch</a>\n</th><td> ") + len("High Alch</a>\n</th><td> ")
        end = page.find("&#160;coins", start)
        halch = page[start:end]
        try:
            halch = int(halch.replace(",", ""))
        except ValueError:
            halch = "-"
        data[itemname]["high_alch"] = halch
        with open(f"{path}Tradeables.json", "w") as data_file:
            json.dump(data, data_file, indent=4)
    return halch


async def search_wiki(message, hakusanat: list, client, get_html=False):
    baselink = "https://oldschool.runescape.wiki/w/"

    search = "_".join(hakusanat)
    search_link = baselink + search
    response = requests.get(search_link).text
    if f"This page doesn&#039;t exist on the wiki. Maybe it should?" in response:
        hyperlinks = []
        truesearch_link = f"https://oldschool.runescape.wiki/w/Special:Search?search={search}"
        truesearch_resp = requests.get(truesearch_link).text

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

    with open(f"{path}Ciphers.json") as cipher_file:
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


async def hae_highscoret(message, hakusanat, client, acc_type=None, gains=False, initial_stats=False):
    from tabulate import tabulate

    table = []
    stats = []
    skillnames = [["Total"], ["Attack"], ["Defence"], ["Strength"], ["Hitpoints"], ["Ranged"], ["Prayer"], ["Magic"],
                  ["Cooking"], ["Woodcutting"], ["Fletching"], ["Fishing"], ["Firemaking"], ["Crafting"], ["Smithing"],
                  ["Mining"], ["Herblore"], ["Agility"], ["Thieving"], ["Slayer"], ["Farming"], ["Runecrafting"],
                  ["Hunter"],
                  ["Construction"]]
    nick = " ".join(hakusanat).lower()
    account_type = "normal"
    header = "hiscore_oldschool"
    if message.content.startswith("!ironstats") or acc_type == "ironman":
        header = "hiscore_oldschool_ironman"
        account_type = "ironman"
    elif message.content.startswith("!uimstats") or acc_type == "uim":
        header = "hiscore_oldschool_ultimate"
        account_type = "uim"
    elif message.content.startswith("!dmmstats") or acc_type == "dmm":
        header = "hiscore_oldschool_deadman"
        account_type = "dmm"
    elif message.content.startswith("!seasonstats") or acc_type == "seasonal":
        header = "hiscore_oldschool_seasonal"
        account_type = "seasonal"
    elif message.content.startswith("!hcstats") or acc_type == "hcim":
        header = "hiscore_oldschool_hardcore_ironman"
        account_type = "hcim"
    elif message.content.startswith("!tournamentstats") or acc_type == "tournament":
        header = "hiscore_oldschool_tournament"
    link = requests.get(f"http://services.runescape.com/m={header}/index_lite.ws?player={nick}")
    tiedot = list(link.text.split("\n"))
    count = 0

    def hae_cluet(stats_list):
        # Osrs  apin vastaus loppuu väliin
        master = stats_list[33]
        elite = stats_list[32]
        hard = stats_list[31]
        medium = stats_list[30]
        easy = stats_list[29]
        beginner = stats_list[28]
        total = stats_list[27]

        clues = [beginner, easy, medium, hard, elite, master, total]
        clue_names = [["Beginner"], ["Easy"], ["Medium"], ["Hard"], ["Elite"], ["Master"], ["All"]]

        for index, clue in enumerate(clues):
            if clue == "-1,-1":
                clue = "0,0"
            clue = clue.split(",")
            for part in clue:
                clue_names[index].append(part)
        return clue_names

    for lista in tiedot:
        table.append(lista.split(", "))
    for lists in table:
        for arvo in lists:
            stats.append(arvo.split(","))
    for skill in stats[0:24]:
        for info in skill:
            try:
                if info == "-1":
                    info = "0"
                skillnames[count].append("{:,}".format(int(info)))
            except ValueError:
                await client.send_message(message.channel, "User not found.")
                return
        count += 1
    if not gains and not initial_stats:
        cluet = hae_cluet(tiedot)
        await client.send_message(message.channel, "```{}\n\n{}\n\n{}```"
                                  .format("{:^50}".format("STATS FOR {}".format(nick.upper())),
                                          tabulate(skillnames, headers=["Skill", "Rank", "Level", "Xp"],
                                                   tablefmt="orgtbl"),
                                          tabulate(cluet, headers=["Clue", "Rank", "Amount"], tablefmt="orgtbl")))
        kayttokerrat("Stats")
    if gains or initial_stats:
        update_stats(nick, skillnames, account_type)
        return skillnames


def check_if_tracked(nimi):
    with open(f"{path}Tracked_players.json") as data_file:
        data = json.load(data_file)
    try:
        # noinspection PyUnusedLocal
        name = data[nimi]
        return True
    except KeyError:
        link = f"http://crystalmathlabs.com/tracker/api.php?type=previousname&player={nimi}"
        previous_name = decode_cml(link).replace("_", " ")
        if previous_name != "-1":
            if previous_name in list(data):
                previous_names = data[previous_name]["previous_names"]
                if previous_name not in previous_names:
                    previous_names.append(previous_name)
                data[nimi] = data.pop(previous_name)
                with open(f"{path}Tracked_players.json", "w") as data_file:
                    json.dump(data, data_file, indent=4)
                with open(f"{path}statsdb.json") as data_file:
                    stats_data = json.load(data_file)
                stats_data[nimi] = stats_data.pop(previous_name)
                with open(f"{path}statsdb.json", "w") as data_file:
                    json.dump(stats_data, data_file, indent=4)
                return True
            else:
                return False
        else:
            return


def update_stats(nick, stats, account_type):
    current_date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

    with open(f"{path}statsdb.json") as data_file:
        data = json.load(data_file)
    try:
        account_type_old = data[nick]["account_type"]
    except KeyError:
        account_type_old = ""
    if (account_type_old == "ironman" or account_type_old == "uim" or account_type_old == "hcim") and \
                    account_type == "normal":
        return
    data[nick] = dict(past_stats=stats, account_type=account_type, saved=current_date)

    with open(f"{path}statsdb.json", "w") as data_file:
        json.dump(data, data_file, indent=4)


async def gains_calculator(message, hakusanat, client):
    from tabulate import tabulate
    username = " ".join(hakusanat).lower().replace("_", " ")
    if username == "":
        await client.send_message(message.channel, "Please give also the user whose gains you want to inspect. If you "
                                                   "need help, use command `!help gains`")
        return

    tracked = check_if_tracked(username)
    if tracked:
        with open(f"{path}statsdb.json") as data_file:
            data = json.load(data_file)
        try:
            stats_past = data[username]["past_stats"]
        except KeyError:
            await client.send_message(message.channel, "KeyError: User is being tracked, but old data could not be "
                                                       "found. Please report this to bot owner. You can find him by "
                                                       "using `!info`.")
            return
        stats_recent = await hae_highscoret(message, hakusanat, client, data[username]["account_type"], gains=True)
        if not stats_recent:
            return
        gains_list = [["Total"], ["Attack"], ["Defence"], ["Strength"], ["Hitpoints"], ["Ranged"], ["Prayer"],
                      ["Magic"], ["Cooking"], ["Woodcutting"], ["Fletching"], ["Fishing"], ["Firemaking"],
                      ["Crafting"], ["Smithing"], ["Mining"], ["Herblore"], ["Agility"], ["Thieving"], ["Slayer"],
                      ["Farming"], ["Runecrafting"], ["Hunter"], ["Construction"]]
        last_savedate = data[username]["saved"]
        current_date = datetime.datetime.now()

        def calculate_gains(recent, old):
            recent = recent.split(",")
            recent = "".join(recent)
            past_tmp = old.split(",")
            past_tmp = "".join(past_tmp)
            gains = int(recent) - int(past_tmp)
            if 0 < gains:
                gains = "+{:,}".format(gains)
            return gains

        # noinspection PyTypeChecker
        for stat in stats_recent:
            current = stat[1]
            past = stats_past[stats_recent.index(stat)][stat.index(current)]
            calc = calculate_gains("-" + current, "-" + past)
            gains_list[stats_recent.index(stat)].append(calc)
            for current in stat[2:]:
                past = stats_past[stats_recent.index(stat)][stat.index(current)]
                calc = calculate_gains(current, past)
                gains_list[stats_recent.index(stat)].append(calc)
        await client.send_message(message.channel,
                                  "```Gains between {} - {} UTC\n\n{}```"
                                  .format(last_savedate, current_date,
                                          tabulate(gains_list, headers=["Skill", "Rank", "Level", "Xp"],
                                                   tablefmt="orgtbl")))
        kayttokerrat("Gains")
    elif tracked is False:
        await client.send_message(message.channel, "This username is not being tracked. Use command "
                                                   "`!track <username>` first. If you're sure its tracked, "
                                                   "try `!namechange`.")
    else:
        await client.send_message(message.channel, "This username is not being tracked and old names could not be "
                                                   "found from CML's database. If you have changed the nickname, use "
                                                   "`!namechange`. Otherwise use `!track <username>`.")


async def time_to_max(message, hakusanat, client):
    await client.send_message(message.channel, "This command has been disabled because either CML API is not in public "
                                               "use anymore or it works very badly.")
    return
    # nick = " ".join(hakusanat).replace("_", " ")
    # link = f"http://crystalmathlabs.com/tracker/api.php?type=ttm&player={nick}"
    # response = decode_cml(link)
    # tunnit = str(math.ceil(float(response))) + " EHP"
    # if tunnit == "-1 EHP":
    #     await client.send_message(message.channel, "This username is not in use or it isn't tracked in CML.")
    #     return
    # elif tunnit == "0 EHP":
    #     tunnit = "0 EHP (maxed)"
    # elif tunnit == "-2 EHP":
    #     return
    # elif tunnit == "-4 EHP":
    #     await client.send_message(message.channel, "CML api is temporarily out of service due to heavy traffic on "
    #                                                "their sites.")
    #     return
    #
    # await client.send_message(message.channel, f"Ttm for {nick}: {tunnit}")
    # kayttokerrat("Ttm")


async def search_anagram(message, hakusanat, client):
    partial_matches = []
    search = " ".join(hakusanat)
    with open(f"{path}Anagrams.json") as anagram_file:
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

    with open(f"{path}Experiences.txt", "r") as file:
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
    file = f"{path}{filename}"

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

    with open(f"{path}Custom_commands.json") as data_file:
        data = json.load(data_file)
    try:
        viesti = data[server]["!{}".format(to_ascii(command))]["message"]
    except KeyError:
        return
    await client.send_message(message.channel, to_utf8(viesti))
    kayttokerrat("custom")


async def addcom(message, words_raw, client):
    words = " ".join(words_raw)
    file = f"{path}Custom_commands.json"
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
    with open(f"{path}Custom_commands.json") as data_file:
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

    with open(f"{path}cryptic_clues.json") as data_file:
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
    file = f"{path}Custom_commands.json"
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
    with open(f"{path}Buy_limits.json") as data_file:
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
    with open(f"{path}Times_used.json") as data_file:
        data = json.load(data_file)
    times = data[command]
    data[command] = times + 1
    if data["date_start"] == "":
        data["date_start"] = current_date
    data["date_now"] = current_date
    with open(f"{path}Times_used.json", "w") as data_file:
        json.dump(data, data_file, indent=4)


async def hinnanmuutos(message, client):
    """
    DEPRECATED
    """

    await client.send_message(message.channel, "This command is deprecated and has been combined with command "
                                               "`!price`.")
    return


async def track_user(message, hakusanat, client):
    name = " ".join(hakusanat).replace("_", " ")
    link = "http://services.runescape.com/m=hiscore_oldschool/index_lite.ws?player={}".format(name)
    request = requests.get(link).text

    async def get_user_type(username):
        account_type = None
        reactions = ["1\u20e3", "2\u20e3", "3\u20e3", "4\u20e3", "5\u20e3", "6\u20e3", "\N{CROSS MARK}"]
        choices = ["1\u20e3 Normal", "2\u20e3 Ironman", "3\u20e3 Uim", "4\u20e3 Hcim", "5\u20e3 Dmm",
                   "6\u20e3 Seasonal", "\N{CROSS MARK} Cancel"]
        bot_embed = discord.Embed(title=f"What is the type of character {username}?",
                                   description="\n".join(choices)).set_footer(text="your reaction is registered only "
                                                                                   "after all options are loaded.")
        bot_message = await client.send_message(message.channel, embed=bot_embed)
        for reaction in reactions:
            await client.add_reaction(bot_message, reaction)
        answer = await client.wait_for_reaction(emoji=reactions, message=bot_message, user=message.author, timeout=7)
        if not answer:
            await client.edit_message(bot_message, embed=discord.Embed(title="No answer, operation cancelled."))
            return
        elif answer.reaction.emoji == reactions[-1]:
            await client.edit_message(bot_message, embed=discord.Embed(title="Operation cancelled."))
            return
        elif answer.reaction.emoji == reactions[0]:
            account_type = "normal"
        elif answer.reaction.emoji == reactions[1]:
            account_type = "ironman"
        elif answer.reaction.emoji == reactions[2]:
            account_type = "uim"
        elif answer.reaction.emoji == reactions[3]:
            account_type = "hcim"
        elif answer.reaction.emoji == reactions[4]:
            account_type = "dmm"
        elif answer.reaction.emoji == reactions[5]:
            account_type = "seasonal"
        await client.edit_message(bot_message, embed=discord.Embed(title="Started tracking {}. Character type: {}"
                                                                   .format(username, account_type.capitalize())))
        return account_type

    with open(f"{path}Tracked_players.json") as data_file:
        data = json.load(data_file)
    if "404 - Page not found" in request:
        await client.send_message(message.channel, "User not found.")
        return
    if name in list(data):
        await client.send_message(message.channel, "This user is already being tracked.")
        return
    try:
        acc_type = await get_user_type(name)
    except discord.errors.Forbidden:
        await client.send_message(message.channel, "For this command bot needs permission to add reactions.")
        return
    if not acc_type:
        return
    data[name] = {"previous_names": []}
    with open(f"{path}Tracked_players.json", "w") as data_file:
        json.dump(data, data_file, indent=4)
    await hae_highscoret(message, name.split(), client, acc_type=acc_type, initial_stats=True)


async def change_name(message, hakusanat, client):
    tiedosto = f"{path}Tracked_players.json"
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
        check_name = requests.get("http://services.runescape.com/m=hiscore_oldschool/index_lite.ws?player={}"
                                  .format(new_name)).text
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
            with open(f"{path}statsdb.json") as data_file:
                stats_data = json.load(data_file)
            stats_data[new_name] = stats_data.pop(old_name)
            with open(f"{path}statsdb.json", "w") as data_file:
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
    with open(f"{path}Tradeables.json") as tradeables:
        all_tradeables = json.load(tradeables)
    with open(f"{path}Item_keywords.json") as data_file:
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
        with open(f"{path}Item_keywords.json", "w") as data_file:
            json.dump(data, data_file, indent=4)
            await client.send_message(message.channel, "Added following items for {}: `{}`. {}"
                                      .format(itemname, ", ".join(approved_keys), denied_msg))
    kayttokerrat("Addkey")


async def delkey(message, keywords, client):
    file = f"{path}Item_keywords.json"
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
    with open(f"{path}Tradeables.json") as data_file:
        data = json.load(data_file)
    try:
        item_id = data[itemname]["id"]
        return itemname, item_id
    except KeyError:
        if not vanilla_names:
            with open(f"{path}Item_keywords.json") as nicks_file:
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
    with open(f"{path}Item_keywords.json") as data_file:
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

    link = "http://oldschool.runescape.com/"
    osrs_response = requests.get(link).text

    osrs_response_html = BeautifulSoup(osrs_response, "html.parser")

    for div_tag in osrs_response_html.findAll("div", attrs={"class": "news-article__details"}):
        p_tag = div_tag.p
        # Somehow the article types always end in space
        article_type = div_tag.span.contents[0][:-1]
        article_link = p_tag.a["href"]
        article_number = p_tag.a["id"][-1]
        news_articles[article_number] = {"link": article_link, "type": article_type}

    # Find the latest article by finding the smallest article key
    latest_article_key = min(news_articles.keys())

    article_link = news_articles[latest_article_key]["link"]
    article_type = news_articles[latest_article_key]["type"]

    await client.send_message(message.channel, f"Latest news about Osrs ({article_type}):\n\n"
                                               f"{article_link}")


async def editcom(message, words_raw, client):
    words = " ".join(words_raw)
    file = f"{path}Custom_commands.json"
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
    footnote = ""
    link = f"http://crystalmathlabs.com/tracker/api.php?type=previousname&player={search}"
    previous_name = decode_cml(link).replace("_", " ")
    with open(f"{path}Tracked_players.json") as data_file:
        data = json.load(data_file)
    try:
        old_nicks = data[search]["previous_names"]
    except KeyError:
        footnote = "To save all user's old nicknames it must be tracked."
        if previous_name == "-4":
            await client.send_message(message.channel, "CML api is currently out of use and the user is not being "
                                                       "tracked, so no old nicknames was found.")
            return
        elif previous_name == "-1":
            await client.send_message(message.channel, "Nickname is not in use or it has never been updated in CML.")
            return
        else:
            msg = discord.Embed(title="Old nick for {}".format(search), description=previous_name)\
                .set_footer(text=footnote)
            await client.send_message(message.channel, embed=msg)
        return
    if previous_name != "-1" and previous_name != "-4" and previous_name not in old_nicks:
        old_nicks.append(previous_name)
        data[search]["previous_names"] = old_nicks
        with open(f"{path}Tracked_players.json", "w") as data_file:
            json.dump(data, data_file, indent=4)
    elif previous_name == "-4":
        footnote = "CML api is currently out of use and therefore there may be an old name missing."
    if len(old_nicks) == 0:
        await client.send_message(message.channel, "Could not find any old nicknames for this user.\n\n{}"
                                  .format(footnote))
        return
    msg = discord.Embed(title=f"Stored old nicks for {search}", description="\n".join(old_nicks))\
        .set_footer(text=footnote)
    await client.send_message(message.channel, embed=msg)


async def get_times_used(message, client):
    commands_list = []
    with open(f"{path}Times_used.json") as data_file:
        data = json.load(data_file)
    dates = "{} - {}".format(data["date_start"], data["date_now"])
    for item in data:
        if item == "date_start" or item == "date_now":
            continue
        commands_list.append(f"{item}: {data[item]}")
    await client.send_message(message.channel, "```{}\n\n{}```".format(dates, "\n".join(commands_list)))


async def bot_info(message, client, release_notes=False):
    with open(f"{path}changelog_en.txt", "r", encoding="utf-8") as file:
        changelog = file.read()
    if release_notes:
        embed = discord.Embed(title="Latest updates", description=changelog)
    else:
        appinfo = await client.application_info()
        bot_name = appinfo.name
        bot_owner = appinfo.owner
        last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(f"{path}Main.py")).strftime("%d/%m/%Y")
        embed = discord.Embed(title=bot_name, description=f"Administrator: {bot_owner.mention}\n"
                                                          f"Updated: {last_modified}\nSource code: Python 3.6 "
                                                          f"([Source](https://github.com/Visperi/OsrsHelper))")
        embed.add_field(name="Credits",
                        value="[discord.py](https://github.com/Rapptz/discord.py)\n"
                              "[Rsbuddy](https://rsbuddy.com/) (price, pricechange)\n"
                              "[Crystalmathlabs](http://www.crystalmathlabs.com/tracker/) (ttm, nicks, ehp)\n"
                              "[Old school runescape](http://oldschool.runescape.com/) (whole game, user stats, "
                              "item info)\n"
                              "[OSRS Wiki](https://oldschool.runescape.wiki) (wiki, clues)")
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

    with open(f"{path}streamers.json") as data_file:
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
    with open(f"{path}droprates.json") as data_file:
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

    with open(f"{path}droprates.json", "w") as data_file:
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

    with open("droprates.json") as rates_file:
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
    with open(f"{path}droprates.json") as data_file:
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
        with open(f"{path}droprates.json", "w") as data_file:
            json.dump(data, data_file, indent=4)
        await client.send_message(message.channel, f"Removed droprate {itemname} from {target}.")
    elif len(keywords) == 1:
        try:
            if keywords[0].capitalize() in data["Misc"]:
                del data["Misc"][keywords[0].capitalize()]
                with open(f"{path}droprates.json", "w") as data_file:
                    json.dump(data, data_file, indent=4)
                await client.send_message(message.channel, f"Removed droprate {keywords[0].capitalize()}.")
                return
        except KeyError:
            await client.send_message(message.channel, "This item doesn't have droprate or you forgot to give a "
                                                       "target which drops it.")
            return
        await client.send_message(message.channel, "Removing a whole categories is not in use yet. You can delete "
                                                   "droprates one at a time if you give the target name first.")


async def test_connection(message, keywords, client):
    site = keywords[0]
    if site == "wiki":
        link = "https://oldschool.runescape.wiki/"
    elif site == "osrs" or site == "runescape":
        link = "http://services.runescape.com/m=hiscore_oldschool/index_lite.ws?player=visperi"
    elif site == "cml" or site == "crystalmathlabs":
        link = "https://crystalmathlabs.com/tracker/api.php?type=ttm&player=visperi"
    else:
        sites = "\n".join(["rsbuddy", "wiki", "osrs", "cml"])
        await client.send_message(message.channel, f"Unknown site. All current choices are:\n\n{sites}")
        return

    try:
        request = requests.get(link, timeout=5)
    except requests.exceptions.ReadTimeout:
        await client.send_message(message.channel, "Site answer was too slow.")
        return
    status = str(request.status_code)
    if status[0] == "2":
        info_string = "Site takes requests, understands them and answers normally."
    elif status[0] == "4":
        info_string = "The request given by bot is faulty."
    elif status[0] == "5":
        info_string = "Site has problems at answering requests."
    else:
        info_string = "Unkwonw response. Before its added to bot, you can check the code by yourself e.g. from " \
                      "[Wikipediasta](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes)."
    embed = discord.Embed(title=f"Status code: {status}", description=f"{info_string}\n"
                                                                      f"Connection was tested with [this]({link}) "
                                                                      f"link.")
    await client.send_message(message.channel, embed=embed)


async def itemspecs(message, hakusanat, client):
    """
    Hakee käyttäjän antamasta itemistä tietoja. Yrittää aseille ja panssareille ensimmäisenä hakea statseja
    tiedostosta, jonka epäonnistuessa ne haetaan wikistä. Lopuksi asettelee kaiken tiedon embediin ja
    lähettää sen discordiin.
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

    with open(f"{path}itemstats.json") as data_file:
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
            geapi_resp = requests.get(f"http://services.runescape.com/m=itemdb_oldschool/api/catalogue/detail.json?"
                                      f"item={item_id}").text
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
            with open("itemstats.json", "w") as data_file:
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


async def item_price(message, hakusanat, client):

    def pricechanges():
        latest = daily_data[latest_ts]
        month = "{:,}".format(int(latest) - int(daily_data[month_ts])).replace(",", " ")
        week = "{:,}".format(int(latest) - int(daily_data[week_ts])).replace(",", " ")
        day = "{:,}".format(int(latest) - int(daily_data[day_ts])).replace(",", " ")
        if month[0] != "-":
            month = f"+{month}"
        if week[0] != "-":
            week = f"+{week}"
        if day[0] != "-":
            day = f"+{day}"
        return month, week, day

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
        resp = requests.get(api_link, timeout=4).text
    except requests.exceptions.ReadTimeout:
        await client.send_message(message.channel, "Old School Runescape api answers too slowly. Try again later.")
        return

    data = json.loads(resp)
    daily_data = data["daily"]
    timestamps = list(daily_data.keys())
    latest_ts = timestamps[-1]
    day_ts = timestamps[-2]
    week_ts = timestamps[-7]
    month_ts = timestamps[-31]

    price_latest = f"{int(daily_data[latest_ts]):,}".replace(",", " ")
    latest_total = f"{int(daily_data[latest_ts]) * multiplier:,}".replace(",", " ")

    pc_month, pc_week, pc_day = pricechanges()
    if multiplier != 1:
        pcs = f"({multiplier} pcs)"
        price_ea = f" ({price_latest} ea)"
    else:
        pcs = ""
        price_ea = ""

    embed = discord.Embed(title=f"{itemname} {pcs}")\
        .add_field(name="Latest price", value=f"{latest_total} gp{price_ea}", inline=False)\
        .add_field(name="Price changes", value=f"In a month: {pc_month} gp\n"
                                                 f"In a week: {pc_week} gp\nIn a day: {pc_day} gp", inline=False)\
        .set_footer(text=f"Latest price from {datetime.datetime.utcfromtimestamp(int(latest_ts) / 1e3)} UTC")
    await client.send_message(message.channel, embed=embed)


async def add_drinks(message, client):
    user_id = message.author.id
    try:
        server_id = message.server.id
    except AttributeError:
        await client.send_message(message.channel, "This command doesn't support direct messages.")
        return

    with open("drinks.json", "r") as data_file:
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

    with open("drinks.json", "w") as output_file:
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

async def drink_highscores(message, client):
    try:
        server_id = message.server.id
    except AttributeError:
        await client.send_message(message.channel, "This command doesn't support direct messages.")
        return

    with open("drinks.json", "r") as data_file:
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

async def remove_drinks(message, client):
    user_id = message.author.id
    try:
        server_id = message.server.id
    except AttributeError:
        await client.send_message(message.channel, "This command doesn't support direct messages.")
        return

    with open("drinks.json", "r") as data_file:
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

    with open("drinks.json", "w") as output_file:
        json.dump(drink_data, output_file, indent=4)

    await client.add_reaction(message, "a:emiTreeB:693788789042184243")

if __name__ == "__main__":
    print("Tätä moduulia ei ole tarkoitettu ajettavaksi itsessään. Suorita Kehittajaversio.py tai Main.py")
    print("Suljetaan...")
    exit()
