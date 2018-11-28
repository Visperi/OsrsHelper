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

import discord
import datetime
import os
import configparser
import Komennot as komennot
import Settings as settings
import Komennot_en as komennot_en
import dev_commands
import json


client = discord.Client()
path = "{}/".format(os.path.dirname(__file__))
if path == "/":
    path = ""
config = configparser.ConfigParser()
config.read("{}settings.ini".format(path))


@client.event
async def on_ready():
    await client.change_presence(game=discord.Game(name="Say !help"))
    print('Logged in as:')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.event
async def on_message(message):
    msg_lower = message.content.lower()
    msg_raw = message.content
    keywords_lower = msg_lower.split()[1:]
    keywords_raw = str(message.content).split()[1:]
    highscoret = msg_lower.startswith("!stats ") or msg_lower.startswith("!ironstats ") or \
                 msg_lower.startswith("!uimstats ") or msg_lower.startswith("!dmmstats ") or \
                 msg_lower.startswith("!seasonstats ") or msg_lower.startswith("!hcstats ") or \
                 msg_lower.startswith("!tournamentstats ")
    time = datetime.datetime.now()
    moduuli = komennot

    async def get_language():
        # Get user specific language. Make a new entry if it doesnt exist
        try:
            language = config["LANGUAGE"][str(message.author.id)]
        except KeyError:
            language = await settings.get_settings(message, client, get_servlang=True)
            try:
                config["LANGUAGE"][str(message.author.id)] = language
            except TypeError:
                return
            with open("{}settings.ini".format(path), "w") as configfile:
                config.write(configfile)
            language = config["LANGUAGE"][str(message.author.id)]
        # Check if server has a forced language on
        force_lang = await settings.get_settings(message, client, get_forcelang=True)
        if force_lang != "false" and force_lang is not None:
            language = force_lang
        return language

    if message.author != client.user:
        user_lang = await get_language()
        if not user_lang and str(message.author.id) != "95532930620719104":
            print("No user language defined! User: {} Time: {}".format(str(message.author), time))
            return
        if user_lang == "english":
            moduuli = komennot_en
        if msg_lower.startswith("!price "):
            await moduuli.current_price(message, client)
        elif msg_lower == "!commands":
            await moduuli.commands(message, client)
        elif msg_lower == "!helo":
            await client.send_message(message.channel, "Paikalla ollaan.")
        elif msg_lower == "!patch":
            await moduuli.bot_info(message, client, release_notes=True)
        elif msg_lower.startswith("!wiki "):
            await moduuli.search_wiki(message, keywords_lower, client)
        elif msg_lower.startswith("!cipher "):
            await moduuli.get_cipher(message, keywords_lower, client)
        elif msg_lower.startswith("!puzzle "):
            await moduuli.hae_puzzle(message, keywords_lower, client)
        elif highscoret:
            await moduuli.hae_highscoret(message, keywords_lower, client)
        elif msg_lower.startswith("!ttm "):
            await moduuli.time_to_max(message, keywords_lower, client)
        elif msg_lower.startswith("!anagram "):
            await moduuli.hae_anagram(message, keywords_lower, client)
        elif msg_lower.startswith("!keys "):
            await moduuli.get_keys(message, keywords_lower, client)
        elif msg_lower == "!howlong":
            await moduuli.kayttajan_tiedot(message, client)
        elif msg_lower.startswith("!xp ") or msg_lower.startswith("!exp ") or msg_lower.startswith("!lvl ") or \
                msg_lower.startswith("!level "):
            await moduuli.experiencelaskuri(message, keywords_lower, client)
        elif msg_lower.startswith("!calc "):
            await moduuli.laskin(message, keywords_lower, client)
        elif msg_lower.startswith("!ehp ") or msg_lower.startswith("!ironehp ") or \
                msg_lower.startswith("!skillerehp ") or msg_lower.startswith("!f2pehp"):
            await moduuli.ehp_rates(message, keywords_lower, client)
        elif msg_lower == "!info" or msg_lower == "!version":
            await moduuli.bot_info(message, client)
        elif msg_lower == "!chatcommands" or msg_lower == "!server commands" or msg_lower == "!custom commands":
            await moduuli.get_custom_commands(message, client)
        elif msg_lower.startswith("!cryptic "):
            await moduuli.cryptic(message, keywords_lower, client)
        elif msg_lower.startswith("!map") or msg_lower.startswith("!maps") or msg_lower == "!maps":
            await moduuli.mapit(message, client)
        elif msg_lower.startswith("!limit "):
            await moduuli.get_buylimit(message, keywords_lower, client)
        elif msg_lower.startswith("!help"):
            await moduuli.function_help(message, keywords_lower, client)
        elif msg_lower.startswith("!gains"):
            await moduuli.gains_calculator(message, keywords_lower, client)
        elif msg_lower.startswith("!pricechange ") or msg_lower.startswith("!pc "):
            await moduuli.hinnanmuutos(message, client)
        elif msg_lower.startswith("!track "):
            await moduuli.track_user(message, keywords_lower, client)
        elif msg_lower.startswith("!namechange "):
            await moduuli.change_name(message, keywords_lower, client)
        elif msg_lower.startswith("!nicks "):
            await moduuli.get_old_nicks(message, keywords_lower, client)
        elif msg_lower == "!update":
            await moduuli.latest_update(message, client)
        elif msg_lower == "!sub streams":
            await moduuli.sub_to_role(message, client)
        elif msg_lower == "!unsub streams":
            await moduuli.sub_to_role(message, client, unsub=True)
        elif msg_lower == "!streamers":
            await moduuli.get_streamers(message, client)
        elif msg_lower.startswith("!drop ") or msg_lower.startswith("!loot "):
            await moduuli.loot_chance(message, keywords_lower, client)
        elif msg_lower.startswith("!test ") or msg_lower.startswith("!connection "):
            await moduuli.test_connection(message, keywords_lower, client)
        elif msg_lower.startswith("!prices"):
            await moduuli.hinnat(message, client)

        elif msg_lower.startswith("%addkey "):
            permissions = await high_permissions(message, user_lang)
            if permissions:
                await moduuli.addkey(message, keywords_lower, client)
        elif msg_lower.startswith("%delkey "):
            permissions = await high_permissions(message, user_lang)
            if permissions:
                await moduuli.delkey(message, keywords_lower, client)
        elif msg_lower.startswith("%addcom"):
            permissions = await high_permissions(message, user_lang)
            if not permissions:
                return
            add_commands = await settings.get_settings(message, user_lang, client, get_addcom=True)
            if not add_commands:
                if user_lang == "finnish":
                    await client.send_message(message.channel,
                                              "Serverin omistaja on asettanut komentojen lisäyksen pois "
                                              "päältä.")
                else:
                    await client.send_message(message.channel,
                                              "Adding commands has been set off by the server owner.")
            elif permissions and add_commands:
                await moduuli.addcom(message, keywords_raw, client)
        elif msg_lower.startswith("%editcom"):
            permissions = await high_permissions(message, user_lang)
            if permissions:
                await moduuli.editcom(message, keywords_raw, client)
        elif msg_lower.startswith("%delcom "):
            permissions = await high_permissions(message, user_lang)
            if permissions:
                await moduuli.delcom(message, keywords_raw, client)
        elif msg_lower.startswith("%addloot ") or msg_lower.startswith("%adddrop"):
            permissions = await high_permissions(message, user_lang)
            if permissions:
                await moduuli.add_droprate(message, keywords_lower, client)
        elif msg_lower.startswith("%delloot "):
            permissions = await high_permissions(message, user_lang)
            if permissions:
                await moduuli.delete_droprate(message, keywords_lower, client)

        elif msg_lower.startswith("&language ") or msg_lower.startswith("&lang "):
            await settings.change_language(message, keywords_lower, user_lang, client)
            config.read("{}settings.ini".format(path))
        elif msg_lower == "&settings":
            await settings.get_settings(message, client)
        elif msg_lower.startswith("&permit "):
            permissions = await high_permissions(message, user_lang, server_owner=True)
            if permissions:
                await settings.add_permissions(message, keywords_raw, user_lang, client)
        elif msg_lower.startswith("&unpermit "):
            permissions = await high_permissions(message, user_lang, server_owner=True)
            if permissions:
                await settings.remove_permissions(message, keywords_raw, user_lang, client)
        elif msg_lower.startswith("&add commands"):
            permissions = await high_permissions(message, user_lang, server_owner=True)
            if permissions:
                await settings.set_addcom(message, keywords_lower[1:], user_lang, client)
        elif msg_lower.startswith("&forcelang "):
            permissions = await  high_permissions(message, user_lang, server_owner=True)
            if permissions:
                await settings.set_forcelanguage(message, keywords_lower, user_lang, client)
        elif msg_lower.startswith("&defaultlang ") or msg_lower.startswith("&defaultlanguage"):
            permissions = await high_permissions(message, user_lang, server_owner=True)
            if permissions:
                await settings.set_default_language(message, keywords_lower, user_lang, client)

        elif msg_lower.startswith("§id "):
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.get_item_id(message, keywords_lower, client)
        elif msg_lower.startswith("§addpuzzle "):
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.add_puzzle(message, keywords_lower, client)
        elif msg_lower.startswith("§addobject "):
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.add_object(message, keywords_lower, client)
        elif msg_lower.startswith("§delobject "):
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.delete_object(message, keywords_lower, client)
        elif msg_lower == "§commands":
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.dev_commands(message, client)
        elif msg_lower == "§timesused" or msg_lower == "§times used":
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.get_times_used(message, client)
        elif msg_lower.startswith("§add alch") or msg_lower.startswith("§addalch"):
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.add_halch(message, keywords_lower, client)
        elif msg_lower.startswith("§addstream "):
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.add_stream(message, keywords_lower, client)
        elif msg_lower.startswith("§delete stream ") or msg_lower.startswith("§delstream "):
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.remove_stream(message, keywords_lower, client)
        elif msg_lower.startswith("§addlim "):
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.add_limit(message, keywords_lower, client)
        elif msg_lower.startswith("§dellim "):
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.delete_limit(message, keywords_lower, client)
        elif msg_lower.startswith("§addobjects "):
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.add_objects(message, msg_raw, client)
        elif msg_lower.startswith("§check"):
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.check_new_items(message, client)
        elif msg_lower.startswith("§get "):
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.get_file(message, keywords_raw, client)
        else:
            if msg_lower.startswith("!") and msg_lower != "!":
                await komennot.execute_custom_commands(message, msg_raw, client)


async def high_permissions(message, user_lang, sysadmin=False, server_owner=False):
    appinfo = await client.application_info()
    bot_owner = appinfo.owner
    try:
        guild_owner = message.server.owner
    except AttributeError:
        await client.send_message(message.channel, "Oikeuksia vaativat komennot eivät toimi yksityisviesteissä.")
        return
    try:
        if sysadmin:
            if message.author == bot_owner:
                return True
            else:
                if user_lang == "finnish":
                    await client.send_message(message.channel, "Vain botin omistaja voi suorittaa tämän komennon.")
                else:
                    await client.send_message(message.channel, "Only the  bot owner can run this command.")
                return
        elif server_owner:
            if (message.author == guild_owner) or (message.author == bot_owner):
                return True
            else:
                if user_lang == "finnish":
                    await client.send_message(message.channel, "Vain serverin ja botin omistaja voivat suorittaa tämän "
                                                               "komennon.")
                else:
                    await client.send_message(message.channel, "Only the server owner and bot owner can run this "
                                                               "command.")
                return

        permitted_roles = await settings.get_settings(message, client, get_roles=True)
        member_top_role = str(message.author.top_role)
        if (message.author == bot_owner) or (member_top_role in permitted_roles) or (message.author == guild_owner):
            return True
        else:
            if user_lang == "finnish":
                await client.send_message(message.channel, "Käyttäjällä täytyy olla korkeampien oikeuksien rooli tämän"
                                                           " komennon suorittamiseen.")
            else:
                await client.send_message(message.channel, "User needs to have a permitted role to execute this "
                                                           "command.")
            return
    except AttributeError:
        if user_lang == "finnish":
            await client.send_message(message.channel, "Toiminto ei ole käytössä yksityisviesteissä.")
        else:
            await client.send_message(message.channel, "This command can't be used in direct messages.")
        return


@client.event
async def on_member_remove(member):
    settings.clear_user_ini(member.id)
    with open(f"{path}streamers.json") as data_file:
        data = json.load(data_file)
    if member.id in data[member.server.id]:
        data[member.server.id].pop(member.id)
        if len(data[member.server.id]) == 0:
            data.pop(member.server.id)
        with open(f"{path}streamers.json", "w") as data_file:
            json.dump(data, data_file, indent=4)


@client.event
async def on_member_join(member):
    mestarit_id = settings.get_credential("server_id", "mestarit")
    test_server_id = settings.get_credential("server_id", "test_server_id")
    server_id = str(member.server.id)
    if server_id == mestarit_id or server_id == test_server_id:
        await client.send_message(member.server,
                                  f"Tervetuloa {member.mention} ! Jos olet tilaaja Teukan striimissä, saat "
                                  f"yhdistämällä käyttäjäsi Twitchiin myös tänne roolin. Botin komennot saat "
                                  f"komennolla `!commands` ja apua komennolla `!help`")


@client.event
async def on_member_update(before, after):
    try:
        if after.game.type == 1:
            try:
                if before.game.type == 1:
                    return
            except AttributeError:
                pass
            with open(f"{path}streamers.json") as data_file:
                data = json.load(data_file)
            try:
                if str(after.id) in data[after.server.id]:
                    stream_link = data[after.server.id][after.id]["stream_link"]
                    streams_role = discord.utils.get(after.server.roles, name="Streams")
                    await client.send_message(after.server, f"{streams_role.mention} "
                                                            f"{after.display_name} live\n"
                                                            f"{stream_link}")
            except KeyError:
                return
    except AttributeError:
        return


if __name__ == "__main__":
    token = settings.get_credential("tokens", "osrshelper")
    client.run(token)
