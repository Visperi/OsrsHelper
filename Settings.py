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

import configparser
import json
import discord

config = configparser.ConfigParser()


def read_config():
    config.read("Data files/settings.ini")


def str2input(string):
    string = string.lower()
    if string in ["finnish", "fin", "fi", "suomi"]:
        string = "finnish"
    elif string in ["english", "eng", "en"]:
        string = "english"
    elif string in ["false", "off"]:
        string = "false"
    elif string in ["true", "on"]:
        string = "true"
    return string


def write_config():
    with open("Data files/settings.ini", "w") as configfile:
        config.write(configfile)
        configfile.close()


async def change_language(message, hakusanat, user_lang, client):
    if len(hakusanat) == 1:
        hakusanat = str2input(hakusanat[0])
        if hakusanat != "english" and hakusanat != "finnish":
            if user_lang == "finnish":
                msg = "Ainoat kielivaihtoehdot ovat suomi ja englanti."
            else:
                msg = "Only available languages are finnish and english."
            await client.send_message(message.channel, msg)
            return

        read_config()
        config.set("LANGUAGE", str(message.author.id), hakusanat)
        write_config()
        if hakusanat == "english":
            msg = f"{message.author.mention} Language set to english."
        else:
            msg = f"{message.author.mention} Asetettiin kieleksi suomi."
        await client.send_message(message.channel, msg)
    else:
        if user_lang == "finnish":
            msg = "Syötä komentoon ainoastaan kieli, johon haluat vaihtaa."
        else:
            msg = "Give only the language you want to change to."
        await client.send_message(message.channel, msg)


async def get_settings(message, client, get_roles=False, get_addcom=False, get_servlang=False,
                       get_forcelang=False):
    read_config()
    server_roles = []
    server_permissions = []
    try:
        settings = config[str(message.server.id)]
    except KeyError:
        settings = config["DEFAULT"]
    except AttributeError:
        return
    permissions = settings["permissions"].split(", ")
    add_commands = settings.getboolean("add_commands")
    force_language = settings["force_language"]
    default_language = settings["default_language"]
    if get_roles:
        return permissions
    elif get_addcom:
        return add_commands
    elif get_servlang:
        return default_language
    elif get_forcelang:
        return force_language
    for role in message.server.roles:
        server_roles.append(str(role))
    for role in permissions:
        if role in server_roles:
            server_permissions.append(role)
    embed = discord.Embed(title=f"Settings for {str(message.server)}",
                           description=f"Permitted roles: {server_permissions}\n"
                                       f"Add commands: {add_commands}\n"
                                       f"Force language: {force_language.capitalize()}\n"
                                       f"Default language: {default_language.capitalize()}")
    await client.send_message(message.channel, embed=embed)


async def set_forcelanguage(message, hakusanat, user_lang, client):
    read_config()
    server_id = str(message.server.id)
    new_setting = str2input(hakusanat[0])
    try:
        current_setting = config[server_id]["force_language"]
    except KeyError:
        config.add_section(server_id)
        current_setting = config[server_id]["force_language"]
    if new_setting == "off":
        new_setting = "false"
    if new_setting == current_setting:
        if user_lang == "finnish":
            msg = "Kyseinen asetus on jo käytössä serverille."
        else:
            msg = "That settings is already in use for this server."
        await client.send_message(message.channel, msg)
        return
    elif new_setting != "english" and new_setting != "finnish" and new_setting != "false":
        if user_lang == "finnish":
            msg = "Ainoat vaihtoehdot pakotetulle kielelle ovat suomi, englanti tai off."
        else:
            msg = "The only options for forced language are finnish, english or off."
        await client.send_message(message.channel, msg)
        return
    config[server_id]["force_language"] = new_setting
    write_config()
    if user_lang == "finnish":
        msg = f"Pakotettu kieli asetettu: {new_setting.capitalize()}."
    else:
        msg = f"Forced language set to {new_setting.capitalize()}."
    await client.send_message(message.channel, msg)


async def set_default_language(message, hakusanat, user_lang, client):
    read_config()
    server_id = str(message.server.id)
    new_setting = str2input(hakusanat[0])
    try:
        current_setting = config[server_id]["default_language"]
    except KeyError:
        config.add_section(server_id)
        current_setting = config[server_id]["default_language"]
    if new_setting == current_setting:
        if user_lang == "finnish":
            msg = "Kyseinen kieli on jo oletuksena tällä serverillä."
        else:
            msg = "This language is already a default in this server."
        await client.send_message(message.channel, msg)
        return
    if new_setting != "english" and new_setting != "finnish" and new_setting != "false":
        if user_lang == "finnish":
            msg = "Ainoat vaihtoehdot oletuskielelle ovat suomi tai englanti"
        else:
            msg = "The only options for default language are finnish or english."
        await client.send_message(message.channel, msg)
        return
    config[server_id]["default_language"] = new_setting
    write_config()
    if user_lang == "finnish":
        msg = "Serverin Oletuskieli vaihdettu kieleen {}.".format(new_setting.capitalize())
    else:
        msg = "Default language for this server set to {}".format(new_setting.capitalize())
    await client.send_message(message.channel, msg)


async def add_permissions(message, words_raw, user_lang, client):
    add = " ".join(words_raw)
    server_id = str(message.server.id)
    server_roles = []
    read_config()
    if add.replace(" ", "") == "":
        if user_lang == "finnish":
            msg = "Lisättävän roolin nimi ei voi olla tyhjää."
        else:
            msg = "Name of the permitted role can't be empty."
        await client.send_message(message.channel, msg)
        return
    for role in message.server.roles:
        server_roles.append(str(role))
    try:
        settings = config[server_id]
        permissions = settings["permissions"].split(", ")
        if add not in server_roles:
            if user_lang == "finnish":
                msg = "Serverillä ei ole antamaasi roolia."
            else:
                msg = "There is no role with that name in this server."
            await client.send_message(message.channel, msg)
            return
        elif add in permissions:
            if user_lang == "finnish":
                msg = "Roolilla {} on jo oikeudet.".format(add)
            else:
                msg = "Role {} is already permitted".format(add)
            await client.send_message(message.channel, msg)
            return
        else:
            permissions.append(add)
        settings["permissions"] = ", ".join(permissions)
    except KeyError:
        permissions = config.get("DEFAULT", "permissions").split(", ")
        permissions.append(add)
        config.add_section(server_id)
        config[server_id]["permissions"] = ", ".join(permissions)
    write_config()
    if user_lang == "finnish":
        msg = "Annettiin oikeudet roolille `{}`.".format(add)
    else:
        msg = "Permitted role `{}`.".format(add)
    await client.send_message(message.channel, msg)


async def remove_permissions(message, words_raw, user_lang, client):
    remove = " ".join(words_raw)
    server_id = str(message.server.id)
    read_config()
    if remove.replace(" ", "") == "":
        if user_lang == "finnish":
            await client.send_message(message.channel, "Poistettavan roolin nimi ei voi olla tyhjää.")
        else:
            await client.send_message(message.channel, "Name of the permitted role can't be empty.")
        return
    default_permissions = config.get("DEFAULT", "permissions").split(", ")
    try:
        settings = config[server_id]
    except KeyError:
        if user_lang == "finnish":
            msg = "Serverillä on oikeudet vain oletusrooleilla, eikä niitä voi poistaa."
        else:
            msg = "Only the default roles are permitted and they can't be removed."
        await client.send_message(message.channel, msg)
        return
    permissions = settings["permissions"].split(", ")
    if remove not in permissions:
        if user_lang == "finnish":
            msg = "Roolille ei ole annettu oikeuksia."
        else:
            msg = "Role is not permitted."
        await client.send_message(message.channel, msg)
        return
    elif remove in default_permissions:
        if user_lang == "finnish":
            msg = "Oikeuksia ei voi poistaa oletuksena olevilta rooleilta."
        else:
            msg = "Permissions can't be removed from default roles."
        await client.send_message(message.channel, msg)
        return
    else:
        permissions.remove(remove)
        settings["permissions"] = ", ".join(permissions)
    write_config()
    if user_lang == "finnish":
        msg = "Poistettiin oikeudet roolilta `{}`.".format(remove)
    else:
        msg = "Removed permissions from role `{}`.".format(remove)
    await client.send_message(message.channel, msg)


async def set_addcom(message, hakusanat, user_lang, client):
    setting = " ".join(hakusanat)
    server_id = str(message.server.id)
    add_commands = await get_settings(message, client, get_addcom=True)
    read_config()
    try:
        settings = config[server_id]
    except KeyError:
        config.add_section(server_id)
        settings = config[server_id]
    if not setting and not add_commands:
        settings["add_commands"] = "true"
    elif not setting and add_commands:
        settings["add_commands"] = "false"
    elif setting == "on" or setting == "true":
        settings["add_commands"] = "true"
    elif setting == "off" or setting == "false":
        settings["add_commands"] = "false"
    else:
        if user_lang == "finnish":
            msg = "Tuntematon syöte. Anna asetus muodossa `on/off` tai `true/false`."
        else:
            msg = "Unknown input. Please give the setting in format `on/off` or `true/false`."
        await client.send_message(message.channel, msg)
        return
    write_config()
    if user_lang == "finnish":
        msg = "Asetettiin add commands tilaan: `{}`".format(settings.getboolean("add_commands"))
    else:
        msg = "Add commands set to: `{}`".format(settings.getboolean("add_commands"))
    await client.send_message(message.channel, msg)


def get_credential(credential, choose):
    with open("Data files/Credentials.json") as data_file:
        data = json.load(data_file)
    info = data[credential][choose]
    return info


def clear_user_ini(member_id):
    read_config()
    config.remove_option("LANGUAGE", member_id)
    write_config()
    pass


if __name__ == "__main__":
    print("Tätä moduulia ei ole tarkoitettu ajettavaksi itsessään. Suorita Kehittajaversio.py tai Main.py")
    print("Suljetaan...")
    exit()
