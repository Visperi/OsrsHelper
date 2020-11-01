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

# OsrsHelper v8.4
# coding=utf-8

import discord
import datetime
import configparser
import Commands
import Settings
import Commands_en
import dev_commands
import json
import asyncio
import dateutil.parser
import aiohttp
from caching import Cache

client = discord.Client()
config = configparser.ConfigParser()
config.read("Data files/settings.ini")


@client.event
async def on_ready():
    await client.change_presence(game=discord.Game(name="Say !help"))

    if not client.on_ready_called:
        print("Logged in as:")
        print(client.user.name)
        print(client.user.id)
        print("------")

        # on_ready is not guaranteed to execute only once so a check is needed to guarantee only one reminder loop
        if not client.reminder_loop_running:
            await start_reminder_loop()

        client.on_ready_called = True


@client.event
async def on_message(message):
    msg_lower = message.content.lower()
    msg_raw = message.content
    keywords_lower = msg_lower.split()[1:]
    keywords_raw = str(message.content).split()[1:]
    highscoret = msg_lower.startswith("!stats ") or msg_lower.startswith("!ironstats ") or \
                 msg_lower.startswith("!uimstats ") or msg_lower.startswith("!dmmstats ") or \
                 msg_lower.startswith("!seasonstats ") or msg_lower.startswith("!hcstats ") or \
                 msg_lower.startswith("!tournamentstats ") or msg_lower.startswith("!lstats") or \
                 msg_lower.startswith("!leaguestats ")
    boss_hiscores = msg_lower.startswith("!kc ") or msg_lower.startswith("!ironkc ") or \
                    msg_lower.startswith("!uimkc ") or msg_lower.startswith("!dmmkc ") or \
                    msg_lower.startswith("!seasonkc ") or msg_lower.startswith("!hckc ") or \
                    msg_lower.startswith("!tournamentkc ") or msg_lower.startswith("!lkc ") or \
                    msg_lower.startswith("!leaguekc ")
    time = datetime.datetime.now()
    moduuli = Commands

    async def get_language():
        # Get user specific language. Make a new entry if it doesnt exist
        try:
            language = config["LANGUAGE"][str(message.author.id)]
        except KeyError:
            language = await Settings.get_settings(message, client, get_servlang=True)
            try:
                config["LANGUAGE"][str(message.author.id)] = language
            except TypeError:
                return
            with open("Data files/settings.ini", "w") as configfile:
                config.write(configfile)
            language = config["LANGUAGE"][str(message.author.id)]
        # Check if server has a forced language on
        force_lang = await Settings.get_settings(message, client, get_forcelang=True)
        if force_lang != "false" and force_lang is not None:
            language = force_lang
        return language

    if message.author != client.user:
        user_lang = await get_language()
        if not user_lang and str(message.author.id) != "95532930620719104":
            print("No user language defined! User: {} Time: {}".format(str(message.author), time))
            return
        if user_lang == "english":
            moduuli = Commands_en
        if msg_lower.startswith("!price "):
            await moduuli.item_price(message, keywords_lower, client)
        elif msg_lower == "!commands":
            await moduuli.commands(message, client)
        elif msg_lower == "!helo":
            await client.send_message(message.channel, "Paikalla ollaan.")
        elif msg_lower == "!patch":
            await moduuli.bot_info(message, client, release_notes=True)
        elif msg_lower.startswith("!cipher "):
            await moduuli.search_cipher(message, keywords_lower, client)
        elif msg_lower.startswith("!puzzle "):
            await moduuli.hae_puzzle(message, keywords_lower, client)
        elif highscoret:
            await moduuli.get_user_stats(message, msg_lower, client)
        elif msg_lower.startswith("!anagram "):
            await moduuli.search_anagram(message, keywords_lower, client)
        elif msg_lower.startswith("!keys ") or msg_lower.startswith("!keywords "):
            await moduuli.get_item_keywords(message, keywords_lower, client)
        elif msg_lower == "!howlong" or msg_lower == "!me":
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
            await moduuli.command_help(message, keywords_lower, client)
        elif msg_lower.startswith("!gains"):
            await moduuli.get_user_gains(message, keywords_lower, client)
        elif msg_lower.startswith("!track "):
            await moduuli.track_username(message, keywords_lower, client)
        elif msg_lower.startswith("!namechange "):
            await moduuli.change_name(message, keywords_lower, client)
        elif msg_lower.startswith("!nicks "):
            await moduuli.get_old_nicks(message, keywords_lower, client)
        elif msg_lower == "!update":
            await moduuli.latest_updates(message, client)
        elif msg_lower == "!sub streams":
            await moduuli.sub_to_role(message, client)
        elif msg_lower == "!unsub streams":
            await moduuli.sub_to_role(message, client, unsub=True)
        elif msg_lower == "!streamers":
            await moduuli.get_streamers(message, client)
        elif msg_lower.startswith("!drop ") or msg_lower.startswith("!loot ") or msg_lower.startswith("!kill "):
            await moduuli.loot_chance(message, keywords_lower, client)
        elif msg_lower.startswith("!satokausi"):
            await Commands.satokausi(message, keywords_lower, client)
        elif msg_lower.startswith("!satokaudet "):
            await Commands.satokaudet(message, keywords_lower, client)
        elif msg_lower == "!korona" or msg_lower == "!corona":
            await Commands.korona_stats(message, client)
        elif msg_lower in ["!beer", "!olut", "!drink"]:
            await moduuli.add_drinks(message, client)
        elif msg_lower in ["!beerscores", "!beers", "!drinks"]:
            await moduuli.drink_highscores(message, client)
        elif msg_lower in ["!unbeer", "!undrink"]:
            await moduuli.remove_drinks(message, client)
        elif msg_lower.startswith("!remindme ") or msg_lower.startswith("!reminder "):
            await moduuli.add_reminder(message, client, keywords_lower)
        elif msg_lower.startswith("!roll"):
            await moduuli.roll_die(message, keywords_lower, client)
        elif msg_lower.startswith("!melvorwiki ") or msg_lower.startswith("!mwiki "):
            await Commands.search_wiki(message, keywords_lower, client.mwiki_cache, client)
        elif msg_lower.startswith("!wiki "):
            await moduuli.search_wiki(message, keywords_lower, client.wiki_cache, client)
        elif boss_hiscores:
            await moduuli.get_boss_scores(message, msg_lower, client)

        elif msg_lower.startswith("%addkey "):
            permissions = await high_permissions(message, user_lang)
            if permissions:
                await moduuli.add_item_keywords(message, keywords_lower, client)
        elif msg_lower.startswith("%delkey "):
            permissions = await high_permissions(message, user_lang)
            if permissions:
                await moduuli.delete_item_keywords(message, keywords_lower, client)
        elif msg_lower.startswith("%addcom"):
            permissions = await high_permissions(message, user_lang)
            if not permissions:
                return
            add_commands = await Settings.get_settings(message, user_lang, client, get_addcom=True)
            if not add_commands:
                if user_lang == "finnish":
                    await client.send_message(message.channel,
                                              "Serverin omistaja on asettanut komentojen lisäyksen pois "
                                              "päältä.")
                else:
                    await client.send_message(message.channel,
                                              "Adding commands has been set off by the server owner.")
            elif permissions and add_commands:
                await moduuli.add_custom_command(message, keywords_raw, client)
        elif msg_lower.startswith("%editcom"):
            permissions = await high_permissions(message, user_lang)
            if permissions:
                await moduuli.edit_custom_command(message, keywords_raw, client)
        elif msg_lower.startswith("%delcom "):
            permissions = await high_permissions(message, user_lang)
            if permissions:
                await moduuli.delete_custom_command(message, keywords_raw, client)
        elif msg_lower.startswith("%addloot ") or msg_lower.startswith("%adddrop"):
            permissions = await high_permissions(message, user_lang)
            if permissions:
                await moduuli.add_droprate(message, keywords_lower, client)
        elif msg_lower.startswith("%delloot "):
            permissions = await high_permissions(message, user_lang)
            if permissions:
                await moduuli.delete_droprate(message, keywords_lower, client)

        elif msg_lower.startswith("&language ") or msg_lower.startswith("&lang "):
            await Settings.change_language(message, keywords_lower, user_lang, client)
            config.read("Data files/settings.ini")
        elif msg_lower == "&settings":
            await Settings.get_settings(message, client)
        elif msg_lower.startswith("&permit "):
            permissions = await high_permissions(message, user_lang, server_owner=True)
            if permissions:
                await Settings.add_permissions(message, keywords_raw, user_lang, client)
        elif msg_lower.startswith("&unpermit "):
            permissions = await high_permissions(message, user_lang, server_owner=True)
            if permissions:
                await Settings.remove_permissions(message, keywords_raw, user_lang, client)
        elif msg_lower.startswith("&add commands"):
            permissions = await high_permissions(message, user_lang, server_owner=True)
            if permissions:
                await Settings.set_addcom(message, keywords_lower[1:], user_lang, client)
        elif msg_lower.startswith("&forcelang "):
            permissions = await  high_permissions(message, user_lang, server_owner=True)
            if permissions:
                await Settings.set_forcelanguage(message, keywords_lower, user_lang, client)
        elif msg_lower.startswith("&defaultlang ") or msg_lower.startswith("&defaultlanguage"):
            permissions = await high_permissions(message, user_lang, server_owner=True)
            if permissions:
                await Settings.set_default_language(message, keywords_lower, user_lang, client)

        elif msg_lower.startswith("§id "):
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.get_item_id(message, keywords_lower, client)
        elif msg_lower == "§commands":
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.dev_commands(message, client)
        elif msg_lower == "§timesused" or msg_lower == "§times used":
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.get_times_used(message, client)
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
        elif msg_lower.startswith("§drinks "):
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.manage_drinks(message, keywords_lower, client)
        elif msg_lower.startswith("§clear "):
            permissions = await high_permissions(message, user_lang, sysadmin=True)
            if permissions:
                await dev_commands.clear_cache(message, keywords_lower, client)
        else:
            if msg_lower.startswith("!") and msg_lower != "!":
                await moduuli.execute_custom_command(message, msg_raw, client)


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

        permitted_roles = await Settings.get_settings(message, client, get_roles=True)
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
    Settings.clear_user_ini(member.id)
    with open("Data files/streamers.json") as data_file:
        data = json.load(data_file)
    if member.id in data[member.server.id]:
        data[member.server.id].pop(member.id)
        if len(data[member.server.id]) == 0:
            data.pop(member.server.id)
        with open("Data files/streamers.json", "w") as data_file:
            json.dump(data, data_file, indent=4)


@client.event
async def on_member_join(member):
    mestarit_id = Settings.get_credential("server_id", "mestarit")
    test_server_id = Settings.get_credential("server_id", "test_server_id")
    server_id = str(member.server.id)
    if server_id == mestarit_id or server_id == test_server_id:
        await client.send_message(member.server,
                                  f"Tervetuloa {member.mention} ! Botin komennot saat komennolla "
                                  f"`!commands` ja apua komennolla `!help`")


@client.event
async def on_member_update(before, after):
    try:
        if after.game.type == 1:
            try:
                if before.game.type == 1:
                    return
            except AttributeError:
                pass
            with open("Data files/streamers.json") as data_file:
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


async def start_reminder_loop():
    reminder_file = "Data files/reminders.json"
    num_deprecated = 0

    with open(reminder_file, "r") as data_file:
        reminder_data = json.load(data_file)

    deprecated_mentions = [ts for ts in reminder_data if dateutil.parser.isoparse(ts) < datetime.datetime.utcnow()]

    for ts in deprecated_mentions:
        num_deprecated += len(reminder_data[ts])
        del reminder_data[ts]

    with open(reminder_file, "w") as output_file:
        json.dump(reminder_data, output_file, indent=4, ensure_ascii=False)

    # Set the state true to prevent multiple reminder loops
    client.reminder_loop_running = True
    print(f"Reminder loop started. Deleted {num_deprecated} deprecated reminders.")

    # Start reminder loop
    while True:
        ts_now = str(datetime.datetime.utcnow().replace(microsecond=0))

        with open(reminder_file, "r") as data_file:
            reminder_data = json.load(data_file)

        try:
            finished_reminders = reminder_data[ts_now]

            for reminder in finished_reminders:
                channel = client.get_channel(reminder["channel"])
                message = reminder["message"]
                author_id = reminder["author"]
                author = channel.server.get_member(author_id)

                await client.send_message(channel, f"{author.mention} {message}")

            del reminder_data[ts_now]

            with open(reminder_file, "w") as output_file:
                json.dump(reminder_data, output_file, indent=4, ensure_ascii=False)

        except KeyError:
            pass

        await asyncio.sleep(1)


if __name__ == "__main__":
    token = Settings.get_credential("tokens", "osrshelper")
    client.aiohttp_session = aiohttp.ClientSession(loop=client.loop)
    client.on_ready_called = False
    client.reminder_loop_running = False
    client.mwiki_cache = Cache("Melvoridle")
    client.wiki_cache = Cache("Osrs")
    client.run(token)
