"""
MIT License

Copyright (c) 2022 Visperi

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

import static_functions
import json
import discord
import asyncio


async def get_item_id(message, keywords, client):
    """
    Dev command to easily get the name and id of an item
    """
    itemname = " ".join(keywords)
    item_data = await static_functions.get_item_data(itemname)
    if not item_data:
        await client.send_message(message.channel, "Could not find any items.")
        return

    default_itemname = item_data["name"]
    item_id = item_data["id"]

    await client.send_message(message.channel, f"Item name: `{default_itemname}`\nId: `{item_id}`")


async def dev_commands(message, client):
    sysadmin_commands = ["§id", "§times used", "§addstream", "§delstream", "§addlim", "§dellim", "§addobjects",
                         "§check", "§get"]
    viesti = discord.Embed(title="Developer commands", description="\n".join(sysadmin_commands))\
        .set_footer(text="These commands are only for the developer's use")
    await client.send_message(message.channel, embed=viesti)


async def get_times_used(message, client):
    from operator import itemgetter
    from tabulate import tabulate
    commands_list = []

    with open("Data files/Times_used.json") as data_file:
        data = json.load(data_file)
    dates = "{} - {}".format(data["date_start"], data["date_now"])
    data.pop("date_start"), data.pop("date_now")
    all_uses = sum(list(data.values()))
    data_sorted = sorted(data.items(), key=itemgetter(1), reverse=True)
    for command in data_sorted:
        uses = command[1]
        uses_percentage = (uses / all_uses) * 100
        rpercentage = round(uses_percentage, 1)
        if rpercentage == 0.0 and uses_percentage > 0:
            rpercentage = "< 0.1"
        commands_list.append([f"{command[0]}: {command[1]}", f"[{rpercentage}%]"])
    table = "{}\n\n{}\n\nTotal: {}".format(dates, tabulate(commands_list, tablefmt="plain"), all_uses)
    await client.send_message(message.channel, f"```{table}```")


async def add_stream(message, keywords, client):
    streamers_file = "Data files/streamers.json"
    streamer = discord.utils.get(message.server.members, id=keywords[-1])
    try:
        stream_link = keywords[-2].replace("<", "").replace(">", "")
    except IndexError:
        await client.send_message(message.channel, "Please give a link to the stream too. Link first, then id.")
        return
    if not streamer:
        await client.send_message(message.channel, "Couldn't find any users with given id.")
        return
    streamer_id = streamer.id
    display_name = streamer.display_name
    streamer_name = f"{streamer.name}#{streamer.discriminator}"

    with open(streamers_file) as data_file:
        data = json.load(data_file)

    try:
        streamers_list = data[message.server.id]
    except KeyError:
        data[message.server.id] = {}
        streamers_list = data[message.server.id]
    if streamer_id in streamers_list:
        await client.send_message(message.channel, "This streamer already is in the streamers list.")
        return
    streamers_list[streamer_id] = {"stream_link": stream_link, "username": streamer_name}

    with open(streamers_file, "w") as data_file:
        json.dump(data, data_file, indent=4)
    await client.send_message(message.channel, f"Successfully added {display_name} to streamers list\n"
                                               f"Id: {streamer_id}\n"
                                               f"Link: <{stream_link}>")


async def remove_stream(message, keywords, client):
    streamers_file = "Data files/streamers.json"
    streamer = discord.utils.get(message.server.members, id=keywords[-1])
    if not streamer:
        await client.send_message(message.channel, "Couldn't find any users with given id.")
        return
    streamer_id, display_name = streamer.id, streamer.display_name

    with open(streamers_file) as data_file:
        data = json.load(data_file)

    try:
        streamers_list = data[message.server.id]
    except KeyError:
        await client.send_message(message.channel, "This server doesn't have any streamers in the list yet.")
        return
    try:
        streamers_list.pop(streamer_id)
    except ValueError:
        await client.send_message(message.channel, "Given user is not in the list for this server.")
        return
    if len(streamers_list) == 0:
        data.pop(message.server.id)

    with open(streamers_file, "w") as data_file:
        json.dump(data, data_file, indent=4)
    await client.send_message(message.channel, f"Successfully removed streamer {streamer_id} ({display_name}) from "
                                               f"streamers list.")


async def check_new_items(message, client):
    tradeables_file = "Data files/Tradeables.json"
    url = "https://prices.runescape.wiki/api/v1/osrs/mapping"

    try:
        resp = await static_functions.make_request(client.aiohttp_session, url)
    except asyncio.TimeoutError:
        await client.send_message(message.channel, "RsBuddy answered too slowly.")
        return

    resp_data = json.loads(resp)
    new_items = []

    with open(tradeables_file, "r") as data_file:
        saved_data = json.load(data_file)

    for item in resp_data:
        item_id = item["id"]
        item_name = item["name"]
        members = item["members"]
        store_price = item["value"]
        examine = item["examine"]

        if item_name not in saved_data.keys():
            try:
                limit = item["limit"]
                saved_data[item_name] = dict(id=item_id, members=members, store_price=store_price, buy_limit=limit,
                                             examine=examine)
            except KeyError:
                saved_data[item_name] = dict(id=item_id, members=members, store_price=store_price, examine=examine)
            new_items.append(item_name)

    added_items_msg = "No new items to add."
    if len(new_items) > 0:
        with open(tradeables_file, "w") as data_file:
            json.dump(saved_data, data_file, indent=4)

        added_items_msg = "Added {} new items:\n\n{}".format(len(new_items), "\n".join(new_items))
        if len(added_items_msg) > 2000:
            added_items_msg += f"Added {len(new_items)} new items but they can't fit into one Discord message."

    await client.send_message(message.channel, added_items_msg)


async def get_file(message, keywords, client):
    filename = " ".join(keywords)
    filepath = f"Data files/{filename}"
    try:
        await client.send_file(message.channel, filepath)
    except FileNotFoundError:
        await client.send_message(message.channel, "File not found.")
        return
    except discord.errors.Forbidden:
        await client.send_message(message.channel, "My role doesn't have permission to send files.")
        return


async def manage_drinks(message, keywords, client):
    try:
        server_id = message.server.id
    except AttributeError:
        await client.send_message(message.channel, "This command doesn't support direct messages.")
        return

    action = keywords[0]
    target_user_id = keywords[1]
    try:
        member_obj = message.server.get_member(target_user_id)
        target_display_name = member_obj.display_name
    except AttributeError:
        target_display_name = target_user_id

    if action == "reset" and len(keywords) != 2:
        await client.send_message(message.channel, f"Invalid amount of parameters. Got {len(keywords)} but expected 2.")
        return
    elif len(keywords) != 3 and action != "reset":
        await client.send_message(message.channel, f"Invalid amount of parameters. Got {len(keywords)} but expected 3.")
        return

    with open("Data files/drinks.json", "r") as drinks_file:
        drinks_data = json.load(drinks_file)

    try:
        server_drinks = drinks_data[server_id]
    except KeyError:
        await client.send_message(message.channel, "This server doesn't have any drinks yet.")
        return
    if action == "reset":
        del server_drinks[target_user_id]
        if len(server_drinks) == 0:
            del drinks_data[server_id]
        success_str = f"Succesfully reset drinks for {target_display_name}."
    else:
        try:
            amount = int(keywords[2])
        except ValueError:
            await client.send_message(message.channel, "Third parameter was not convertible to an integer.")
            return
        try:
            target_user_drinks = server_drinks[target_user_id]
        except KeyError:
            await client.send_message(message.channel, "Target doesn't have any drinks yet.")
            return

        if action == "remove":
            target_user_drinks -= amount
        elif action == "add":
            target_user_drinks += amount
        elif action == "set":
            target_user_drinks = amount
        else:
            await client.send_message(message.channel, "Unknown operation.")
            return

        server_drinks[target_user_id] = target_user_drinks
        success_str = f"Succesfully modified drinks for {target_display_name}. They now have " \
                      f"{target_user_drinks} drinks."

    with open("Data files/drinks.json", "w") as output_file:
        json.dump(drinks_data, output_file, indent=4)

    await client.send_message(message.channel, success_str)


async def clear_cache(message, keywords, client):
    cache_name = " ".join(keywords)

    if cache_name == "melvoridle" or cache_name == "mwiki":
        cache = client.mwiki_cache
    elif cache_name == "osrs" or cache_name == "wiki":
        cache = client.wiki_cache
    else:
        await client.send_message(message.channel, "Unknown cache name.")
        return

    cache_items = len(cache)
    if cache_items == 0:
        await client.send_message(message.channel, "The cache is already empty.")
        return

    cache.clear()
    await client.send_message(message.channel, f"Cleared {cache.name} cache.\nCleared entries: {cache_items}")


if __name__ == '__main__':
    print("Dont run this module as a independent process as it doesn't do anything. Run Main.py instead.")
