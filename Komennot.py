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
import covid19_data
from dateutil.relativedelta import relativedelta
import asyncio
import pytz
import numpy as np
import static_functions


async def command_help(message, keywords, client):
    command = " ".join(keywords).replace("!", "").replace("%", "").replace("&", "")
    if not command:
        msg = "`!info`: Perustietoa botista ja viimeisimmät päivitykset\n" \
              "`!commands`: Lista kaikista käytettävissä olevista komennoista\n" \
              "`!server commands`: Lista kaikista tämän serverin omista komennoista\n" \
              "`!help <komennon nimi>`: Käyttöohjeet yksittäiselle komennolle"
        await client.send_message(message.channel, msg)
        return
    with open("Data files/Help.json", encoding="utf-8") as data_file:
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
    utc_tz = pytz.utc
    fin_tz = pytz.timezone("Europe/Helsinki")

    try:
        avatar_url = message.author.avatar_url
        display_name = message.author.display_name

        created_at = utc_tz.localize(message.author.created_at).astimezone(fin_tz)
        created_at = created_at.strftime("%d.%m.%Y %H:%M:%S")
        joined_at = utc_tz.localize(message.author.joined_at).astimezone(fin_tz)
        joined_at = joined_at.strftime("%d.%m.%Y %H:%M:%S")

        roles = [str(role) for role in message.author.roles if str(role) != "@everyone"]

    except AttributeError:
        await client.send_message(message.channel, "Komento ei toimi yksityisviesteissä.")
        return

    user_info = discord.Embed().set_author(name=display_name).set_thumbnail(url=avatar_url) \
        .add_field(name="Username", value=str(message.author)) \
        .add_field(name="Id", value=message.author.id) \
        .add_field(name="Käyttäjä luotu", value=created_at) \
        .add_field(name="Liittyi serverille", value=joined_at) \
        .add_field(name="Roolit tällä serverillä", value=", ".join(roles))
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

    embed = discord.Embed()
    embed.set_footer(text="Jos tarvitset apua komentojen käytössä, käytä komentoa !help <komento>")

    for category in commands_dict.keys():
        category_commands = [command for command in commands_dict[category]]
        embed.add_field(name=category, value="\n".join(category_commands))

    await client.send_message(message.channel, embed=embed)


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
        await client.send_message(message.channel, "Antamaasi itemiä ei löytynyt.")
        return
    if len(new_keys) == 0 or new_keys[0] == "":
        await client.send_message(message.channel, "Itemille täytyy antaa vähintään yksi uusi avainsana.")
        return
    if itemname not in data.keys():
        data[itemname.lower()] = []
    for key in new_keys:
        key = static_functions.to_ascii(key)
        if "*" in key:
            discarded_keys += 1
            continue
        elif key not in data["all nicks"] and key not in all_tradeables.keys():
            data["all nicks"].append(key)
            data[itemname.lower()].append(key)
            approved_keys.append(static_functions.to_utf8(key))
    if discarded_keys > 0:
        denied_msg = f"{discarded_keys} avaimista hylättiin, koska ne sisälsi kertomerkkejä. Lisätietoa saat " \
            f"komennolla `!help addkey`"
    if len(approved_keys) == 0:
        await client.send_message(message.channel, f"Kaikki antamasi avainsanat ovat varattuja. {denied_msg}")
        return
    else:
        with open("Data files/Item_keywords.json", "w") as data_file:
            json.dump(data, data_file, indent=4)
            await client.send_message(message.channel, "Lisättiin seuraavat avainsanat itemille {}: `{}`. {}"
                                      .format(itemname, ", ".join(approved_keys), denied_msg))
    kayttokerrat("Addkey")


async def delkey(message, keywords, client):
    file = "Data files/Item_keywords.json"
    keywords = " ".join(keywords).replace(", ", ",").split(",")
    itemname = keywords[0]
    deletelist = keywords[1:]
    deleted_keys = []
    item_info = static_functions.get_iteminfo(itemname, default_names=True)
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
        keyword = static_functions.to_ascii(keyword)
        if keyword in item_keys:
            delete_keys.append(keyword)
    if len(delete_keys) == 0:
        await client.send_message(message.channel, "Yhtäkään antamistasi avainsanoista ei ole asetettu tälle itemille.")
        return
    for key in delete_keys:
        data[itemname].remove(key)
        data["all nicks"].remove(key)
        deleted_keys.append(static_functions.to_utf8(key))
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
    iteminfo = static_functions.get_iteminfo(itemname, default_names=True)
    if not iteminfo:
        await client.send_message(message.channel, "Haullasi ei löytynyt yhtään itemiä.")
        return
    with open("Data files/Item_keywords.json") as data_file:
        data = json.load(data_file)
    try:
        nicks_ascii = data[itemname]
        for nick in nicks_ascii:
            nicks_utf8.append(static_functions.to_utf8(nick))
        embed = discord.Embed(title=f"Avainsanat itemille {itemname.capitalize()}", description="\n".join(nicks_utf8))
        await client.send_message(message.channel, embed=embed)
    except KeyError:
        await client.send_message(message.channel, "Tavaralle ei ole asetettu avainsanoja.")


async def search_wiki(message, hakusanat: list, client, get_html=False):
    baselink = "https://oldschool.runescape.wiki/w/"

    search = "_".join(hakusanat)
    search_link = baselink + search
    try:
        response = await static_functions.make_request(client.aiohttp_session, search_link)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Wiki vastasi liian hitaasti. Kokeile myöhemmin uudelleen.")
        return
    if f"This page doesn&#039;t exist on the wiki. Maybe it should?" in response:
        if get_html:
            return TypeError
        hyperlinks = []
        truesearch_link = f"https://oldschool.runescape.wiki/w/Special:Search?search={search}"
        try:
            truesearch_resp = await static_functions.make_request(client.aiohttp_session, truesearch_link)
        except asyncio.TimeoutError:
            await client.send_message(message.channel, "Wiki vastasi liian hitaasti. Kokeile myöhemmin uudelleen.")
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
            await client.send_message(message.channel, "Haullasi löytyi {} anagrammia:\n{}\n\nKokeile tarkentaa "
                                                       "hakuasi.".format(matches, "\n".join(partial_matches)))
        elif matches > 10:
            await client.send_message(message.channel, "Haullasi löytyi yli 10 anagrammia. Kokeile tarkentaa hakuasi.")
        else:
            await client.send_message(message.channel, "Haullasi ei löytynyt yhtään anagrammia.")


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
    file = f"Data files/{filename}"

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

    with open(f"Data files/Custom_commands.json") as data_file:
        data = json.load(data_file)
    try:
        viesti = data[server]["!{}".format(static_functions.to_ascii(command))]["message"]
    except KeyError:
        return
    await client.send_message(message.channel, static_functions.to_utf8(viesti))
    kayttokerrat("custom")


async def addcom(message, words_raw, client):
    words = " ".join(words_raw)
    file = f"Data files/Custom_commands.json"
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
        viesti_raw = static_functions.to_ascii(string[start:end]).replace("\\n", "\n")
        komento_raw = static_functions.to_ascii(" ".join(string[:start - 8].split(" ")[0:]))
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
            raise

    try:
        command, viesti, command_raw = convert(words)
        if len(command_raw) > 30:
            raise
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
    await client.send_message(message.channel, "Komento `{}` lisätty.".format(static_functions.to_utf8(command)))
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
    with open("Data files/Custom_commands.json") as data_file:
        data = json.load(data_file)
    custom_commands_raw = list(data[server])
    if len(custom_commands_raw) == 0:
        await client.send_message(message.channel, "Serverillä ei ole yhtään komentoa.")
        return
    for command in custom_commands_raw:
        custom_commands.append(static_functions.to_utf8(command))
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
    file = f"Data files/Custom_commands.json"
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
            await client.send_message(message.channel, "Komento `{}` poistettu."
                                      .format(static_functions.to_utf8(komento)))
            kayttokerrat("delcom")
    else:
        await client.send_message(message.channel, "Komentoa ei ole olemassa.")


async def get_buylimit(message, keywords, client):
    """
    Gives a four hour Grand Exchange limit for an item if there is any
    """
    keyword = " ".join(keywords)
    iteminfo = static_functions.get_iteminfo(keyword)
    if not iteminfo:
        await client.send_message(message.channel, "Haullasi ei löytynyt yhtään itemiä.")
        return
    else:
        itemname = iteminfo[0]
    with open("Data files/Buy_limits.json") as data_file:
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
        try:
            url = f"http://services.runescape.com/m=hiscore_oldschool/index_lite.ws?player={new_name}"
            check_name = await static_functions.make_request(client.aiohttp_session, url)
        except asyncio.TimeoutError:
            await client.send_message(message.channel, "Osrs:n API vastasi liian hitaasti. Kokeile myöhemmin "
                                                       "uudelleen.")
            return

        if "404 - Page not found" in check_name:
            await client.send_message(message.channel, "Uutta käyttäjänimeä ei löytynyt pelistä.")
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
                                  "Käyttäjän vanhaa nimeä ei ole seurannassa. Uusille nimille käytä suoraan komentoa "
                                  "`!track`. Jos vanha nimi on mielestäsi jo seurannassa, ota yhteyttä botin "
                                  "ylläpitäjään.")


async def latest_update(message, client):
    news_articles = {}
    articles = []

    link = "http://oldschool.runescape.com/"
    try:
        osrs_response = await static_functions.make_request(client.aiohttp_session, link)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Osrs:n etusivu vastasi liian hitaasti. Kokeile myöhemmin "
                                                   "uudelleen.")
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
        viesti_raw = static_functions.to_ascii(string[start:end]).replace("\\n", "\n")
        komento = static_functions.to_ascii(" ".join(string[:start - 8].split(" ")[0:])).replace("!", "")
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
    await client.send_message(message.channel, "Muokattiin komentoa `{}`.".format(static_functions.to_utf8(command)))


async def get_old_nicks(message, hakusanat, client):
    search = " ".join(hakusanat)
    with open("Data files/Tracked_players.json") as data_file:
        data = json.load(data_file)
    try:
        old_nicks = data[search]["previous_names"]
    except KeyError:
        await client.send_message(message.channel, "Käyttäjä ei ole seurannassa.")
        return
    if len(old_nicks) == 0:
        await client.send_message(message.channel, "Käyttäjälle ei löydy vanhoja nimiä.")
        return
    embed = discord.Embed(title=f"Tallennetut vanhat nimet käyttäjälle {search}", description="\n".join(old_nicks))
    await client.send_message(message.channel, embed=embed)


async def patchnotes(message, client):
    with open("Data files/changelog.txt", "r", encoding="utf-8") as file:
        changelog = file.read()
    embed = discord.Embed(title="Viimeisimmät päivitykset", description=changelog)
    await client.send_message(message.channel, embed=embed)


async def bot_info(message, client, release_notes=False):
    with open("Data files/changelog.txt", "r", encoding="utf-8") as file:
        changelog = file.read()
    if release_notes:
        embed = discord.Embed(title="Viimeisimmät päivitykset", description=changelog)
    else:
        appinfo = await client.application_info()
        bot_name = appinfo.name
        bot_owner = appinfo.owner
        last_modified = datetime.datetime.fromtimestamp(os.path.getmtime("Main.py")).strftime("%d/%m/%Y")
        created_at = client.user.created_at.replace(microsecond=0)
        embed = discord.Embed(title=bot_name, description=f"Kehittäjä: {bot_owner}\n"
                                                          f"Päivitetty: {last_modified}\n"
                                                          f"Lähdekoodi: Python 3.6 "
                                                          f"([Source](https://github.com/Visperi/OsrsHelper))\n"
                                                          f"Luotu: {created_at} UTC")
        embed.add_field(name="Kolmannen osapuolen lähteet",
                        value="[discord.py](https://github.com/Rapptz/discord.py) (Lähdekoodi)\n"
                              "[Crystalmathlabs](http://www.crystalmathlabs.com/tracker/) (EHP ratet)\n"
                              "[Old school runescape](http://oldschool.runescape.com/) (Highscoret, G.E. hinnat, "
                              "peliuutiset)\n"
                              "[OSRS Wiki](https://oldschool.runescape.wiki) (Wiki)", inline=False)
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

    with open("Data files/streamers.json") as data_file:
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
    with open("Data files/droprates.json") as data_file:
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

    with open("Data files/droprates.json", "w") as data_file:
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

    with open("Data files/droprates.json") as rates_file:
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
    with open(f"Data files/droprates.json") as data_file:
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
        with open(f"Data files/droprates.json", "w") as data_file:
            json.dump(data, data_file, indent=4)
        await client.send_message(message.channel, f"Poistettiin kohteelta {target} droprate {itemname}.")
    elif len(keywords) == 1:
        try:
            if keywords[0].capitalize() in data["Misc"]:
                del data["Misc"][keywords[0].capitalize()]
                with open("Data files/droprates.json", "w") as data_file:
                    json.dump(data, data_file, indent=4)
                await client.send_message(message.channel, f"Poistettiin droprate {keywords[0].capitalize()}.")
                return
        except KeyError:
            await client.send_message(message.channel, "Itemille ei ole dropratea tai unohdit antaa myös kohteen, "
                                                       "joka droppaa itemiä.")
            return
        await client.send_message(message.channel, "Kokonaisten kategorioiden poisto ei ole vielä käytössä. Voit "
                                                   "poistaa yksittäisiä droprateja jonkin tietyn kohteen alta.")


async def satokausi(message, hakusanat, client):
    """
    A command function for getting list of fruits and vegetables that currently are in their harvest season
    (I dont currently know better translation). This command is currently exclusive to Finnish and thus does not appear
    in English module.

    :param message: Message that invoked this command
    :param hakusanat: Message content as a list
    :param client: Bot client responsible of all work between code and Discord client
    """

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
    with open("Data files/satokaudet.json", encoding="utf-8-sig") as data_file:
        data = json.load(data_file)
    kotimaiset = sorted(data[str(kuukausi)]["kotimaiset"])
    ulkomaiset = sorted(data[str(kuukausi)]["ulkomaiset"])
    embed = discord.Embed(title=f"Satokaudet {kuukausi_str}lle")\
        .add_field(name="Kotimaiset", value="\n".join(kotimaiset))\
        .add_field(name="Ulkomaiset", value="\n".join(ulkomaiset))
    await client.send_message(message.channel, embed=embed)


async def satokaudet(message, hakusanat, client):
    """
    A command function for searching when a given plant is in its harvest season. This command is currently exclusive
    to Finnish and thus does not appear in English module.

    :param message: Message that invoked this command
    :param hakusanat: Message content as a list
    :param client: Bot client that is responsible of all work between code and Discord client
    """

    kuukaudet = ["tammikuu", "helmikuu", "maaliskuu", "huhtikuu", "toukokuu", "kesäkuu", "heinäkuu", "elokuu",
                 "syyskuu", "lokakuu", "marraskuu", "joulukuu"]
    search = " ".join(hakusanat)
    kotimaisena = []
    ulkomaisena = []
    with open("Data files/satokaudet.json", encoding="utf-8-sig") as data_file:
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

    with open("Data files/itemstats.json") as data_file:
        data = json.load(data_file)
    try:
        itemname, item_id = static_functions.get_iteminfo(" ".join(hakusanat))
        tradeable = True
        if itemname in ignore_list:
            raise
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
                geapi_resp = await static_functions.make_request(client.aiohttp_session, link)
            except asyncio.TimeoutError:
                await client.send_message(message.channel, "Osrs:n API vastasi liian hitaasti eikä itemin tietoja "
                                                           "saatu haettua.")
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
            with open("Data files/itemstats.json", "w") as data_file:
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

    search = " ".join(hakusanat).replace(" * ", "*").split("*")
    try:
        itemname, itemid = static_functions.get_iteminfo(search[0])
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
        resp = await static_functions.make_request(client.aiohttp_session, api_link)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Old School Runescapen API vastasi liian hitaasti. Kokeile "
                                                   "myöhemmin uudelleen.")
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
    embed.add_field(name="Viimeisin hinta", value=f"{latest_price_total} gp{price_ea}", inline=False)
    embed.add_field(name="Hinnanmuutokset", value=f"Kuukaudessa: {pc_month} gp\n"
                                                  f"Viikossa: {pc_week} gp\n"
                                                  f"Päivässä: {pc_day} gp", inline=False)
    embed.set_footer(text=f"Viimeisin hinta ajalta {datetime.datetime.utcfromtimestamp(int(latest_ts) / 1e3)} UTC")
    await client.send_message(message.channel, embed=embed)


async def korona_stats(message, client) -> None:
    """
    A command function for getting current status of covid19 (coronavirus) in Finland. This command is currently
    exclusive to Finnish and thus does not appear in English module.

    :param message: Message that invoked this command
    :param client: Bot client responsible of all work in between code and Discord client
    """

    cooldown = 3  # Data update cooldown in minutes
    utc_now = datetime.datetime.utcnow()
    corona_file = "Data files/korona.json"

    embed = discord.Embed(title="Koronan tilanne Suomessa")
    embed.set_thumbnail(url="https://i.imgur.com/lQ5ecBe.png")

    try:
        update_timedelta = utc_now - covid19_data.previous_request
        update_timedelta = update_timedelta.total_seconds() / 60
    except TypeError:
        update_timedelta = cooldown

    if update_timedelta >= cooldown:
        try:
            data = await covid19_data.async_get_updated_data(client.aiohttp_session, covid19_data.hs,
                                                             output_file=corona_file, indent=4)
            covid19_data.previous_request = utc_now
        except (asyncio.TimeoutError, RuntimeError) as error:
            if isinstance(error, asyncio.TimeoutError):
                embed.set_footer(text="Näytetään tallennettua dataa, koska datalähde vastasi liian hitaasti")
            elif isinstance(error, RuntimeError):
                embed.set_footer(text="Näytetään tallennettua dataa, koska datalähde vastasi virhekoodilla")
            data = covid19_data.read_datafile(corona_file)
    else:
        data = covid19_data.read_datafile(corona_file)

    all_daily_cases = covid19_data.get_daily_cases(data, localize_to="Europe/Helsinki")
    latest_cases = covid19_data.get_latest_cases(data, localize_to="Europe/Helsinki",
                                                 localized_datefmt="%d.%m.%Y %H:%M")

    if embed.footer.EmbedProxy == discord.Embed.Empty:
        synch_ts = covid19_data.previous_request
        synch_ts = covid19_data.localize_timestamp(synch_ts, "Europe/Helsinki", new_datefmt="%d.%m.%Y %H:%M:%S")
        embed.set_footer(text=f"Data synkronoitu viimeksi: {synch_ts}")

    for case_type in ["confirmed", "deaths", "recovered"]:
        total_cases = len(data[case_type])
        daily_cases = len(all_daily_cases[case_type])
        latest_date = latest_cases[case_type]["date"]
        latest_area = latest_cases[case_type]["healthCareDistrict"]

        if daily_cases != 0:
            daily_cases = f"(+{daily_cases})"
        else:
            daily_cases = ""

        if case_type == "confirmed":
            title = "Tartunnat"
        elif case_type == "deaths":
            title = "Menehtyneet"
            if not latest_area:
                latest_area = latest_cases["deaths"]["area"]
        else:
            title = "Parantuneet"

        if not latest_area:
            latest_area = "Ei tietoa"

        if case_type == "confirmed":
            in_ward = latest_cases["hospitalised"]["inWard"]
            in_icu = latest_cases["hospitalised"]["inIcu"]
            total_hospitalised = latest_cases["hospitalised"]["totalHospitalised"]

            embed.add_field(name=title, value=f"{total_cases} {daily_cases}\nViimeisin: {latest_date}\n"
                                              f"Alue: {latest_area}")
            embed.add_field(name="Hoitoa vaativat", value=f"Osastohoidossa: {in_ward}\nTehohoidossa: {in_icu}\n"
                                                          f"Yhteensä: {total_hospitalised}")
        else:
            embed.add_field(name=title, value=f"{total_cases} {daily_cases}\nViimeisin: {latest_date}\n"
                                              f"Alue: {latest_area}", inline=False)

    await client.send_message(message.channel, embed=embed)


async def add_drinks(message, client) -> None:
    user_id = message.author.id
    try:
        server_id = message.server.id
    except AttributeError:
        await client.send_message(message.channel, "Tämä komento ei tue yksityisviestejä.")
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
        await client.send_message(message.channel, f"{message.author.display_name} saavutti {user_drinks} annoksen "
                                                   f"rajapyykin <a:blobbeers:693529052371222618>")
    elif mod100 == 0:
        await client.send_message(message.channel, f"\U0001F973 {message.author.display_name} saavutti "
                                                   f"{user_drinks} annoksen rajapyykin! \U0001F973")


async def drink_highscores(message, client) -> None:
    try:
        server_id = message.server.id
    except AttributeError:
        await client.send_message(message.channel, "Tämä Komento ei tue yksityisviestejä.")
        return

    with open("Data files/drinks.json", "r") as data_file:
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
        if pos > 9:
            break

        try:
            member = message.server.get_member(user_id)
            display_name = member.display_name
        except AttributeError:
            display_name = "Tuntematon"

        if pos == 0:
            pos = "\N{FIRST PLACE MEDAL}"
        elif pos == 1:
            pos = "\N{SECOND PLACE MEDAL}"
        elif pos == 2:
            pos = "\N{THIRD PLACE MEDAL}"
        else:
            pos = f"{pos + 1}."

        highscores.append(f"{pos} {display_name} ({server_data[user_id]})")

    embed = discord.Embed(title="Serverin kovimmat kaljankittaajat", description="\n".join(highscores))

    await client.send_message(message.channel, embed=embed)


async def remove_drinks(message, client) -> None:
    user_id = message.author.id
    try:
        server_id = message.server.id
    except AttributeError:
        await client.send_message(message.channel, "Tämä komento ei tue yksityisviestejä.")
        return

    with open("Data files/drinks.json", "r") as data_file:
        drink_data = json.load(data_file)

    try:
        server_data = drink_data[server_id]
    except KeyError:
        await client.send_message(message.channel, "Serverillä ei ole juomia mitä poistaa.")
        return

    try:
        server_data[user_id] -= 1
    except KeyError:
        await client.send_message(message.channel, "Sinulla ei ole yhtään juotua juomaa.")
        return

    if server_data[user_id] == 0:
        del server_data[user_id]
        if len(server_data) == 0:
            del drink_data[server_id]

    with open("Data files/drinks.json", "w") as output_file:
        json.dump(drink_data, output_file, indent=4)

    await client.add_reaction(message, "a:emiTreeB:693788789042184243")


async def add_reminder(message, client, hakusanat) -> None:
    min_secs = 10
    reminder_file = "Data files/reminders.json"
    ts_now = datetime.datetime.utcnow().replace(microsecond=0)
    user_string = " ".join(hakusanat)

    i1, i2 = user_string.find("\""), user_string.rfind("\"")
    if i1 == i2:
        await client.send_message(message.channel, "Anna viesti lainausmerkkien sisällä.")
        return
    elif i1 < 1:
        await client.send_message(message.channel, "Anna myös ajastimelle aika.")
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
        reminder_time = relativedelta(minutes=int(time_string))
    except ValueError:
        try:
            reminder_time = static_functions.string_to_timedelta(time_string)
        except ValueError:
            await client.send_message(message.channel, "Annettu aika ei ollut tuetussa muodossa.")
            return

    # Convert the reminder time from relativedelta to datetime.datetime object so total seconds can be extracted
    reminder_time = ((ts_now + reminder_time) - ts_now)
    if reminder_time.total_seconds() < min_secs:
        await client.send_message(message.channel, f"Annetun ajan täytyy olla vähintään {min_secs} sekuntia.")
        return

    with open(reminder_file) as data_file:
        reminder_data = json.load(data_file)

    try:
        trigger_time = ts_now + reminder_time
        localized_trigger_time = covid19_data.localize_timestamp(trigger_time, "Europe/Helsinki",
                                                                 new_datefmt="%Y-%m-%d %H:%M:%S")
        trigger_time = str(ts_now + reminder_time)
    except OverflowError:
        await client.send_message(message.channel, "Liian iso ajastus :(")
        return
    try:
        ts_reminders = reminder_data[trigger_time]
    except KeyError:
        reminder_data[trigger_time] = []
        ts_reminders = reminder_data[trigger_time]

    ts_reminders.append({"channel": message.channel.id, f"message": reminder_message, "author": message.author.id})
    with open(reminder_file, "w") as data_file:
        json.dump(reminder_data, data_file, indent=4, ensure_ascii=False)

    await client.send_message(message.channel, f"Asetettiin muistutus ajankohdalle {localized_trigger_time}")


async def get_user_stats(message: discord.Message, keywords: str, client: discord.Client) -> None:
    """
    A command function for getting current hiscores of given username. Hiscore type can be specified with giving more
    specific command invokation to get more accurate rankings (All users are always in default normal hiscores too).
    These user stats are then send in a nice tabulate table.

    :param message: Message that invoked this command
    :param keywords: Message content as a string
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
        user_stats = await static_functions.get_hiscore_data(username, client.aiohttp_session, acc_type=account_type)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Osrs:n API vastasi liian hitaasti. Yritä myöhemmin uudelleen.")
        return
    except TypeError:
        await client.send_message(message.channel, "Annetulla käyttäjätyypillä ei löytynyt käyttäjänimelle dataa.")
        return
    except ValueError:
        await client.send_message(message.channel, "Käyttäjänimien maksimipituus on 12 merkkiä.")
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
        await client.send_message(message.channel, "Antamasi käyttäjä ei ole seurannassa.")
        return

    account_type = saved_data["account_type"]
    saved_stats = saved_data["past_stats"]
    saved_ts = datetime.datetime.fromtimestamp(saved_data["saved"])

    try:
        new_stats = await static_functions.get_hiscore_data(username, client.aiohttp_session, acc_type=account_type)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Osrs:n API vastasi liian hitaasti. Yritä myöhemmin uudelleen.")
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

    # Overwrite saved user data if argument -noupdate was used
    if update is True:
        saved_data["past_stats"] = new_stats
        saved_data["saved"] = int(datetime.datetime.utcnow().replace(microsecond=0, second=0).timestamp())

        with open("Data files/statsdb.json", "w") as output_file:
            json.dump(data, output_file, indent=4)

    await client.send_message(message.channel, scoretable)


async def track_username(message: discord.Message, keywords: list, client: discord.Client) -> None:
    """
    A command function that adds an username and its current info into a json file. Progress for this user can be then
    calculated just by using command !gains <username>

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
        await client.send_message(message.channel, "Käyttäjä on jo seurannassa.")
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

    acc_type_embed = discord.Embed(title=f"Mikä on käyttäjän {username} tyyppi?", description="\n".join(type_options))
    acc_type_embed.set_footer(text=f"Reaktiosi tallennetaan vasta kaikkien {len(reactions)} reaktion latauduttua!")
    acc_type_query = await client.send_message(message.channel, embed=acc_type_embed)

    for reaction in reactions:
        await client.add_reaction(acc_type_query, reaction)

    acc_type_answer = await client.wait_for_reaction(emoji=reactions, user=message.author, timeout=8,
                                                     message=acc_type_query)
    # Embed that is used to edit previous embed when command finishes, exceptions or not
    finish_embed = discord.Embed()
    if not acc_type_answer:
        finish_embed.title = "Ei vastausta. Toiminto peruutettu."
        await client.edit_message(acc_type_query, embed=finish_embed)
        return

    answer_reaction_idx = reactions.index(acc_type_answer.reaction.emoji)
    if answer_reaction_idx == len(reactions) - 1:
        finish_embed.title = "Toiminto peruutettu."
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
        getting_stats_embed = discord.Embed(title=f"Haetaan statseja käyttäjälle {username}...")
        await client.edit_message(acc_type_query, embed=getting_stats_embed)
        initial_stats = await static_functions.get_hiscore_data(username, client.aiohttp_session, account_type)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "Osrs:n API vastasi liian hitaasti eikä käyttäjää voitu laittaa"
                                                   " seurantaan. Kokeile myöhemmin uudelleen.")
        return
    except TypeError:
        finish_embed.title = f"Käyttäjänimelle {username} ei löytynyt hiscoreja käyttäjätyypillä {account_type_formal}."
        await client.edit_message(acc_type_query, embed=finish_embed)
        return
    except ValueError as e:
        if e.args[0].startswith("Username"):
            finish_embed.title = "Yli 12 merkkiä pitkiä käyttäjänimiä ei voi olla käytössä."
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

    finish_embed.title = f"Asetettiin käyttäjä {username} seurantaan. Käyttäjätyyppi: {account_type_formal}"
    await client.edit_message(acc_type_query, embed=finish_embed)


async def get_boss_stats(message: discord.Message, keywords: list, client: discord.Client):
    """
    A draft command that can't currently be used, but boss scores have been asked for a long time.
    """

    username = " ".join(keywords)

    # Parse (optional) account type

    user_stats = await static_functions.get_hiscore_data(username, client.aiohttp_session)

    boss_data = user_stats[35:]
    boss_names = ["Abyssal Sire", "Alchemical Hydra", "Barrows Chests", "Bryophyta", "Callisto", "Cerberus",
                  "Chambers of Xeric", "Chambers of Xeric: Challenge Mode", "Chaos Elemental", "Chaos Fanatic",
                  "Commander Zilyana", "Corporeal Beast", "Crazy Archaeologist", "Dagannoth Prime", "Dagannoth Rex",
                  "Dagannoth Supreme", "Deranged Archaeologist", "General Graardor", "Giant Mole",
                  "Grotesque Guardians", "Hespori", "Kalphite Queen", "King Black Dragon", "Kraken", "Kree'Arra",
                  "K'ril Tsutsaroth", "Mimic", "Nightmare", "Obor", "Sarachnis", "Scorpia", "Skotizo", "The Gauntlet",
                  "The Corrupted Gauntlet", "Theatre of Blood", "Thermonuclear Smoke Devil", "TzKal-Zuk", "TzKal-Jad",
                  "Venenatis", "Vet'ion", "Vorkath", "Wintertodt", "Zalcano", "Zulrah"]


if __name__ == "__main__":
    print("Dont run this module as a independent process as it doesn't do anything. Run Main.py instead.")
    exit()
