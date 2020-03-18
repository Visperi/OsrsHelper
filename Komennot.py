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
import requests
import Settings
from fractions import Fraction
from bs4 import BeautifulSoup
from mathparse import mathparse
import pytz

path = "{}/".format(os.path.dirname(__file__))
if path == "/":
    path = ""


async def send_message(msg_string, message, client, embed=False):
    if embed:
        pass
    else:
        await client.send_message(message.channel, msg_string)


def to_utf8(string):
    string = string.replace("Ã¤", "ä").replace("Ã¶", "ö").replace("/ae", "ä").replace("/oe", "ö").replace("Ã„", "Ä") \
        .replace("Ã–", "Ö").replace("Â§", "§").replace("/ss", "§")
    return string


def to_ascii(string):
    string = string.replace("ä", "/ae").replace("ö", "/oe").replace("Ä", "/AE").replace("Ö", "/OE").replace("§", "/ss")
    return string


def decode_cml(link):
    response = requests.get(link)
    response.encoding = "utf-8-sig"
    return response.text


async def function_help(message, keywords, client):
    command = " ".join(keywords).replace("!", "").replace("%", "").replace("&", "")
    if not command:
        msg = "`!info`: Perustietoa botista ja viimeisimmät päivitykset\n" \
              "`!commands`: Lista kaikista käytettävissä olevista komennoista\n" \
              "`!server commands`: Lista kaikista tämän serverin omista komennoista\n" \
              "`!help <komennon nimi>`: Käyttöohjeet yksittäiselle komennolle"
        await client.send_message(message.channel, msg)
        return
    with open(f"{path}Help.json", encoding="utf-8") as data_file:
        data = json.load(data_file)
    for obj in data:
        if command in obj["function"]:
            name, description, additional, example = obj["name"], obj["description"], obj["additional"], obj["example"]
            await client.send_message(message.channel, f"**{name}**\n"
                                                       f"{description}\n\n"
                                                       f"**Lisätietoa:** {additional}\n"
                                                       f"**Esimerkki:** {example}")
            return
    await client.send_message(message.channel, "Hakemaasi komentoa ei löytynyt. Komennolla `!commands` saat listan "
                                               "kaikista käytettävissä olevista komennoista.")


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
        await client.send_message(message.channel, "Komento ei toimi yksityisviesteissä.")
        return

    user_info = discord.Embed().set_author(name=display_name).set_thumbnail(url=avatar) \
        .add_field(name="Username", value=str(message.author)) \
        .add_field(name="Id", value=message.author.id) \
        .add_field(name="Käyttäjä luotu", value=created_at) \
        .add_field(name="Liittyi serverille", value=joined_at) \
        .add_field(name="Roolit tällä serverillä", value=", ".join(roles))
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
        .add_field(name="Item commands", value="\n".join(item_commands)) \
        .add_field(name="Discord commands", value="\n".join(discord_commands)) \
        .add_field(name="Clue commands", value="\n".join(clue_commands)) \
        .add_field(name="High permission commands", value="\n".join(moderator_commands)) \
        .add_field(name="Settings commands", value="\n".join(settings_commands)) \
        .set_footer(text="Jos tarvitset apua komentojen käytössä, käytä komentoa !help <komento>")
    await client.send_message(message.channel, embed=viesti)


def get_iteminfo(itemname: str, default_names=False):
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


async def current_price(message, client):
    """
    DEPRECATED
    """
    await client.send_message(message.channel, "Komento on valitettavasti jouduttu ottamaan pois käytöstä. Lisätietoa "
                                               "komennolla `!prices`.")
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
        await client.send_message(message.channel, "Antamaasi itemiä ei löytynyt.")
        return
    if len(new_keys) == 0 or new_keys[0] == "":
        await client.send_message(message.channel, "Itemille täytyy antaa vähintään yksi uusi avainsana.")
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
        denied_msg = f"{discarded_keys} avaimista hylättiin, koska ne sisälsi kertomerkkejä. Lisätietoa saat " \
            f"komennolla `!help addkey`"
    if len(approved_keys) == 0:
        await client.send_message(message.channel, f"Kaikki antamasi avainsanat ovat varattuja. {denied_msg}")
        return
    else:
        with open(f"{path}Item_keywords.json", "w") as data_file:
            json.dump(data, data_file, indent=4)
            await client.send_message(message.channel, "Lisättiin seuraavat avainsanat itemille {}: `{}`. {}"
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
        await client.send_message(message.channel, "Haullasi ei löytynyt yhtään itemiä.")
        return
    if len(deletelist) == 0 or deletelist[0] == "":
        await client.send_message(message.channel, "Anna vähintään yksi avainsana, jonka haluat poistaa itemiltä.")
        return
    with open(file) as data_file:
        data = json.load(data_file)
    try:
        item_keys = data[itemname]
        delete_keys = []
    except KeyError:
        await client.send_message(message.channel, "Itemille ei ole asetettu yhtään avainsanaa.")
        return
    for keyword in deletelist:
        keyword = to_ascii(keyword)
        if keyword in item_keys:
            delete_keys.append(keyword)
    if len(delete_keys) == 0:
        await client.send_message(message.channel, "Yhtäkään antamistasi avainsanoista ei ole asetettu tälle itemille.")
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
                              f"Seuraavat avainsanat poistettiin itemiltä {itemname.capitalize()}: `{deleted_keys}`.")
    kayttokerrat("Delkey")


async def get_keys(message, hakusanat, client):
    itemname = " ".join(hakusanat).lower()
    nicks_utf8 = []
    iteminfo = get_iteminfo(itemname, default_names=True)
    if not iteminfo:
        await client.send_message(message.channel, "Haullasi ei löytynyt yhtään itemiä.")
        return
    with open(f"{path}Item_keywords.json") as data_file:
        data = json.load(data_file)
    try:
        nicks_ascii = data[itemname]
        for nick in nicks_ascii:
            nicks_utf8.append(to_utf8(nick))
        embed = discord.Embed(title=f"Avainsanat itemille {itemname.capitalize()}", description="\n".join(nicks_utf8))
        await client.send_message(message.channel, embed=embed)
    except KeyError:
        await client.send_message(message.channel, "Tavaralle ei ole asetettu avainsanoja.")


async def search_wiki(message, hakusanat: list, client, get_html=False):
    baselink = "https://oldschool.runescape.wiki/w/"

    search = "_".join(hakusanat)
    search_link = baselink + search
    response = requests.get(search_link).text
    if f"This page doesn&#039;t exist on the wiki. Maybe it should?" in response:
        if get_html:
            return TypeError
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
        await client.send_message(message.channel, "Haullasi ei löytynyt yhtään cipheriä. Tarkista oikeinkirjoitus.")
    elif len(partial_matches) > 1:
        await client.send_message(message.channel, "Haullasi löytyi {} cipheriä:\n{}"
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
        await client.send_message(message.channel, "Antamaasi puzzlea ei löytynyt.")
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
                await client.send_message(message.channel, "Käyttäjää ei löytynyt.")
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
        await client.send_message(message.channel, "Anna myös käyttäjä, jonka gainseja haluat tarkastella. Apua "
                                                   "tähän komentoon saat komennolla `!help gains`.")
        return

    tracked = check_if_tracked(username)
    if tracked:
        with open(f"{path}statsdb.json") as data_file:
            data = json.load(data_file)
        try:
            stats_past = data[username]["past_stats"]
        except KeyError:
            await client.send_message(message.channel, "KeyError: Käyttäjä on seurattu, mutta vanhoja tietoja ei "
                                                       "löydetty. Ilmoita tästä ylläpitäjälle. Löydät hänet "
                                                       "käyttämällä komentoa `!info`.")
            return

        stats_recent = await hae_highscoret(message, hakusanat, client, data[username]["account_type"], gains=True)
        if not stats_recent:
            return
        gains_list = [["Total"], ["Attack"], ["Defence"], ["Strength"], ["Hitpoints"], ["Ranged"], ["Prayer"],
                      ["Magic"], ["Cooking"], ["Woodcutting"], ["Fletching"], ["Fishing"], ["Firemaking"],
                      ["Crafting"], ["Smithing"], ["Mining"], ["Herblore"], ["Agility"], ["Thieving"], ["Slayer"],
                      ["Farming"], ["Runecrafting"], ["Hunter"], ["Construction"]]
        last_savedate = data[username]["saved"]
        current_date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

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
        await client.send_message(message.channel, "Nimimerkki ei ole seurannassa. Käytä ensin komentoa "
                                                   "`!track <nimimerkki>`. Jos tiedät laittaneesi nimimerkin "
                                                   "seurantaan, käytä komentoa `!namechange`.")
    else:
        await client.send_message(message.channel, "Nimimerkki ei ole seurannassa eikä sille löytynyt vanhoja nimiä "
                                                   "CML:n tietokannasta. Jos olet vaihtanut nimeä, käytä komentoa "
                                                   "`!namechange`. Muussa tapauksessa käytä `!track <nimimerkki>`.")


async def time_to_max(message, hakusanat, client):
    await client.send_message(message.channel, "Komento on poistettu käytöstä, koska CML:n API ei ole enää julkisesti "
                                               "käytössä tai toimii todella huonosti.")
    return
    # nick = " ".join(hakusanat).replace("_", " ")
    # link = f"http://crystalmathlabs.com/tracker/api.php?type=ttm&player={nick}"
    # response = decode_cml(link)
    # tunnit = str(math.ceil(float(response))) + " EHP"
    # if tunnit == "-1 EHP":
    #     await client.send_message(message.channel, "Käyttäjänimi ei ole käytössä tai sitä ei ole päivitetty kertaakaan "
    #                                                "CML:ssä.")
    #     return
    # elif tunnit == "0 EHP":
    #     tunnit = "0 EHP (maxed)"
    # elif tunnit == "-2 EHP":
    #     return
    # elif tunnit == "-4 EHP":
    #     await client.send_message(message.channel, "CML:n api on väliaikaisesti poissa käytöstä johtuen "
    #                                                "ruuhkautuneesta liikenteestä heidän sivuilla.")
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
            await client.send_message(message.channel, "Haullasi löytyi {} anagrammia:\n{}\n\nKokeile tarkentaa "
                                                       "hakuasi.".format(matches, "\n".join(partial_matches)))
        elif matches > 10:
            await client.send_message(message.channel, "Haullasi löytyi yli 10 anagrammia. Kokeile tarkentaa hakuasi.")
        else:
            await client.send_message(message.channel, "Haullasi ei löytynyt yhtään anagrammia.")


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
                await client.send_message(message.channel, "Levelin täytyy olla kokonaisluku.")
                return
            if int(x[0]) > 127:
                await client.send_message(message.channel, "Annoit liian ison levelin. Pelin isoin level on 127 tai "
                                                           "max.")
            else:
                for exp in experiences:
                    if str(x[0]) == exp[0]:
                        if exp[0] == "127":
                            await client.send_message(message.channel, "Maksimileveliin tarvittava xp: {:,}"
                                                      .format(int(exp[1])).replace(",", " "))
                        else:
                            await client.send_message(message.channel, "Leveliin {} tarvittava xp: {:,}"
                                                      .format(x[0], int(exp[1])).replace(",", " "))
                        kayttokerrat("Xp")
        elif len(x) == 2:
            try:
                lvl_isompi = int(x[1])
                lvl_pienempi = int(x[0])
            except ValueError:
                await client.send_message(message.channel, "Levelien täytyy olla kokonaislukuja.")
                return
            if lvl_isompi > 127 or lvl_pienempi > 127:
                await client.send_message(message.channel, "Annoit liian ison levelin. Pelin isoin level on 127 tai "
                                                           "max.")
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
                await client.send_message(message.channel, "Tarvittava xp level välillä {}-{}: {:,}"
                                          .format(x[0], x[1], xp_erotus).replace(",", " "))
                kayttokerrat("Xp")
            else:
                await client.send_message(message.channel, "Moi mitä kullu")


async def laskin(message, hakusanat, client):
    equation = " ".join(hakusanat).replace("^", " ^ ").replace("**", " ^ ").replace(",", ".").replace("+", " + ")\
        .replace("-", " - ").replace("*", " * ").replace("/", " / ")
    try:
        solution = mathparse.parse(equation)
    except IndexError:
        await client.send_message(message.channel, "Yhtälö ei ollut tuetussa muodossa. Kokeile laittaa osa yhtälöstä "
                                                   "sulkuihin tai tarkista tuetut laskut komennolla `!help calc`.")
        return
    except ValueError:
        await client.send_message(message.channel, "Laskin ei pystynyt laskemaan jotain osaa yhtälöstä. Kaikki ei "
                                                   "tuetut laskujärjestykset eivät ole vielä tiedossa, joten yritä "
                                                   "uudelleen laskemalla lasku osissa.")
        return
    except KeyError:
        await  client.send_message(message.channel, "Yhtälössä oli tekijöitä joita ei voitu muuttaa numeroiksi.")
        return
    except OverflowError:
        await client.send_message(message.channel, "Laskun tulos oli liian suuri tällä komennolla laskemiseen.")
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
                taulukko = "\n".join(skill.replace("{}:\n".format(otsikko), f"{otsikko}\n").split("\n"))
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
        await client.send_message(message.channel, "Komentojen lisäys on asetettu pois päältä.")
        return
    if len(words_raw) < 2:
        await client.send_message(message.channel, "Anna sekä komento että viesti.")
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
            await client.send_message(message.channel, "Annoit vääränlaisen syötteen. Anna ensin komento ja sitten "
                                                       "viesti lainausmerkeissä. Apua saat komennolla `!help addcom`.")
            return
    except TypeError:
        await client.send_message(message.channel, "Komennon viestin täytyy alkaa ja päättyä lainausmerkillä. "
                                                   "Anna ensin komento ja sitten viesti. Älä anna mitään muuta "
                                                   "viestissäsi.")
        return
    except IndexError:
        await client.send_message(message.channel, "Komennon nimi ei saa olla pelkkiä huutomerkkejä, sillä ne "
                                                   "poistetaan siitä joka tapauksessa. Siten tämä komento olisi "
                                                   "tyhjä merkkijono.")
        return
    except ValueError:
        await client.send_message(message.channel, f"Komennon nimen maksimipituus on 30 merkkiä. Sinun "
                                                   f"oli {len(command_raw)}.")
        return
    with open(file) as data_file:
        data = json.load(data_file)
    try:
        server_commands = list(data[server])
        if command in server_commands:
            await client.send_message(message.channel, "Komento on jo olemassa.")
            return
        elif len(server_commands) > 199:
            await client.send_message(message.channel, "Komentojen maksimimäärä on 200 kappaletta, joka on tällä "
                                                       "guildilla jo täyttynyt.")
            return
    except KeyError:
        data[server] = {}
    data[server][command] = {"message": viesti}
    with open(file, "w") as data_file:
        json.dump(data, data_file, indent=4)
    await client.send_message(message.channel, "Komento `{}` lisätty.".format(to_utf8(command)))
    if (command_raw[0] == "!" and command_raw.count("!") > 1) or (command_raw[0] != "!" and command_raw.count("!") > 0):
        await client.send_message(message.channel, "Komennon nimessä ei voi olla huutomerkkejä ja ne poistettiin "
                                                   "automaattisesti.")
    kayttokerrat("addcom")


async def get_custom_commands(message, client):
    try:
        server = message.server.id
    except AttributeError:
        await client.send_message(message.channel, "Komento ei ole käytössä yksityisviesteissä.")
        return
    custom_commands = []
    with open(f"{path}Custom_commands.json") as data_file:
        data = json.load(data_file)
    custom_commands_raw = list(data[server])
    if len(custom_commands_raw) == 0:
        await client.send_message(message.channel, "Serverillä ei ole yhtään komentoa.")
        return
    for command in custom_commands_raw:
        custom_commands.append(to_utf8(command))
    embed = discord.Embed(title=f"Omat komennot serverille {str(message.server).capitalize()}")
    embed.set_footer(text=f"Komentoja yhteensä: {len(custom_commands)}")

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
        await client.send_message(message.channel, "Haullasi ei löytynyt yhtään cluea.")
        return
    else:
        if len("\n".join(keys_found)) > 2000:
            await client.send_message(message.channel, "Haullasi löytyi useita clueja, eivätkä niiden avainsanat mahdu "
                                                       "yhdelle viestikentälle. Kokeile tarkentaa hakuasi.")
            return
        await client.send_message(message.channel, "Haullasi löytyi {} cluea:\n\n{}".format(len(keys_found),
                                                                                            "\n".join(keys_found)))
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
            await client.send_message(message.channel, "Komento `{}` poistettu.".format(to_utf8(komento)))
            kayttokerrat("delcom")
    else:
        await client.send_message(message.channel, "Komentoa ei ole olemassa.")


async def get_buylimit(message, keywords, client):
    """
    Gives a four hour Grand Exchange limit for an item if there is any
    """
    keyword = " ".join(keywords)
    iteminfo = get_iteminfo(keyword)
    if not iteminfo:
        await client.send_message(message.channel, "Haullasi ei löytynyt yhtään itemiä.")
        return
    else:
        itemname = iteminfo[0]
    with open(f"{path}Buy_limits.json") as data_file:
        data = json.load(data_file)
    try:
        buy_limit = data[itemname]
    except KeyError:
        await client.send_message(message.channel, "Itemille ei löytynyt ostorajaa. Ilmoitathan, jos huomaat virheen, "
                                                   "niin korjataan tilanne.")
        return
    await client.send_message(message.channel, f"Neljän tunnin ostorajoitus itemille {itemname}: {buy_limit} kpl.")
    kayttokerrat("Limit")


def kayttokerrat(function_used):
    """Keeps a record of how many times most of commands are used. Updates every time some command is used.

    :param function_used: Name of the function in string format
    :return: Nothing
    """
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


async def track_user(message, hakusanat, client):
    name = " ".join(hakusanat).replace("_", " ")
    link = "http://services.runescape.com/m=hiscore_oldschool/index_lite.ws?player={}".format(name)
    request = requests.get(link).text

    async def get_user_type(username):
        account_type = None
        reactions = ["1\u20e3", "2\u20e3", "3\u20e3", "4\u20e3", "5\u20e3", "6\u20e3", "\N{CROSS MARK}"]
        choices = ["1\u20e3 Normaali", "2\u20e3 Ironman", "3\u20e3 Uim", "4\u20e3 Hcim", "5\u20e3 Dmm",
                   "6\u20e3 Seasonal", "\N{CROSS MARK} Peruuta"]
        bot_embed = discord.Embed(title=f"Mikä on hahmon {username} tyyppi?", description="\n".join(choices)) \
            .set_footer(text="Botti rekisteröi reaktiosi vasta vaihtoehtojen latauduttua.")
        bot_message = await client.send_message(message.channel, embed=bot_embed)
        for reaction in reactions:
            await client.add_reaction(bot_message, reaction)
        answer = await client.wait_for_reaction(emoji=reactions, message=bot_message, user=message.author, timeout=7)
        if not answer:
            await client.edit_message(bot_message, embed=discord.Embed(title="Ei vastausta, toiminto peruutettu."))
            return
        elif answer.reaction.emoji == reactions[-1]:
            await client.edit_message(bot_message, embed=discord.Embed(title="Toiminto peruutettu"))
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
        await client.edit_message(bot_message, embed=discord.Embed(title="Aloitettiin käyttäjän {} seuranta. "
                                                                         "Käyttäjän tyyppi: {}"
                                                                   .format(username, account_type.capitalize())))
        return account_type

    with open(f"{path}Tracked_players.json") as data_file:
        data = json.load(data_file)
    if "404 - Page not found" in request:
        await client.send_message(message.channel, "Käyttäjää ei löytynyt.")
        return
    if name in list(data):
        await client.send_message(message.channel, "Käyttäjä on jo seurannassa.")
        return
    try:
        acc_type = await get_user_type(name)
    except discord.errors.Forbidden:
        await client.send_message(message.channel, "Tämä komento vaatii botille oikeudet lisätä reaktioita.")
        return
    if not acc_type:
        return
    # if name in list(data): Tarkistaa käyttäjän tyypin ja antaa lisätä, jos uusi on dmm, seasonal tai tournament
    data[name] = {"previous_names": []}
    with open(f"{path}Tracked_players.json", "w") as data_file:
        json.dump(data, data_file, indent=4)
    await hae_highscoret(message, name.split(), client, acc_type=acc_type, initial_stats=True)


async def change_name(message, hakusanat, client):
    tiedosto = f"{path}Tracked_players.json"
    nimet = " ".join(hakusanat).replace(", ", ",")

    async def confirm_change(vanha, uusi):
        bot_message = await client.send_message(message.channel, "Haluatko varmasti vaihtaa nimen {} -> {}?"
                                                .format(vanha, uusi))
        await client.add_reaction(bot_message, "✅")
        await client.add_reaction(bot_message, "❌")
        answer = await client.wait_for_reaction(emoji=["✅", "❌"], message=bot_message, user=message.author, timeout=5)
        if not answer:
            await client.edit_message(bot_message, "Ei vastausta. Toiminto peruutetaan.")
            return
        elif answer.reaction.emoji == "✅":
            await client.edit_message(bot_message, "Nimi vaihdettu!")
            return True
        elif answer.reaction.emoji == "❌":
            await client.edit_message(bot_message, "Toiminto peruutettu.")
            return

    if "," not in nimet:
        await client.send_message(message.channel, "Erota vanha ja uusi nimi pilkulla.")
        return
    nimet = nimet.split(",")
    old_name = nimet[0]
    new_name = nimet[1]
    old_name = old_name.lower()
    new_name = new_name.lower()
    with open(tiedosto) as data_file:
        data = json.load(data_file)
    if new_name in list(data):
        await client.send_message(message.channel, "Käyttäjän uusi nimi on jo listalla.")
    elif old_name in list(data):
        check_name = requests.get("http://services.runescape.com/m=hiscore_oldschool/index_lite.ws?player={}"
                                  .format(new_name)).text
        if "404 - Page not found" in check_name:
            await client.send_message(message.channel, "Uusi käyttäjänimi ei ole käytössä.")
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
                                  "Käyttäjän vanhaa nimeä ei ole seurannassa. Uusille nimille käytä suoraan komentoa "
                                  "`!track`. Jos vanha nimi on mielestäsi jo seurannassa, ota yhteyttä botin "
                                  "ylläpitäjään.")


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

    await client.send_message(message.channel, f"Viimeisimmät uutiset liittyen Osrs:ään ({article_type}):\n\n"
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
        await client.send_message(message.channel, "Komennon viestin täytyy alkaa ja päättyä lainausmerkillä. "
                                                   "Anna ensin komento ja sitten viesti. Älä anna mitään muuta "
                                                   "viestissäsi.")
        return
    try:
        if command in list(data[server]):
            old_message = data[server][command]["message"]
            if viesti_edited != old_message:
                data[server][command]["message"] = viesti_edited
            else:
                await client.send_message(message.channel, "Uusi viesti ei voi olla sama kuin aiemmin.")
                return
        else:
            await client.send_message(message.channel, "Antamaasi komentoa ei ole olemassa.")
            return
    except KeyError:
        await client.send_message(message.channel, "Serverille ei ole asetettu serverikohtaisia komentoja.")
        return
    with open(file, "w") as data_file:
        json.dump(data, data_file, indent=4)
    await client.send_message(message.channel, "Muokattiin komentoa `{}`.".format(to_utf8(command)))


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
        footnote = "Käyttäjä täytyy laittaa seurantaan, jos kaikki vanhat nimimerkit halutaan tallentaa."
        if previous_name == "-4":
            await client.send_message(message.channel, "CML:n api on tällä hetkellä poissa käytöstä eikä käyttäjä ole "
                                                       "seurannassa, joten nimiä ei löydy.")
            return
        elif previous_name == "-1":
            await client.send_message(message.channel, "Käyttäjänimi ei ole käytössä tai sitä ei ole päivitetty "
                                                       "kertaakaan CML:ssä.")
            return
        else:
            msg = discord.Embed(title="Vanha nimi käyttäjälle {}".format(search), description=previous_name) \
                .set_footer(text=footnote)
            await client.send_message(message.channel, embed=msg)
        return
    if previous_name != "-1" and previous_name != "-4" and previous_name not in old_nicks:
        old_nicks.append(previous_name)
        data[search]["previous_names"] = old_nicks
        with open(f"{path}Tracked_players.json", "w") as data_file:
            json.dump(data, data_file, indent=4)
    elif previous_name == "-4":
        footnote = "CML:n api on tällä hetkellä poissa käytöstä ja listasta saattaa sen vuoksi puuttua vanha nimi."
    if len(old_nicks) == 0:
        await client.send_message(message.channel, "Käyttäjälle ei löydy vanhoja nimiä.\n\n{}".format(footnote))
        return
    msg = discord.Embed(title=f"Tallennetut vanhat nimet käyttäjälle {search}", description="\n".join(old_nicks)) \
        .set_footer(text=footnote)
    await client.send_message(message.channel, embed=msg)


async def patchnotes(message, client):
    with open(f"{path}changelog.txt", "r", encoding="utf-8") as file:
        changelog = file.read()
    embed = discord.Embed(title="Viimeisimmät päivitykset", description=changelog)
    await client.send_message(message.channel, embed=embed)


async def bot_info(message, client, release_notes=False):
    with open(f"{path}changelog.txt", "r", encoding="utf-8") as file:
        changelog = file.read()
    if release_notes:
        embed = discord.Embed(title="Viimeisimmät päivitykset", description=changelog)
    else:
        appinfo = await client.application_info()
        bot_name = appinfo.name
        bot_owner = appinfo.owner
        last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(f"{path}Main.py")).strftime("%d/%m/%Y")
        embed = discord.Embed(title=bot_name, description=f"Ylläpitäjä: {bot_owner.mention}\n"
                                                          f"Päivitetty: {last_modified}\nLähdekoodi: Python 3.6 "
                                                          f"([Source](https://github.com/Visperi/OsrsHelper))")
        embed.add_field(name="Kiitokset",
                        value="[discord.py](https://github.com/Rapptz/discord.py)\n"
                              "[Crystalmathlabs](http://www.crystalmathlabs.com/tracker/) (ttm, nicks, ehp)\n"
                              "[Old school runescape](http://oldschool.runescape.com/) (koko peli, statsit, hinnat)\n"
                              "[OSRS Wiki](https://oldschool.runescape.wiki) (wiki, clue komennot)")
        embed.add_field(name="Viimeisimmät päivitykset", value=changelog)
        embed.set_thumbnail(url=appinfo.icon_url)
    await client.send_message(message.channel, embed=embed)
    kayttokerrat("info")


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
            await client.add_reaction(message, "\N{THUMBS UP SIGN}")
        elif not unsub:
            if server_roles[sub_role] in user_roles:
                return
            await client.add_roles(message.author, server_roles[sub_role])
        await client.add_reaction(message, "\N{THUMBS UP SIGN}")
    except KeyError:
        await client.send_message(message.channel, "Serverillä ei ole roolia Streams.")
    except discord.errors.Forbidden:
        await client.send_message(message.channel, "Roolillani ei ole oikeuksia hallinnoida rooleja tai reagoida "
                                                   "viesteihin tällä kanavalla. Rooli täytyy lisätä ja "
                                                   "poistaa manuaalisesti.")
    except AttributeError:
        await client.send_message(message.channel, "Komento ei toimi yksityisviesteissä.")


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
        await client.send_message(message.channel, "Serverillä ei ole yhtään lisättyä streameria.")
        return
    for streamer in streamers_list:
        display_name = streamer_display_name(streamer)
        username = streamers_list[streamer]["username"]
        stream_link = streamers_list[streamer]["stream_link"]
        final_list.append(f"- {display_name} ({username}) [Stream link]({stream_link})")
    embed = discord.Embed(title=f"Listatut streamerit serverillä {message.server.name}",
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
        await client.send_message(message.channel, "Anna ensin dropin antavan kohteen nimi (jos sellainen on) ja "
                                                   "dropin itemin nimi, sitten droprate. "
                                                   "Erota kaikki toisistaan pilkulla")
        return
    except IndexError:
        return
    with open(f"{path}droprates.json") as data_file:
        data = json.load(data_file)
    try:
        if itemname in data[dropper]:
            await client.send_message(message.channel, "Kyseiselle itemille on jo droprate annetulle kohteelle.")
            return
    except KeyError:
        data[dropper] = {}

    if droprate > 1:
        droprate = Fraction(1, droprate)
    data[dropper][itemname] = str(droprate)

    with open(f"{path}droprates.json", "w") as data_file:
        json.dump(data, data_file, indent=4)
    await client.send_message(message.channel, f"Lisättiin droprate tiedostoon:\n\n**Kohde**: {dropper}\n"
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
        await client.send_message(message.channel, "Tappojen määrä täytyy olla kokonaisluku. Anna ensin tapot ja "
                                                   "sitten kohteen nimi.")
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
        await client.send_message(message.channel, "Antamallasi nimellä ei löytynyt yhtään bossia.")
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
    await client.send_message(message.channel, f"Todennäköisyydet saada droppeja {amount} tapolla "
                                               f"bossilta {boss_name.capitalize()}\n\n{drop_chances_joined}")


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
                await client.send_message(message.channel, "Kohteelle ei ole tallennettu kyseisen itemin dropratea.")
                return
        else:
            await client.send_message(message.channel, "Kohteelle ei ole tallennettu yhtään dropratea.")
            return
        with open(f"{path}droprates.json", "w") as data_file:
            json.dump(data, data_file, indent=4)
        await client.send_message(message.channel, f"Poistettiin kohteelta {target} droprate {itemname}.")
    elif len(keywords) == 1:
        try:
            if keywords[0].capitalize() in data["Misc"]:
                del data["Misc"][keywords[0].capitalize()]
                with open(f"{path}droprates.json", "w") as data_file:
                    json.dump(data, data_file, indent=4)
                await client.send_message(message.channel, f"Poistettiin droprate {keywords[0].capitalize()}.")
                return
        except KeyError:
            await client.send_message(message.channel, "Itemille ei ole dropratea tai unohdit antaa myös kohteen, "
                                                       "joka droppaa itemiä.")
            return
        await client.send_message(message.channel, "Kokonaisten kategorioiden poisto ei ole vielä käytössä. Voit "
                                                   "poistaa yksittäisiä droprateja jonkin tietyn kohteen alta.")


async def test_connection(message, keywords, client):
    site = keywords[0]
    if site == "wiki":
        link = "https://oldschool.runescape.wiki/"
    elif site == "osrs" or site == "runescape":
        link = "http://services.runescape.com/m=hiscore_oldschool/index_lite.ws?player=visperi"
    elif site == "cml" or site == "crystalmathlabs":
        link = "https://crystalmathlabs.com/tracker/api.php?type=ttm&player=visperi"
    else:
        sites = "\n".join(["wiki", "osrs", "cml"])
        await client.send_message(message.channel, f"Tuntematon sivu. Vaihtoehdot ovat:\n\n{sites}")
        return

    try:
        request = requests.get(link, timeout=5)
    except requests.exceptions.ReadTimeout:
        await client.send_message(message.channel, "Sivu vastaa liian hitaasti.")
        return
    status = str(request.status_code)
    if status[0] == "2":
        info_string = "Sivu ottaa vastaan pyyntöjä, käsittelee ne ja vastaa normaalisti."
    elif status[0] == "4":
        info_string = "Botin antama pyyntö on virheellinen."
    elif status[0] == "5":
        info_string = "Sivu ei vastaa pyyntöihin normaalisti."
    else:
        info_string = "Tuntematon vastaus. Voit tarkistaa koodin itse esim. " \
                      "[Wikipediasta](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes), " \
                      "kunnes se lisätään bottiin."
    embed = discord.Embed(title=f"Status code: {status}", description=f"{info_string}\n"
                                f"Yhteys testattiin [tällä]({link}) linkillä.")
    await client.send_message(message.channel, embed=embed)


async def satokausi(message, hakusanat, client):
    kuukaudet = ["tammikuu", "helmikuu", "maaliskuu", "huhtikuu", "toukokuu", "kesäkuu", "heinäkuu", "elokuu",
                 "syyskuu", "lokakuu", "marraskuu", "joulukuu"]
    if len(hakusanat) == 0:
        kuukausi = int(datetime.datetime.now().strftime("%m"))
        kuukausi_str = kuukaudet[kuukausi - 1]
    else:
        try:
            kuukausi_str = hakusanat[0]
            kuukausi = str(kuukaudet.index(kuukausi_str) + 1)
        except ValueError:
            await client.send_message(message.channel, "Anna kuukautta hakiessa sen nimi kirjoitettuna.")
            return
    with open(f"{path}satokaudet.json", encoding="utf-8-sig") as data_file:
        data = json.load(data_file)
    kotimaiset = sorted(data[str(kuukausi)]["kotimaiset"])
    ulkomaiset = sorted(data[str(kuukausi)]["ulkomaiset"])
    embed = discord.Embed(title=f"Satokaudet {kuukausi_str}lle")\
        .add_field(name="Kotimaiset", value="\n".join(kotimaiset))\
        .add_field(name="Ulkomaiset", value="\n".join(ulkomaiset))
    await client.send_message(message.channel, embed=embed)


async def satokaudet(message, hakusanat, client):
    kuukaudet = ["tammikuu", "helmikuu", "maaliskuu", "huhtikuu", "toukokuu", "kesäkuu", "heinäkuu", "elokuu",
                 "syyskuu", "lokakuu", "marraskuu", "joulukuu"]
    search = " ".join(hakusanat)
    kotimaisena = []
    ulkomaisena = []
    with open(f"{path}satokaudet.json", encoding="utf-8-sig") as data_file:
        data = json.load(data_file)

    for month in data:
        month_name = kuukaudet[int(month) - 1]
        if search in data[month]["kotimaiset"]:
            kotimaisena.append(month_name)
        if search in data[month]["ulkomaiset"]:
            ulkomaisena.append(month_name)

    if not kotimaisena and not ulkomaisena:
        await client.send_message(message.channel, "Antamallesi hakusanalle ei löytynyt satokausia.")
        return

    embed = discord.Embed(title=f"Satokaudet {search}lle")
    if kotimaisena:
        embed.add_field(name="Kotimaisena", value="\n".join(kotimaisena))
    if ulkomaisena:
        embed.add_field(name="Ulkomaisena", value="\n".join(ulkomaisena))
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
            await client.send_message(message.channel, "Haullasi ei löytynyt yhtään itemiä. Untradeable itemit eivät "
                                                       "tue avainsanojen käyttöä.")
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
                    footer = "Itemin statseja ei saatu haettua. Tämä johtuu todennäköisesti siitä, että siitä on " \
                             "useampi eri versio ja ne täytyy lisätä manuaalisesti."
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
        await client.send_message(message.channel, "Haullasi löytyi untradeable item jolle ei löydy statseja ja "
                                                   "muodostettava upote olisi täysin tyhjä.")
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
        await client.send_message(message.channel, "Haullasi ei löytynyt yhtään itemiä.")
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
        await client.send_message(message.channel, "Kertoimessa oli tuntematon merkki. Kerroin tukee ainoastaan "
                                                   "lyhenteitä `k` ja `m`.")
        return
    try:
        resp = requests.get(api_link, timeout=4).text
    except requests.exceptions.ReadTimeout:
        await client.send_message(message.channel, "Old School Runescapen api vastaa liian hitaasti. Kokeile myöhemmin "
                                                   "uudelleen.")
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
        pcs = f"({multiplier} kpl)"
        price_ea = f" ({price_latest} ea)"
    else:
        pcs = ""
        price_ea = ""

    embed = discord.Embed(title=f"{itemname} {pcs}")\
        .add_field(name="Viimeisin hinta", value=f"{latest_total} gp{price_ea}", inline=False)\
        .add_field(name="Hinnanmuutokset", value=f"Kuukaudessa: {pc_month} gp\n"
                                                 f"Viikossa: {pc_week} gp\nPäivässä: {pc_day} gp", inline=False)\
        .set_footer(text=f"Viimeisin hinta ajalta {datetime.datetime.utcfromtimestamp(int(latest_ts) / 1e3)} UTC")
    await client.send_message(message.channel, embed=embed)


async def korona_stats(message, client):
    utc_tz = pytz.utc
    helsinki_tz = pytz.timezone("Europe/Helsinki")
    # Get the latest Finnish corona data
    korona_link = "https://w3qa5ydb4l.execute-api.eu-west-1.amazonaws.com/prod/finnishCoronaData"
    try:
        resp = requests.get(korona_link, timeout=5)
    except requests.exceptions.ReadTimeout:
        await client.send_message(message.channel, "Datalähde vastaa liian hitaasti. Kokeile myöhemmin uudelleen.")
        return
    if not resp.ok:
        await client.send_message(message.channel, f"Datalähde vastasi statuskoodilla {resp.status_code}. Kokeile "
                                                   f"myöhemmin uudelleen.")
        return
    new_data = json.loads(resp.text, encoding="utf-8")

    with open("korona.json", "r") as data_file:
        saved_data = json.load(data_file)

    updated_data = {"confirmed": {}, "deaths": {}, "recovered": {}}

    for header in updated_data.keys():
        current_cases = len(new_data[header])
        try:
            latest_case = new_data[header][-1]["date"]
            updated_data[header]["latest"] = latest_case
            updated_data[header]["healthCareDistrict"] = new_data[header][-1]["healthCareDistrict"]
        except IndexError:
            pass

        updated_data[header]["cases"] = current_cases

    now = datetime.datetime.now(tz=utc_tz)
    updated_data["lastUpdated"] = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    embed = discord.Embed(title="Koronan tilanne Suomessa")

    for header in updated_data.keys():
        if header == "confirmed":
            title = "Tartunnat"
        elif header == "deaths":
            title = "Menehtyneet"
        elif header == "recovered":
            title = "Parantuneet"
        else:
            continue

        current_cases = updated_data[header]["cases"]
        cases_diff = current_cases - saved_data[header]["cases"]
        if cases_diff != 0:
            cases_diff_str = "({0:+})".format(cases_diff)
        else:
            cases_diff_str = ""

        try:
            latest_strp = datetime.datetime.strptime(updated_data[header]["latest"], "%Y-%m-%dT%H:%M:%S.%fZ")
            latest_localized = utc_tz.localize(latest_strp).astimezone(helsinki_tz)
            latest_formatted = latest_localized.strftime("%d.%m.%Y %H:%M")
            area = updated_data[header]["healthCareDistrict"]
            if area is None:
                area = "Ei tietoa"
            info_str = f"{current_cases} {cases_diff_str}\nViimeisin: {latest_formatted}\nAlue: {area}"
        except KeyError:
            info_str = current_cases

        embed.add_field(name=title, value=info_str, inline=False)

    embed.set_footer(text="Muutokset ovat päiväkohtaisia")
    await client.send_message(message.channel, embed=embed)

    new_compare_time = datetime.datetime.strptime(updated_data["lastUpdated"], "%Y-%m-%dT%H:%M:%S.%fZ")
    saved_compare_time = datetime.datetime.strptime(saved_data["lastUpdated"], "%Y-%m-%dT%H:%M:%S.%fZ")

    if new_compare_time.day > saved_compare_time.day:
        with open("korona.json", "w", encoding="utf-8") as output_file:
            json.dump(updated_data, output_file, indent=4, ensure_ascii=False)


async def add_drinks(message, client):
    user_id = message.author.id
    server_id = message.server.id

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


async def drink_highscores(message, client):
    server_id = message.server.id

    with open("drinks.json", "r") as data_file:
        drink_data = json.load(data_file)

    try:
        server_data = drink_data[server_id]
    except KeyError:
        await client.send_message(message.channel, "Serverillä ei ole otettu vielä kertaakaan olutta "
                                                   "<:feelsbad:333731708405022721>")
        return

    sorted_scores = sorted(server_data, key=server_data.get, reverse=True)
    highscores = []

    for pos, user_id in enumerate(sorted_scores):
        if pos > 4:
            break

        user = message.server.get_member(user_id)

        if pos == 0:
            pos = "\N{FIRST PLACE MEDAL}"
        elif pos == 1:
            pos = "\N{SECOND PLACE MEDAL}"
        elif pos == 2:
            pos = "\N{THIRD PLACE MEDAL}"
        else:
            pos = f"{pos + 1}."

        highscores.append(f"{pos} {user.display_name} ({server_data[user_id]})")

    embed = discord.Embed(title="Serverin kovimmat kaljankittaajat", description="\n".join(highscores))

    await client.send_message(message.channel, embed=embed)

if __name__ == "__main__":
    print("Tätä moduulia ei ole tarkoitettu ajettavaksi itsessään. Suorita Kehittajaversio.py tai Main.py")
    print("Suljetaan...")
    exit()
