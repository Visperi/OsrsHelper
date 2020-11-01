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
import static_functions
import random
from caching import Cache


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
                                          "!satokausi", "!beer", "!beerscores", "!korona", "!reminder", "!roll",
                                          "!mwiki"],
                     "Osrs commands": ["!wiki", "!stats", "!gains", "!track", "!xp", "!ehp", "!nicks", "!kill",
                                       "!update", "!kc"],
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
        viesti = data[server]["!{}".format(static_functions.to_ascii(command))]["message"]
    except KeyError:
        return
    await client.send_message(message.channel, static_functions.to_utf8(viesti))
    kayttokerrat("custom")


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
        custom_commands.append(static_functions.to_utf8(command))
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
    komento = static_functions.to_ascii(komento)
    with open(file) as data_file:
        data = json.load(data_file)
    if komento in list(data[server]):
        del data[server][komento]
        with open(file, "w") as data_file:
            json.dump(data, data_file, indent=4)
            await client.send_message(message.channel, "Command `{}` deleted."
                                      .format(static_functions.to_utf8(komento)))
            kayttokerrat("delcom")
    else:
        await client.send_message(message.channel, "That command doesn't exist")


async def get_buylimit(message, keywords, client):
    """
    Gives a four hour Grand Exchange limit for an item if there is any
    """
    keyword = " ".join(keywords)
    item_data = await static_functions.get_item_data(keyword)
    if not item_data:
        await client.send_message(message.channel, "Haullasi ei löytynyt yhtään itemiä.")
        return
    else:
        default_itemname = item_data["name"]
    with open("Data files/Buy_limits.json") as data_file:
        data = json.load(data_file)
    try:
        buy_limit = data[default_itemname]
    except KeyError:
        await client.send_message(message.channel, "Itemille ei löytynyt ostorajaa. Ilmoitathan, jos huomaat virheen, "
                                                   "niin korjataan tilanne.")
        return
    await client.send_message(message.channel, f"Four hours buy limit for {default_itemname}: {buy_limit} pcs.")


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
            _tmp = new_name.replace(" ", "_")
            url = f"http://services.runescape.com/m=hiscore_oldschool/index_lite.ws?player={_tmp}"
            check_name = await static_functions.make_request(client, url)
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


async def find_itemname(message, hakusanat, client, vanilla_names=False):
    print(hakusanat)
    itemname = static_functions.to_ascii(" ".join(hakusanat)).capitalize()
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


async def latest_updates(message, client):
    news_articles = {}
    articles = []

    link = "http://oldschool.runescape.com/"
    try:
        osrs_response = await static_functions.make_request(client.aiohttp_session, link)
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


async def get_old_nicks(message, hakusanat, client):
    search = " ".join(hakusanat)
    with open("Data files/Tracked_players.json") as data_file:
        data = json.load(data_file)
    try:
        old_nicks = data[search]["previous_names"]
    except KeyError:
        await client.send_message(message.channel, "This user is not tracked. Use command `!track` first.")
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
                        value="[discord.py](https://github.com/Rapptz/discord.py) (Discord library used in bot)\n"
                              "[Crystalmathlabs](http://www.crystalmathlabs.com/tracker/) (EHP rates)\n"
                              "[Old school runescape](http://oldschool.runescape.com/) (Highscores, game news)\n"
                              "[RSBuddy](https://rsbuddy.com/) (G.E. prices)\n"
                              "[Melvoridle wiki](https://wiki.melvoridle.com/) (Melvoridle wiki)\n"
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
    item_data = await static_functions.get_item_data(search[0])
    if not item_data:
        await client.send_message(message.channel, "Could not find any items with your search.")
        return

    item_id = item_data["id"]
    default_itemname = item_data["name"]
    high_alch_value = int(0.6 * item_data["store_price"])
    # api_link = f"http://services.runescape.com/m=itemdb_oldschool/api/graph/{item_id}.json"
    api_link = f"https://rsbuddy.com/exchange/graphs/1440/{item_id}.json"

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
        await client.send_message(message.channel, "The multiplier had an unknown character. Multiplier supports only "
                                                   "abbreviations `k` and `m`.")
        return
    try:
        resp = await static_functions.make_request(client.aiohttp_session, api_link)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Osrs API answered too slowly. Try again later.")
        return

    price_data = json.loads(resp)
    latest_ts = price_data[-1]["ts"]
    latest_price = price_data[-1]["overallPrice"]
    day_price = price_data[-2]["overallPrice"]
    week_price = price_data[-7]["overallPrice"]
    month_price = price_data[-31]["overallPrice"]

    # Format and calculate the latest piece values and total values
    latest_price_formal = f"{latest_price:,}".replace(",", " ")
    high_alch_value_formal = f"{high_alch_value:,}".replace(",", " ")
    price_total = f"{latest_price * multiplier:,}".replace(",", " ")
    high_alch_total = f"{high_alch_value * multiplier:,}".replace(",", " ")

    # Calculate and format the price changes
    pc_month = "{:+,}".format(latest_price - month_price).replace(",", " ")
    pc_week = "{:+,}".format(latest_price - week_price).replace(",", " ")
    pc_day = "{:+,}".format(latest_price - day_price).replace(",", " ")

    title = default_itemname
    latest_price_str = f"{price_total} gp"
    high_alch_value_str = f"{high_alch_total} gp"
    price_changes_str = f"In a month: {pc_month} gp\nIn a week: {pc_week} gp\nIn a day: {pc_day} gp"

    if multiplier != 1:
        latest_price_str = f"{latest_price_str} ({latest_price_formal} ea)"
        high_alch_value_str = f"{high_alch_value_str} ({high_alch_value_formal} ea)"
        title = f"{title} ({multiplier} pcs)"

    embed = discord.Embed(title=title)
    embed.add_field(name="Latest price", value=latest_price_str, inline=False)
    embed.add_field(name="High alch value", value=high_alch_value_str, inline=False)
    embed.add_field(name="Price changes", value=price_changes_str, inline=False)
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
    title = ""

    for pos, user_id in enumerate(sorted_scores):
        if pos > 9:
            break

        try:
            member = message.server.get_member(user_id)
            display_name = member.display_name
        except AttributeError:
            title = "Due to an update in Discord bot systems, usernames cannot temporarily be fetched " \
                    "<:danskisu:689928015341158469>"
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

    embed = discord.Embed(title="Users with the most alcohol units drinked in this server",
                          description="\n".join(highscores))
    embed.set_footer(text="Counter started in 2020-03-20")

    await client.send_message(message.channel, title, embed=embed)


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
            reminder_time = static_functions.string_to_timedelta(time_string)
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
    elif invoked_with == "!lstats" or invoked_with == "!leaguestats":
        account_type = "seasonal"
    else:
        await client.send_message(message.channel, f"Unknown account type with invokation: {invoked_with}")
        return

    try:
        user_stats = await static_functions.get_hiscore_data(username, client.aiohttp_session, acc_type=account_type)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Osrs API answered too slowly. Try again later.")
        return
    except TypeError:
        await client.send_message(message.channel, "Could not find hiscores for user with given account type.")
        return
    except ValueError as e:
        error_msg = e.args[0]

        if error_msg == "Username can't be longer than 12 characters.":
            await client.send_message(message.channel, "Usernames can't be longer than 12 characters.")
        elif "Unknown account type:" in error_msg:
            await client.send_message(message.channel, f"Unknow account type while requesting hiscore data: "
                                                       f"{account_type}.")
        else:
            await client.send_message(message.channel, "Unknown error while requesting hiscore  data. Please check the "
                                                       "official hiscores are working as normal.")
        return

    scoretable = await static_functions.make_scoretable(user_stats, username, account_type)
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
        # msg = "This user is not tracked. Use command `!track` first."
        msg = "This user is not being tracked. Tracking new accounts is temporarily disabled."
        await client.send_message(message.channel, msg)
        return

    account_type = saved_data["account_type"]
    saved_stats = saved_data["past_stats"]
    saved_ts = datetime.datetime.fromtimestamp(saved_data["saved"])

    try:
        new_stats = await static_functions.get_hiscore_data(username, client.aiohttp_session, acc_type=account_type)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Osrs API answered too slowly. Try again later.")
        return
    except TypeError:
        await client.send_message((message.channel, "There is no existing hiscore data for this username."))
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
    scoretable = await static_functions.make_scoretable(gains, username, account_type, gains=True, saved_ts=saved_ts)

    # Overwrite saved user data if argument -noupdate was NOT used
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

    await client.send_message(message.channel, "This command is temporarily disabled due to an update that affects "
                                               "into seeing members in Discord.")
    return

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

    # Concatenate account types with number emojis into a numbered list
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
        initial_stats = await static_functions.get_hiscore_data(username, client.aiohttp_session, account_type)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Osrs API answered too slowly and user could not be tracked. "
                                                   "Try again later.")
        return
    except TypeError:
        finish_embed.title = f"Could not find hiscores for user {username} with account type {account_type_formal}."
        await client.edit_message(acc_type_query, embed=finish_embed)
        return
    except ValueError as e:
        error_msg = e.args[0]

        if error_msg == "Username can't be longer than 12 characters.":
            finish_embed.title = "Usernames can't be longer than 12 characters."
        elif "Unknown account type:" in error_msg:
            finish_embed.title = "ValueError: Unknown account type."
        else:
            finish_embed.title = "Unknown error while requesting hiscore  data. Please check the official hiscores " \
                                 "are working as normal."
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


async def add_custom_command(message, keywords, client):
    max_commands = 200
    custom_commands_file = "Data files/Custom_commands.json"
    content = " ".join(keywords)
    start_quote_i = content.find("\"")
    end_quote_i = content.rfind("\"")

    try:
        server_id = message.server.id
    except AttributeError:
        await client.send_message(message.channel, "This command doen't work in private messages.")
        return

    if not await Settings.get_settings(message, client, get_addcom=True):
        await client.send_message(message.channel, "Adding commands is disabled in this server.")
        return
    elif content.count("\"") == 0:
        await client.send_message(message.channel, "Give the message of command inside quotes.")
        return
    elif end_quote_i != len(content) - 1:
        await client.send_message(message.channel, "The command message must be ended with quotes.")
        return

    command_message = content[start_quote_i + 1:end_quote_i].replace("\\n", "\n")
    command = content[:start_quote_i - 1]

    if command_message == "":
        await client.send_message(message.channel, "The command message cannot be empty.")
        return

    with open(custom_commands_file, "r", encoding="utf-8") as data_file:
        data = json.load(data_file)

    try:
        if command[0] != "!":
            command = f"!{command}"
    except IndexError:
        await client.send_message(message.channel, "The command cannot be empty.")
        return

    try:
        server_commands = data[server_id]
    except KeyError:
        data[server_id] = {}
        server_commands = data[server_id]

    if command in server_commands.keys():
        await client.send_message(message.channel, "This command already exists.")
        return
    elif len(list(server_commands)) >= max_commands:
        await client.send_message(message.channel, f"The server commands exceed the limit of {max_commands} custom "
                                                   f"commands. Try deleting some commands first.")
        return

    server_commands[command] = dict(message=command_message, author=message.author.id,
                                    date=int(datetime.datetime.utcnow().timestamp()), edited=None, edit_date=None)

    with open(custom_commands_file, "w", encoding="utf-8") as data_file:
        json.dump(data, data_file, ensure_ascii=False, indent=4)

    await client.send_message(message.channel, f"Successfully added command `{command}`.")


async def execute_custom_command(message, msg_content, client):
    """
    A function that tries to find any custom commands for server if message starts with prefix, and no hard coded ones
    are found.

    :param message:
    :param msg_content:
    :param client:
    """
    try:
        server_id = message.server.id
    except AttributeError:
        # Message was sent by private messages
        return

    with open("Data files/Custom_commands.json", "r", encoding="utf-8") as data_file:
        data = json.load(data_file)

    try:
        command_message = data[server_id][msg_content]["message"]
    except KeyError:
        # No command was found for this server
        return

    await client.send_message(message.channel, command_message)


async def delete_custom_command(message, keywords, client):
    """
    A command function for command %delcom to delete existin server specific custom commands.

    :param message:
    :param keywords:
    :param client:
    """
    command_file = "Data files/Custom_commands.json"
    command = " ".join(keywords)

    try:
        server_id = message.server.id
    except AttributeError:
        await client.send_message(message.channel, "This command doesn't work in private messages.")
        return

    if command[0] != "!":
        command = f"!{command}"

    with open(command_file, "r", encoding="utf-8") as data_file:
        data = json.load(data_file)

    try:
        server_commands = data[server_id]
    except KeyError:
        await client.send_message(message.channel, f"Command `{command}` does not exist.")
        return
    try:
        del server_commands[command]
    except KeyError:
        await client.send_message(message.channel, f"Command `{command}` does not exist.")
        return

    if len(server_commands) == 0:
        del data[server_id]

    with open(command_file, "w", encoding="utf-8") as data_file:
        json.dump(data, data_file, indent=4, ensure_ascii=False)

    await client.send_message(message.channel, f"Successfully deleted command `{command}`.")


async def edit_custom_command(message, cmd_content, client):
    custom_commands_file = "Data files/Custom_commands.json"
    cmd_content = " ".join(cmd_content)
    start_quote_i = cmd_content.find("\"")
    end_quote_i = cmd_content.rfind("\"")

    try:
        server_id = message.server.id
    except AttributeError:
        await client.send_message(message.channel, "This command doesn't work in private messages.")
        return

    if cmd_content.count("\"") == 0:
        await client.send_message(message.channel, "The new message of command must be inside quotes.")
        return
    elif end_quote_i != len(cmd_content) - 1:
        await client.send_message(message.channel, "The new message of command must be ended with quotes.")
        return

    new_command_message = cmd_content[start_quote_i + 1:end_quote_i].replace("\\n", "\n")
    command = cmd_content[:start_quote_i - 1]

    if new_command_message == "":
        await client.send_message(message.channel, "The message of command cannot be empty.")
        return

    with open(custom_commands_file, "r", encoding="utf-8") as data_file:
        data = json.load(data_file)

    try:
        if command[0] != "!":
            command = f"!{command}"
    except IndexError:
        await client.send_message(message.channel, "The command cannot be empty.")
        return

    try:
        command_data = data[server_id][command]
    except KeyError:
        await client.send_message(message.channel, f"Command `{command}` does not exist.")
        return

    command_data["message"] = new_command_message
    command_data["edited"] = message.author.id
    command_data["edit_date"] = int(datetime.datetime.utcnow().timestamp())

    with open(custom_commands_file, "w", encoding="utf-8") as data_file:
        json.dump(data, data_file, indent=4, ensure_ascii=False)

    await client.send_message(message.channel, f"Successfully edited command `{command}`.")


async def get_item_keywords(message, cmd_content, client):
    itemname = " ".join(cmd_content)

    with open("Data files/Item_keywords.json", "r", encoding="utf-8") as keywords_file:
        keyword_data = json.load(keywords_file)

    item_data = await static_functions.get_item_data(itemname)
    if not item_data:
        await client.send_message(message.channel, "Could not find any items with your search.")
        return

    default_itemname = item_data["name"]
    try:
        if itemname.lower() == "all nicks":
            raise KeyError
        keywords_list = [f"`{name}`" for name in keyword_data[default_itemname]]
    except KeyError:
        await client.send_message(message.channel, "Given item has no keywords.")
        return

    await client.send_message(message.channel, "Keywords for {}: {}".format(default_itemname,
                                                                                   ", ".join(keywords_list)))


async def add_item_keywords(message, cmd_content, client):
    item_keywords_file = "Data files/Item_keywords.json"
    with open(item_keywords_file, "r", encoding="utf-8") as keywords_file:
        keywords_data = json.load(keywords_file)

    cmd_content = " ".join(cmd_content).replace(", ", ",").split(",")
    itemname = cmd_content[0]
    keyword_candidates = cmd_content[1:]

    item_data = await static_functions.get_item_data(itemname)
    if not item_data:
        await client.send_message(message.channel, f"Could not find item `{itemname}`.")
        return

    default_itemname = item_data["name"]
    rejected_keywords = []
    accepted_keywords = []

    for keyword in keyword_candidates:
        if keyword in keywords_data["All keywords"] or len(keyword) == 0:
            rejected_keywords.append(keyword)
        else:
            accepted_keywords.append(keyword)

    try:
        current_keywords = keywords_data[default_itemname]
    except KeyError:
        keywords_data[default_itemname] = []
        current_keywords = keywords_data[default_itemname]

    for keyword in accepted_keywords:
        current_keywords.append(keyword)
        keywords_data["All keywords"].append(keyword)

    if len(accepted_keywords) > 0:
        with open(item_keywords_file, "w", encoding="utf-8") as keywords_file:
            json.dump(keywords_data, keywords_file, indent=4, ensure_ascii=False)

        finish_message = "Successfully added {} keywords for {}: {}\nRejected {} keywords: {}"\
            .format(len(accepted_keywords), default_itemname, ", ".join(accepted_keywords), len(rejected_keywords),
                    ", ".join(rejected_keywords))
    else:
        finish_message = "All given keywords are already in use or they were rejected."

    await client.send_message(message.channel, finish_message)


async def delete_item_keywords(message, cmd_content, client):
    item_keywords_file = "Data files/Item_keywords.json"
    with open(item_keywords_file, "r", encoding="utf-8") as keywords_file:
        keywords_data = json.load(keywords_file)

    cmd_content = " ".join(cmd_content).replace(", ", ",").split(",")
    itemname = cmd_content[0]
    keyword_candidates = cmd_content[1:]

    item_data = await static_functions.get_item_data(itemname)
    if not item_data:
        await client.send_message(message.channel, f"Could not find item `{itemname}`.")
        return

    default_itemname = item_data["name"]
    deleted_keywords = []
    keys_not_found = []

    try:
        current_keywords = keywords_data[default_itemname]
    except KeyError:
        await client.send_message(message.channel, "Given item has no keywords.")
        return

    for keyword in keyword_candidates:
        try:
            current_keywords.remove(keyword)
        except ValueError:
            # Item does not have this keyword
            keys_not_found.append(keyword)
            continue
        # This will always succeed except if adding keywords has some serious bugs, so no error handling here
        keywords_data["All keywords"].remove(keyword)
        deleted_keywords.append(keyword)

    if len(deleted_keywords) > 0:
        if len(current_keywords) == 0:
            del keywords_data[default_itemname]
        with open(item_keywords_file, "w", encoding="utf-8") as keywords_file:
            json.dump(keywords_data, keywords_file, indent=4, ensure_ascii=False)

        finish_message = "Successfully deleted {} keywords from `{}`: {}\nRejected deletion of {} keywords: {}"\
            .format(len(deleted_keywords), default_itemname, ", ".join(deleted_keywords), len(keys_not_found),
                    ", ".join(keys_not_found))
    else:
        finish_message = f"Not a single of given keywords in use of {default_itemname}."

    await client.send_message(message.channel, finish_message)


async def roll_die(message: discord.Message, keywords: str, client: discord.Client):
    max_dices = 20
    max_sides = 120

    if not keywords:
        keywords = [6]
    try:
        sides = int(keywords[0])
        rolls = 1
    except ValueError:
        try:
            dice_info = keywords[0].split("d")
            sides = int(dice_info[1])
            rolls = int(dice_info[0])
        except (ValueError, IndexError):
            await client.send_message(message.channel, "Die info was given in invalid format.")
            return

    if sides > 120:
        await client.send_message(message.channel, f"The die can only have maximum of {max_sides} sides.")
        return
    elif rolls > max_dices:
        await client.send_message(message.channel, f"You can throw at most {max_dices} dice at once.")
        return
    elif sides < 1:
        await client.send_message(message.channel, "The die must have at least 1 sides.")
        return
    elif rolls < 1:
        await client.send_message(message.channel, "The die must be thrown at least once.")
        return

    roll_results = []
    for _ in range(rolls):
        roll_result = random.randint(1, sides)
        roll_results.append(roll_result)

    if rolls > 1:
        substr = ", ".join(str(_int) for _int in roll_results)
        msg = f"{sides}-sided die roll results: `{substr}`\n\nTotal sum: {sum(roll_results)}"
    else:
        msg = roll_results[0]

    await client.send_message(message.channel, msg)


async def search_wiki(message: discord.message, keywords: list, cache: Cache, client: discord.client):
    if cache.name == "Melvoridle":
        base_url = "https://wiki.melvoridle.com"
        search = " ".join(keywords).title().replace(" ", "_")
        direct_search_url = f"{base_url}/index.php?title={search}"
        full_search_url = f"{base_url}/index.php?search={search}"

    elif cache.name == "Osrs":
        base_url = "https://oldschool.runescape.wiki"
        search = " ".join(keywords).capitalize().replace(" ", "_")
        direct_search_url = f"{base_url}/w/{search}"
        full_search_url = f"{base_url}/w/Special:Search?search={search}"

    else:
        raise ValueError(f"Unknown cache name: {cache.name}")

    if direct_search_url in cache:
        await client.send_message(message.channel, f"<{direct_search_url}>")
        return

    try:
        await static_functions.make_request(client.aiohttp_session, direct_search_url, raise_on_error=True)
        await client.send_message(message.channel, f"<{direct_search_url}>")
        cache.add(direct_search_url)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Wiki answered too slowly. Try again later.")
        return
    except ValueError:
        try:
            full_search = await static_functions.make_request(client.aiohttp_session, full_search_url)
        except asyncio.TimeoutError:
            await client.send_message(message.channel, "Wiki answered too slowly. Try again later.")
            return

        hyperlinks = static_functions.parse_search_candidates(full_search, base_url, cache)
        if len(hyperlinks) == 0:
            await client.send_message(message.channel, "Could not find any pages.")
            return

        embed = discord.Embed(title="Did you mean", description="\n".join(hyperlinks))
        await client.send_message(message.channel, embed=embed)


async def get_boss_scores(message: discord.Message, keywords: str, client: discord.Client) -> None:

    keywords = keywords.split()
    invoked_with = keywords[0]
    username = " ".join(keywords[1:])

    if invoked_with == "!kc":
        account_type = "normal"
    elif invoked_with == "!ironkc":
        account_type = "ironman"
    elif invoked_with == "!uimkc":
        account_type = "uim"
    elif invoked_with == "!dmmkc":
        account_type = "dmm"
    elif invoked_with == "!seasonkc":
        account_type = "seasonal"
    elif invoked_with == "!hckc":
        account_type = "hcim"
    elif invoked_with == "!lkc" or invoked_with == "!leaguekc":
        account_type = "seasonal"
    else:
        await client.send_message(message.channel, f"Unknown account type with invokation: {invoked_with}")
        return

    try:
        user_stats = await static_functions.get_hiscore_data(username, client.aiohttp_session,
                                                             acc_type=account_type)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "OSRS API answered too slowly. Try again later.")
        return
    except TypeError:
        await client.send_message(message.channel, "Could not find hiscores for user with given account type.")
        return
    except ValueError as e:
        error_msg = e.args[0]

        if error_msg == "Username can't be longer than 12 characters.":
            await client.send_message(message.channel, "Usernames can't be longer than 12 characters.")
        elif "Unknown account type:" in error_msg:
            await client.send_message(message.channel, f"Unknow account type while requesting hiscore data: "
                                                       f"{account_type}.")
        else:
            await client.send_message(message.channel, "Unknown error while requesting hiscore  data. Please check the "
                                                       "official hiscores are working as normal.")
        return

    scoretable = await static_functions.make_boss_scoretable(user_stats, username, account_type)

    try:
        await client.send_message(message.channel, scoretable)
    except discord.errors.HTTPException:
        await client.send_message(message.channel, "Users bossing hiscores exceeds the Discord 2000 character limit. "
                                                   "For now, too long scores are not available with this command.")
        return


if __name__ == "__main__":
    print("Dont run this module as a independent process as it doesn't do anything. Run Main.py instead.")
    exit()
