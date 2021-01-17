import database
import discord
from discord.ext import commands
import logging
from logging.handlers import RotatingFileHandler
import os
# import re
# import time
# import traceback
from utils import checks
from utils import helpers
from utils import mysql_module
from utils import output
from utils import parsing
from utils.logger import create_logger

intents = discord.Intents.default()
intents.members = True

# LOGPATH = 'log'

config = parsing.parse_json('config.json')
skip_cogs = config['skip_cogs']


def start_setup():
    # check if staking account is set up
    staking_account = config["stake_bal"]
    if Mysql.get_staking_user(staking_account) is None:
        Mysql.register_user(staking_account)

    # check if treasury account is set up
    treasury_account = config["treasurer"]
    if Mysql.get_staking_user(treasury_account) is None:
        Mysql.register_user(treasury_account)

    # check if donation account is set up
    donate_account = config["donation"]
    if Mysql.get_staking_user(donate_account) is None:
        Mysql.register_user(donate_account)

    # check if game account is set up
    game_account = config["game_bal"]
    if Mysql.get_staking_user(game_account) is None:
        Mysql.register_user(game_account)


# class Printable:
#     def __repr__(self):
#         from pprint import pformat
#         return "<" + type(self).__name__ + ">\n" + pformat(vars(self), indent=4, width=1)


discordlog = create_logger('discord')
botlog = create_logger('bot')
messageslog = create_logger('messages', messagelog=True)
# messageslog = create_logger('messages')

Mysql = mysql_module.Mysql()
bot = commands.Bot(command_prefix=config['prefix'], description=config["description"], intents=intents)

try:
    os.remove("log.txt")
except FileNotFoundError:
    pass

startup_extensions = os.listdir("./cog")
if "__pycache__" in startup_extensions:
    startup_extensions.remove("__pycache__")
# for x in startup_extensions:
#     if x[0] == '_':
#         startup_extensions.remove(x)

startup_extensions = [x.replace('.py', '') for x in startup_extensions]
startup_extensions = [x for x in startup_extensions if x not in skip_cogs]
startup_extensions = [x for x in startup_extensions if x[0] != '_']

loaded_extensions = []


@bot.event
async def on_ready():
    output.info("Loading {} extension(s)...".format(len(startup_extensions)))

    for extension in startup_extensions:
        try:
            bot.load_extension("cog.{}".format(extension.replace(".py", "")))
            loaded_extensions.append(extension)

        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            output.error('Failed to load extension {}\n\t->{}'.format(extension, exc))
    output.success('Successfully loaded the following extension(s): {}'.format(', '.join(loaded_extensions)))
    output.info('You can now invite the bot to a server using the following link: https://discordapp.com/oauth2/authorize?client_id={}&scope=bot'.format(bot.user.id))
    output.info('database system accounts check..'.format(bot.user.id))
    start_setup()
    output.info('done.'.format(bot.user.id))


@bot.event
async def on_message(message):
    if message.guild:
        if message.guild.id != config["discord"]["server"]:
            return
        if message.channel.id != config["discord"]["channel"]:
            return
    print('')
    print(message)
    print(message.content)
    messageslog.info('{}{} {} {} {} {} | {}'.format(
        str(message.guild.id) + ' ' if message.guild else '',
        str(message.guild) if message.guild else 'DM',
        str(message.channel.id), str(message.channel),
        str(message.author.id), str(message.author),
        str(message.content)))
    # disregard messages sent by our own bot
    if message.author.id == bot.user.id:
        return
    # check if the owner is registered
    # must be done to add an entry to the db and initialize the db
    owner = config["owners"]
    for ids in owner:
        if Mysql.get_user(ids) is None:
            if message.author.id == ids:
                Mysql.register_user(ids)
    # users that are not registered will be caught below
    # continue if the message is not from the bot
    if not message.author.bot:
        # print('author no bot')
        # config register keyword
        rkeyword = str(config["register_keyword"])
        prefix = str(config["prefix"])
        # rkeywordcall is the register command for users not registered
        rkeywordcall = prefix + rkeyword
        coin_name = str(config["currency_symbol"])
        # authid is the unique discord id number for the user that send the message to the server
        authid = message.author.id
        # check if the message author is in the database (meaning they are registered)
        if Mysql.get_user(authid) is None:
            if str(message.content).startswith(rkeywordcall) is True:
                Mysql.register_user(authid)
                await message.channel.send('{} Welcome! :tada:'.format(message.author.mention))
                await message.channel.send('Thank You for registering. Use {}deposit to check your {} deposit address'.format(prefix, coin_name))
                return
            elif str(message.content).startswith(prefix) is True:
                Mysql.register_user(authid)
                await message.channel.send('Welcome! {0} You are Now Registered. :tada:.\nUse:\n{1}bal to check your {2} balance\n{1}deposit to get your {2} deposit address'.format(
                    message.author.mention, prefix, coin_name))
                return
        else:
            if Mysql.user_last_msg_check(message.author.id, message.content, helpers.is_private_dm(bot, message.channel)) is False:
                return
            if str(message.content).startswith(prefix) is True:
                botlog.info('{}{} {} {} {} {} | {}'.format(
                    str(message.guild.id) + ' ' if message.guild else '',
                    str(message.guild) if message.guild else 'DM',
                    str(message.channel.id), str(message.channel),
                    str(message.author.id), str(message.author),
                    str(message.content)))
                await bot.process_commands(message)


async def send_cmd_help(ctx):
    if ctx.invoked_subcommand:
        pages = bot.formatter.format_help_for(ctx, ctx.invoked_subcommand)
    else:
        pages = bot.formatter.format_help_for(ctx, ctx.command)
    for page in pages:
        em = discord.Embed(title="Missing args :x:",
                           description=page.strip("```").replace('<', '[').replace('>', ']'),
                           color=discord.Color.red())
        await ctx.send(embed=em)


@bot.command()
@commands.check(checks.is_owner)
async def shutdown(ctx):
    """Shut down the bot [ADMIN ONLY]"""
    author = str(ctx.message.author)
    try:
        await ctx.send("Shutting down...")
        await bot.logout()
        output.info('{} has shut down the bot...'.format(author))
    except Exception as e:
        print(e)


# @bot.command(hidden=True)
@bot.command()
@commands.check(checks.is_owner)
async def restart(ctx):
    """Restart the bot"""
    author = str(ctx.message.author)
    try:
        await ctx.send("Restarting...")
        await bot.logout()
        output.info('{} has restarted the bot...'.format(author))
    except Exception as e:
        print(e)
        pass
    finally:
        os.system('./restart.sh')


@bot.command()
@commands.check(checks.is_owner)
async def load(ctx, module: str):
    """Load a cog located in /cogs [ADMIN ONLY]"""
    author = str(ctx.message.author)
    module = module.strip()
    try:
        bot.load_extension("cog.{}".format(module))
        output.info('{} loaded module: {}'.format(author, module))
        startup_extensions.append(module)
        await ctx.send("Successfully loaded {}.py".format(module))
    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        output.error('{} attempted to load module \'{}\' but the following '
                     'exception occured;\n\t->{}'.format(author, module, exc))
        await ctx.send('Failed to load extension {}\n\t->{}'.format(module, exc))


@bot.command()
@commands.check(checks.is_owner)
async def reload(ctx, module: str):
    """Load a cog located in /cogs [ADMIN ONLY]"""
    author = str(ctx.message.author)
    module = module.strip()
    try:
        bot.reload_extension("cog.{}".format(module))
        output.info('{} reloaded module: {}'.format(author, module))
        await ctx.send("Successfully reloaded {}.py".format(module))
    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        output.error('{} attempted to reload module \'{}\' but the following '
                     'exception occured;\n\t->{}'.format(author, module, exc))
        await ctx.send('Failed to reload extension {}\n\t->{}'.format(module, exc))


@bot.command()
@commands.check(checks.is_owner)
async def unload(ctx, module: str):
    """Unload any loaded cog [ADMIN ONLY]"""
    author = str(ctx.message.author)
    module = module.strip()
    try:
        bot.unload_extension("cog.{}".format(module))
        output.info('{} unloaded module: {}'.format(author, module))
        startup_extensions.remove(module)
        await ctx.send("Successfully unloaded {}.py".format(module))
    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        await ctx.send('Failed to load extension {}\n\t->{}'.format(module, exc))


@bot.command()
@commands.check(checks.is_owner)
async def loaded(ctx):
    """List loaded cogs [ADMIN ONLY]"""
    string = ""
    for cog in loaded_extensions:
        string += str(cog) + "\n"
    await ctx.send('Currently loaded extensions:\n```{}```'.format(string))


@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.MissingRequiredArgument):
        await send_cmd_help(ctx)
    elif isinstance(error, commands.BadArgument):
        await send_cmd_help(ctx)
    elif isinstance(error, commands.CommandInvokeError):
        output.error("Exception in command '{}', {}".format(ctx.command.qualified_name, error.original))
        oneliner = "Error in command '{}' - {}: {}\nIf this issue persists, Please report it in the support server.".format(
            ctx.command.qualified_name, type(error.original).__name__, str(error.original))
        await ctx.send(oneliner)


database.run()
bot.run(config["discord"]["token"], bot=True, reconnect=True)
bot.loop.close()
