"""
MIT License

Copyright (c) 2018 Visperi

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
import re
import datetime
import pytz
import traceback
import Settings
from fractions import Fraction

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


def convert_to_utc(timestamp):
    gmt = pytz.timezone("Europe/Helsinki")
    utc = pytz.timezone("UTC")
    timestamp_utc = gmt.localize(timestamp).astimezone(utc)
    return timestamp_utc


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
                role = "\@everyone"
            roles.append(str(role))
    except AttributeError:
        await client.send_message(message.channel, "This command doesn't work in direct messages.")
        return

    user_info = discord.Embed().set_author(name=display_name).set_thumbnail(url=avatar)\
        .add_field(name="Username", value=str(message.author))\
        .add_field(name="Id", value=message.author.id)\
        .add_field(name="User created", value=created_at)\
        .add_field(name="Joined server", value=joined_at)\
        .add_field(name="Role in this server", value=", ".join(roles))
    await client.send_message(message.channel, embed=user_info)


async def commands(message, client):
    discord_commands = ["!info", "!help", "!calc", "!howlong", "!update", "!namechange", "!server commands",
                        "!sub streams", "!unsub streams", "!streamers", "!test"]
    osrs_commands = ["!wiki", "!stats", "!gains", "!track", "!ttm", "!xp", "!ehp", "!nicks", "!loot"]
    clue_commands = ["!cipher", "!anagram", "!puzzle", "!cryptic", "!maps"]
    item_commands = ["!keys", "!limit", "!pricechange", "!price"]
    moderator_commands = ["%addkey", "%delkey", "%addcom", "%delcom", "%editcom", "%addloot", "%delloot"]
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


async def current_price(message, keywords, client):
    """
    Uses Rsbuddy api to search current Grand Exchange prices and high alch value for given item. Coefficient
    can be given to get prices for multiple pieces of the same item.

    :param message: discord.py message object
    :param keywords: Item to search for. Has to be in list format (str.split()). If wanted, coefficient is given here.
    :param client: discord.Client() object
    :return: Sends discord embed containing total prices, unit prices and high alch values into channel the command
    was requested from.
    """

    keywords = " ".join(keywords).replace("*", " * ").split()
    itemname = " ".join(keywords).capitalize()
    coeff = 1
    if "*" in keywords:
        itemname = " ".join(keywords[:keywords.index("*")]).capitalize()
        coeff = keywords[-1]
        try:
            if coeff[-1] == "k":
                coeff = int(coeff[:-1]) * 1000
            elif coeff[-1] == "m":
                coeff = int(coeff[:-1]) * 1000000
            else:
                coeff = int(coeff)
            if coeff == 0:
                await client.send_message(message.channel, "The coefficient cannot be zero.")
                return
        except ValueError:
            await client.send_message(message.channel, "There can't be letters or special signs in the coefficient. "
                                                      "One shortener for thousands (k) and millions (m) can be used.")
            return
        except IndexError:
            await client.send_message(message.channel, "Found multiplication sign but no coefficient. Please check "
                                                       "the spelling.")
            return
    item_info = get_iteminfo(itemname)
    if not item_info:
        await client.send_message(message.channel, "Could not find any items with your keywords.")
        return
    itemname, item_id = item_info[0], item_info[1]
    pcs = "({} kpl)".format("{:,}".format(coeff).replace(",", " "))
    if pcs == "(1 kpl)":
        pcs = ""
    try:
        apipage = requests.get(f"https://api.rsbuddy.com/grandExchange?a=guidePrice&i={item_id}", timeout=4).text
        tradeinfo = json.loads(apipage)
        buying, selling, bquantity, squantity = tradeinfo["buying"], tradeinfo["selling"], \
                                                tradeinfo["buyingQuantity"], tradeinfo["sellingQuantity"]
        unit_price_buy = "({:,} ea)".format(int(buying)).replace(",", " ")
        unit_price_sell = "({:,} ea)".format(int(selling)).replace(",", " ")
        if coeff == 1:
            unit_price_buy, unit_price_sell = "", ""
        total_buyprice = ("{:,} gp".format(int(buying) * coeff)).replace(",", " ")
        if total_buyprice == "0 gp":
            total_buyprice = "Epäaktiivinen"
        total_sellprice = ("{:,} gp".format(int(selling) * coeff)).replace(",", " ")
        if total_sellprice == "0 gp":
            total_sellprice = "Epäaktiivinen"

        item_alch = await get_halch(itemname)
        alch_total = "-"
        unit_alch = ""
        if item_alch != "-":
            unit_alch = "({:,} ea)".format(int(item_alch))
            alch_total = "{:,} gp".format(item_alch * coeff).replace(",", " ")
        if coeff < 2:
            unit_alch = ""

        embed = discord.Embed(title=f"{itemname} {pcs}",
                              description=f"Buy price: {total_buyprice} {unit_price_buy}\n"
                                          f"Sell price: {total_sellprice} {unit_price_sell}\n"
                                          f"High alch: {alch_total} {unit_alch}")\
            .set_footer(text=f"Buying: {bquantity} pcs, Selling: {squantity} pcs")
        await client.send_message(message.channel, embed=embed)
        kayttokerrat("Price")

    except RuntimeError:
        await client.send_message(message.channel,
                                  "RuntimeError: Rsbuddy offline or some other unexpected error happened.")
        return
    except requests.exceptions.ReadTimeout:
        await client.send_message(message.channel, "Rsbuddy answers too slowly. Try again later.")
        return
    except ConnectionError:
        await client.send_message(message.client, "ConnectionError: Runescape offline or some other unexpected error "
                                                  "happened.")
        return
    except ValueError:
        await client.send_message(message.channel, "Rsbuddy gave an incorrect answer. Unfortunately, this is something "
                                                   "that happens randomly now. Try again later.")
        return


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


async def hae_wikista(message, hakusanat, client):
    """ Yhdistää käyttäjän antaman syötteen yhdeksi hakusanaksi ja antaa linkin kyseiselle merkkijonolle osrs-wikiin."""

    x = "_".join(hakusanat)
    y = "+".join(hakusanat)
    valitus = "Did you mean" and "<a href=\"/wiki/{xtitle}\" title=\"{x_korjattu}\">{x_korjattu}</a>" \
        .format(xtitle=x.title(), x_korjattu=x.title().replace("_", " "))
    link = requests.get("http://www.2007.runescape.wikia.com/wiki/{}".format(x))
    ei_sivua = "This page does not exist. Mayhaps it should?"
    did_you_mean = "Did you mean <span class=\"alternative-suggestion\" data-type=\"alternative-suggestion-question\"" \
                   "><a href=\"/wiki/"

    if valitus in link.text:
        x = x.title()
    elif did_you_mean in link.text:
        alku = link.text.find(did_you_mean) + len(did_you_mean)
        loppu = link.text.find("\" title=\"", alku)
        korjaus = link.text[alku:loppu]
        await client.send_message(message.channel, "<http://www.2007.runescape.wikia.com/wiki/{}>".format(korjaus))
        return
    elif ei_sivua in link.text:
        haku = requests.get("http://2007.runescape.wikia.com/wiki/Special:Search?query={}".format(y)).text
        if "No results found." in haku:
            await client.send_message(message.channel, "Hakusanalla ei löytynyt yhtään sivua.")
            return
        else:
            ehdotukset = []
            for i in range(1, 5):
                haku_alku = "class=\"result-link\" data-pos=\"{}\" >".format(i)
                haku_loppu = "</a>\n"
                find_haku_alku = haku.find(haku_alku) + len(haku_alku)
                find_nimi_loppu = haku.find(haku_loppu, find_haku_alku)
                ehdotus = haku[find_haku_alku:find_nimi_loppu]
                if len(ehdotus) > 50:
                    continue
                ehdotukset.append(ehdotus)
            await client.send_message(message.channel, "Tarkoititko jotain näistä:\n{}".format("\n".join(ehdotukset)))
            return

    await client.send_message(message.channel, "<http://www.2007.runescape.wikia.com/wiki/{}>".format(x))
    kayttokerrat("Wiki")


async def get_cipher(message, search, client):
    search = " ".join(search)
    found = []
    with open(f"{path}Ciphers.json") as data_file:
        data = json.load(data_file)
    for cipher in list(data):
        if search in cipher.lower():
            found.append(cipher.lower())
    if len(found) == 0:
        await client.send_message(message.channel, "Couldn't find any cipher clues with your search. Check the "
                                                   "spelling.")
    elif len(found) > 1:
        await client.send_message(message.channel, "Found {} ciphers with your search:\n{}".format(len(found),
                                                                                                   "\n".join(found)))
    elif len(found) == 1:
        cipher = data[found[0].upper()]
        solution, location, answer, kuva = cipher["solution"], cipher["location"], cipher["answer"], cipher["kuva"]
        if not kuva:
            await client.send_message(message.channel, f"Solution: {solution}\nLocation: {location}\nAnswer: {answer}")
        else:
            await client.send_message(message.channel, f"Solution: {solution}\nLocation: {location}\n"
                                                       f"Answer: {answer}\n{kuva}")


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
        master = stats_list[-2]
        elite = stats_list[-3]
        hard = stats_list[-5]
        medium = stats_list[-9]
        easy = stats_list[-10]
        total = stats_list[-8]

        clues = [easy, medium, hard, elite, master, total]
        clue_names = [["Easy"], ["Medium"], ["Hard"], ["Elite"], ["Master"], ["All"]]
        time = 0

        for clue in clues:
            if clue == "-1,-1":
                clue = "0,0"
            clue = clue.split(",")
            for part in clue:
                clue_names[time].append(part)
            time += 1
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
        last_savedate_utc = convert_to_utc(datetime.datetime.strptime(last_savedate, "%d/%m/%Y %H:%M"))\
            .strftime("%d/%m/%Y %H:%M")
        current_date_utc = convert_to_utc(current_date).strftime("%d/%m/%Y %H:%M")

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
                                  .format(last_savedate_utc, current_date_utc,
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
    nick = " ".join(hakusanat).replace("_", " ")
    link = f"http://crystalmathlabs.com/tracker/api.php?type=ttm&player={nick}"
    response = decode_cml(link)
    tunnit = str(math.ceil(float(response))) + " EHP"
    if tunnit == "-1 EHP":
        await client.send_message(message.channel, "Username is not in use or it isn't tracked in CML.")
        return
    elif tunnit == "0 EHP":
        tunnit = "0 EHP (maxed)"
    elif tunnit == "-2 EHP":
        return
    elif tunnit == "-4 EHP":
        await client.send_message(message.channel, "CML api is temporarily out of service due to heavy traffic on "
                                                   "their sites.")
        return

    await client.send_message(message.channel, f"Ttm for {nick}: {tunnit}")
    kayttokerrat("Ttm")


async def hae_anagram(message, hakusanat, client):
    link = "http://2007.runescape.wikia.com/wiki/Anagrams"
    f = requests.get(link)
    sivu = f.text
    hakusana = " ".join(hakusanat).title()
    found = await search_from_file(message, hakusana.lower(), client)

    if not found:
        if hakusana == "":
            return
        elif hakusana == "Arr! So I Am A Crust, And?":
            hakusana = "Arr! So I am a crust, and?"
        elif hakusana == "Mal In Tau":
            hakusana = "Mal in Tau"
        elif hakusana == "Me If":
            hakusana = "Me if"
        elif hakusana == "Pacinng A Taie":
            hakusana = "Pacinng a taie "
        elif hakusana == "R Slicer":
            hakusana = "R SLICER"
        elif hakusana == "Woo An Egg Kiwi":
            hakusana = "Woo an egg kiwi"
        elif hakusana == "Yawns Gy":
            hakusana = "YAWNS GY"
        elif hakusana == "Ded War":
            hakusana = "DED WAR"
        elif hakusana == "His Phor":
            hakusana = "HIS PHOR"

        if hakusana in sivu:
            nimi_alku = "{}</i>\n</td><td><a href=\"/wiki/".format(hakusana)
            nimi_loppu = "\" title=\""
            find_nimi_alku = sivu.find(nimi_alku) + len(nimi_alku)
            find_nimi_loppu = sivu.find(nimi_loppu, find_nimi_alku)
            nimi = sivu[find_nimi_alku:find_nimi_loppu].replace("%27", "'").replace("_", " ")
            if nimi not in sivu:
                await client.send_message(message.channel, "You are the first one to search this anagram. Please write "
                                                           "it as full now so it can be found more easily in the "
                                                           "future.")
                return

            paikka_alku = "{}</a>\n</td><td>".format(nimi)
            paikka_vastaus_loppu = "</td><td>"
            find_paikka_alku = sivu.find(paikka_alku) + len(paikka_alku)
            find_paikka_loppu = sivu.find(paikka_vastaus_loppu, find_paikka_alku)
            paikka_raaka = (sivu[find_paikka_alku:find_paikka_loppu])
            paikka = re.sub("<[^>]+>", "", paikka_raaka).strip("\n").replace("•", "")

            vastaus_alku = "{}</td><td>".format(paikka_raaka)
            find_vastaus_alku = sivu.find(vastaus_alku) + len(vastaus_alku)
            find_vastaus_loppu = sivu.find(paikka_vastaus_loppu, find_vastaus_alku)
            vastaus_raaka = sivu[find_vastaus_alku:find_vastaus_loppu]
            vastaus = re.sub("<[^>]+>", "", vastaus_raaka).strip("\n")

            if "redlink=" in nimi or "redlink=" in paikka or "redlink=" in vastaus:
                await client.send_message(message.channel, "Anagram needs to be added manually due to its different "
                                                           "coding.")
                return
            if nimi and paikka and vastaus:
                with open(f"{path}Anagrams.json") as data_file:
                    data = json.load(data_file)
                data[hakusana.lower()] = {"solution": nimi, "location": paikka, "challenge_answer": vastaus,
                                          "puzzle": ""}
                with open(f"{path}Anagrams.json", "w") as data_file:
                    json.dump(data, data_file, indent=4)

                await client.send_message(message.channel, "Solution: {nimi}\nLocation: {paikka}\nChallenge answer: "
                                                           "{vastaus}\n\nAnagrammi tallennettiin tiedostoon ja löytyy "
                                                           "nyt myös osittaisella hakusanalla."
                                          .format(nimi=nimi, paikka=paikka, vastaus=vastaus))
                kayttokerrat("Anagram")
        else:
            await client.send_message(message.channel,
                                        "Couldn't find any anagrams with your search. Check the spelling.")


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
    hakusanat = "".join(hakusanat).replace("**", "^").replace(",", "")
    operation = None
    result = None
    operators = ["+", "-", "*", "^", "/"]
    for operator in operators:
        if operator in hakusanat:
            hakusanat = hakusanat.split(operator)
            operation = operator
    if not operation:
        await client.send_message(message.channel, "Unknown operator. Check all the available operators with command "
                                                   "`!help calc`.")
        return

    if len(hakusanat) > 2:
        await client.send_message(message.channel, "The calculator supports only two factor calculations without "
                                                   "brackets or variables.")
        return

    for factor in hakusanat:
        index = hakusanat.index(factor)
        try:
            if factor[-1] == "m":
                hakusanat[index] = float(factor[:-1]) * 1000000
            elif factor[-1] == "k":
                hakusanat[index] = float(factor[:-1]) * 1000
            else:
                hakusanat[index] = float(factor)
        except ValueError:
            await client.send_message(message.channel, "Other or both factors had a variable or other characters that "
                                                       "cannot be converted to numbers.")
            return

    factor1, factor2 = hakusanat[0], hakusanat[1]
    try:
        if operation == "+":
            result = factor1 + factor2
        elif operation == "-":
            result = factor1 - factor2
        elif operation == "*":
            result = factor1 * factor2
        elif operation == "^":
            result = factor1 ** factor2
        elif operation == "/":
            try:
                result = factor1 / factor2
            except ZeroDivisionError:
                await client.send_message(message.channel, "Dividing by zero is undefined.")
                return
    except OverflowError:
        await client.send_message(message.channel, "The result is too big to be calculated")
        return
    if result:
        rounded = round(result, 3)
        result = "{:,}".format(rounded).replace(",", " ")
        await client.send_message(message.channel, result)
        kayttokerrat("calc")


async def ehp_laskuri(message, hakusanat, client):
    otsikko = hakusanat[0].capitalize()
    tiedosto = f"{path}Ehp.txt"
    if message.content.startswith("!ironehp"):
        tiedosto = "{}Ehp_ironman.txt".format(path)
    elif message.content.startswith("!skillerehp"):
        tiedosto = "{}Ehp_skiller.txt".format(path)

    with open(tiedosto, "r") as file:
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
            await client.send_message(message.channel, "Komento on jo olemassa.")
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
        if message.content.startswith("!cryptic "):
            await client.send_message(message.channel, data[keys_found[0]])
            kayttokerrat("cryptic")
        else:
            return [keys_found[0], data[keys_found[0]]]
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
    await client.send_message(message.channel, "<http://2007.runescape.wikia.com/wiki/Treasure_Trails/Guide/Maps>")


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


async def hinnanmuutos(message, keywords, client):
    keyword = " ".join(keywords)
    item_info = get_iteminfo(keyword)
    if not item_info:
        await client.send_message(message.channel, "Could not find any items with your keyword.")
        return
    else:
        itemname, item_id = item_info[0], item_info[1]

    def laske_muutos(vanha, nykyinen):
        muutos = nykyinen - vanha
        if muutos < 0:
            muutos = "{:,} gp".format(muutos).replace(",", " ")
        elif muutos > 0:
            muutos = "+{:,} gp".format(muutos).replace(",", " ")
        elif muutos == 0:
            muutos = "0 gp"
        return muutos

    def get_time(timestamp):
        time = convert_to_utc(datetime.datetime.fromtimestamp(int(timestamp) / 1000)).strftime("%d/%m/%Y %H:%M")
        return time

    try:
        api_hours = requests.get(f"https://api.rsbuddy.com/grandExchange?a=graph&g=60&i={item_id}", timeout=4)
        api_month = requests.get(f"https://api.rsbuddy.com/grandExchange?a=graph&g=1440&i={item_id}", timeout=4)
        prices_hourly = json.loads(api_hours.text)
        prices_daily = json.loads(api_month.text)
    except ValueError:
        traceback.print_exc()
        await client.send_message(message.channel, "Rsbuddy gave an incorrect answer. Unfortunately, this is something "
                                                   "that happens randomly now. Try again later.")
        return
    except requests.exceptions.ReadTimeout:
        await client.send_message(message.channel, "Rsbuddy answers too slowly. Try again later.")
        return
    try:
        price_now = int(prices_hourly[-1]["overallPrice"])
        latest_timestamp = get_time(prices_hourly[-1]["ts"])
    except IndexError:
        await client.send_message(message.channel, "Item has not been traded in G.E. yet.")
        return
    if price_now == 0 or len(prices_hourly) < 3:
        await client.send_message(message.channel, "Item is being traded too rarely to calculate price changes.")
        return
    try:
        price_month_ago = int(prices_daily[0]["overallPrice"])
        price_week_ago = int(prices_hourly[0]["overallPrice"])
    except IndexError:
        await client.send_message(message.channel, "Rsbuddy price history has currently some problems sending "
                                                   "the data. Try again later.")
        return
    try:
        price_24h = int(prices_hourly[-24]["overallPrice"])
        price_hour = int(prices_hourly[-2]["overallPrice"])
    except IndexError:
        stylished_prices = []
        price_third_last, third_last_ts = int(prices_hourly[-3]["overallPrice"]), get_time(prices_hourly[-3]["ts"])
        price_before_now, before_now_ts = int(prices_hourly[-2]["overallPrice"]), get_time(prices_hourly[-2]["ts"])
        month_ago_ts, week_ago_ts = get_time(prices_daily[0]["ts"]), get_time(prices_hourly[0]["ts"])
        for hinta in [price_month_ago, price_week_ago, price_third_last, price_before_now, price_now]:
            stylished_prices.append("{:,} gp".format(hinta).replace(",", " "))
        embed = discord.Embed(title=f"Prices from different times for {itemname}",
                               description=f"{month_ago_ts}: {stylished_prices[0]}\n"
                                           f"{week_ago_ts}: {stylished_prices[1]}\n"
                                           f"{third_last_ts}: {stylished_prices[2]}\n"
                                           f"{before_now_ts}: {stylished_prices[3]}\n"
                                           f"{latest_timestamp}: {stylished_prices[4]}")
        await client.send_message(message.channel, "Item is being traded too rarely to calculate price changes.",
                                  embed=embed)
        kayttokerrat("pricechange")
        return
    kuukaudessa = laske_muutos(price_month_ago, price_now)
    viikossa = laske_muutos(price_week_ago, price_now)
    paivassa = laske_muutos(price_24h, price_now)
    tunnissa = laske_muutos(price_hour, price_now)
    hinta_nyt = "{:,} gp".format(price_now).replace(",", " ")
    embed = discord.Embed(title=f"Price changes for {itemname}",
                           description=f"In a month: {kuukaudessa}\n"
                                       f"In a week: {viikossa}\n"
                                       f"In a day: {paivassa}\n"
                                       f"In a hour: {tunnissa}\n"
                                       f"Latest price: {hinta_nyt}")\
        .set_footer(text=f"Latest price from {latest_timestamp} UTC")
    await client.send_message(message.channel, embed=embed)
    kayttokerrat("pricechange")


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
            await client.send_message(message.channel, "No answer, operation cancelled.")
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


async def search_from_file(message, search, client):
    hits = []
    with open(f"{path}Anagrams.json") as data_file:
        data = json.load(data_file)
    for anagram in list(data):
        if search == anagram:
            hits = [anagram]
            break
        if search in anagram:
            hits.append(anagram)
    if len(hits) == 0:
        found = False
    elif len(hits) == 1:
        found = True
        anagram = hits[0]
        solution = data[anagram]["solution"]
        location = data[anagram]["location"]
        answer = data[anagram]["challenge_answer"]
        puzzle = data[anagram]["puzzle"]
        await client.send_message(message.channel, f"Solution: {solution}\nLocation: {location}\n"
                                                   f"Challenge answer: {answer}\n{puzzle}")
        kayttokerrat("Anagram")
    else:
        await client.send_message(message.channel, "Found {} anagrams:\n{}\n\nIf you dont see your anagram in this "
                                                   "list, try searching with the whole anagram."
                                  .format(len(hits), "\n".join(hits)))
        found = True
    return found


async def latest_update(message, client):
    from bs4 import BeautifulSoup

    dates = []
    news_html = []
    article_numbers = []

    link = "http://oldschool.runescape.com/"
    try:
        html = requests.get(link, timeout=4).text
    except requests.exceptions.ReadTimeout:
        await client.send_message(message.channel, "oldschool.runescape.com answers too slowly. Try again later.")
        return
    html_parsed = BeautifulSoup(html, "html.parser")
    for i in html_parsed.findAll("time"):
        if i.has_attr("datetime"):
            dates.append(i["datetime"])
    latest_date = max(dates)

    for j in html_parsed.find_all("div", attrs={"class": "news-article__details"}):
        if j.find("time")["datetime"] == latest_date:
            news_html.append(j.find("p"))
    for k in news_html:
        article_number = int(k.find("a")["id"].replace("news-article-link-", ""))
        article_numbers.append(article_number)
    min_article_nr = min(article_numbers)
    for l in news_html:
        article_number = int(l.find("a")["id"].replace("news-article-link-", ""))
        if article_number == min_article_nr:
            news_link = l.find("a")["href"]
            await client.send_message(message.channel, f"Latest news regarding Osrs: {news_link}")
            return


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
        last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(f"{path}Main_menu.py")).strftime("%d/%m/%Y")
        embed = discord.Embed(title=bot_name, description=f"Developer: {bot_owner.mention}\n"
                                                          f"Updated: {last_modified}\nSource code: Python 3.6")
        embed.add_field(name="Credits",
                        value="[discord.py](https://github.com/Rapptz/discord.py)\n"
                              "[Rsbuddy](https://rsbuddy.com/) (price, pricechange)\n"
                              "[Crystalmathlabs](http://www.crystalmathlabs.com/tracker/) (ttm, nicks, ehp)\n"
                              "[Old school runescape](http://oldschool.runescape.com/) (whole game, user stats)\n"
                              "[OSRS Wiki](http://oldschoolrunescape.wikia.com/wiki/Old_School_RuneScape_Wiki) "
                              "(wiki, clues, high alch values)")
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

    def calculate_chance(rate, attempts):
        chance_raw = (1 - (1 - rate) ** attempts) * 100
        if chance_raw < 0.01:
            chance = "< 0.01%"
        elif chance_raw > 99.99:
            chance = "> 99.99%"
        else:
            rounded = round(chance_raw, 2)
            chance = f"{rounded}%"
        return chance

    keywords = " ".join(keywords).replace(", ", ",").split(",")
    if keywords[0].lower() == "misc":
        return
    try:
        droprate, tries = Fraction(keywords[0].replace(" ", "")), int(keywords[1])
        if droprate > 1:
            droprate = Fraction(1, droprate)
        if tries < 1:
            if tries == 0:
                await client.send_message(message.channel, "0%")
            else:
                await client.send_message(message.channel, "The amount of tries can't be smaller than zero.")
            return
        drop_chance = calculate_chance(float(droprate), tries)
        if "73" in str(drop_chance.replace(".", "")):
            drop_chance = f"{drop_chance} :joy:"
        await client.send_message(message.channel, drop_chance)
    except IndexError:
        await client.send_message(message.channel, "Please also give the number of tries, separated by comma.")
        return

    except ValueError:
        with open(f"{path}droprates.json") as data_file:
            data = json.load(data_file)
        if len(keywords) < 3 and keywords[0].capitalize() in data:
            chances_list = []
            dropper = keywords[0].capitalize()
            try:
                tries = int(keywords[1])
                if tries < 1:
                    await client.send_message(message.channel, "The number of tries must be at least one.")
                    return
            except IndexError:
                tries = 1
            except ValueError:
                itemname = keywords[1].capitalize()
                if itemname not in data[dropper]:
                    await client.send_message(message.channel, "Given target doesnt't have this drop.")
                else:
                    item_chance = calculate_chance(float(Fraction(data[dropper][itemname])), 1)
                    await client.send_message(message.channel, item_chance)
                return
            for drop in data[dropper]:
                droprate = Fraction(data[dropper][drop])
                item_chance = calculate_chance(float(droprate), tries)
                if "73" in str(item_chance).replace(".", ""):
                    chances_list.append(f"**{drop}**: {item_chance} :joy:")
                else:
                    chances_list.append(f"**{drop}**: {item_chance}")
            await client.send_message(message.channel, "Probabilities to get drops with {} tries:\n\n{}"
                                      .format(tries, "\n".join(chances_list)))
        else:
            if len(keywords) < 3:
                keywords.insert(0, "Misc")
                if len(keywords) < 3:
                    keywords.insert(2, 1)
            try:
                dropper, itemname, tries = keywords[0].capitalize(), keywords[1].capitalize(), int(keywords[2])
                droprate = Fraction(data[dropper][itemname])
                item_chance = calculate_chance(float(droprate), tries)
            except ValueError:
                await client.send_message(message.channel, "The number of tries must be an integer and other "
                                                           "parameters must be strings. Check more specific info with "
                                                           "command `!help loot`.")
                return
            except KeyError:
                await client.send_message(message.channel, "There is no saved droprate for this item.")
                return
            await client.send_message(message.channel, item_chance)


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
    if site == "rsbuddy":
        link = "https://api.rsbuddy.com/grandExchange?a=guidePrice&i=4151"
    elif site == "wiki":
        link = "http://oldschoolrunescape.wikia.com/wiki/Old_School_RuneScape_Wiki"
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


if __name__ == "__main__":
    print("Tätä moduulia ei ole tarkoitettu ajettavaksi itsessään. Suorita Kehittajaversio.py tai Main_menu.py")
    print("Suljetaan...")
    exit()
