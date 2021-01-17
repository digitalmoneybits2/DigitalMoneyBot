import discord
from discord.ext import commands
from utils import checks
from utils import mysql_module
from utils import parsing
from utils import helpers
from utils.logger import create_logger

import random
import math

mysql = mysql_module.Mysql()


class Rain(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rainlog = create_logger('rain', messagelog=True)

    @commands.check(checks.in_server)
    @commands.command()
    async def rain(self, ctx, amount: float, usercount=None):
        """Rain all active users.

        optional:
        select random [usercount] from active users"""
        if usercount:
            try:
                usercount = int(usercount)
                if usercount < 1:
                    return
            except ValueError as e:
                print('ValueError:', e)
                pass
        print('usercount:', usercount)
        config = parsing.parse_json('config.json')
        CURRENCY_SYMBOL = config["currency_symbol"]

        rain_config = parsing.parse_json('config.json')['rain']
        RAIN_MINIMUM = rain_config['min_amount']
        RAIN_REQUIRED_USER_ACTIVITY_M = rain_config['user_activity_required_m']
        USE_MAX_RECIPIENTS = rain_config['use_max_recipients']
        MAX_RECIPIENTS = rain_config['max_recipients']

        if helpers.is_private_dm(self.bot, ctx.message.channel):
            return
        if amount < 0:
            await ctx.send("**:warning: Nice try! :smile: ..but the amount can not be negative. :warning:**".format(float(amount), CURRENCY_SYMBOL, float(RAIN_MINIMUM)))
            return
        if amount < RAIN_MINIMUM:
            await ctx.send("**:warning: Amount {:.8f} {} for rain is less than minimum {:.8f} required! :warning:**".format(float(amount), CURRENCY_SYMBOL, float(RAIN_MINIMUM)))
            return

        snowflake = ctx.message.author.id

        balance = mysql.get_user_balance(snowflake, check_update=True)
        if not balance:
            return
        if float(balance) < amount:
            await ctx.send("{0} **:warning: You cannot rain more {1} than you have! :warning:**\n..your {1} balance: {2:.8f}".format(ctx.message.author.mention, CURRENCY_SYMBOL, float(balance)))
            return

        # Create tip list
        active_id_users = mysql.get_active_users_id(RAIN_REQUIRED_USER_ACTIVITY_M, True)
        if int(ctx.message.author.id) in active_id_users:
            active_id_users.remove(int(ctx.message.author.id))

        users_list = []
        for user in ctx.message.guild.members:
            if user.id in active_id_users:
                users_list.append(user)

        if len(users_list) == 0:
            await ctx.send("{}, you are all alone if we don't include bots! Trying raining when people are online and active.".format(ctx.message.author.mention))
            return

        print(users_list)
        if USE_MAX_RECIPIENTS:
            if len(users_list) > MAX_RECIPIENTS:
                users_list = list(random.sample(set(users_list), k=MAX_RECIPIENTS))

        if usercount:
            if len(users_list) > usercount:
                users_list = list(random.sample(set(users_list), k=usercount))

        amount_split = math.floor(float(amount) * 1e8 / len(users_list)) / 1e8
        print('amount_split:', amount_split)
        if amount_split == 0:
            await ctx.send("{} **:warning:{:.8f} {} is not enough to split between {} users:warning:**".format(ctx.message.author.mention, float(amount), CURRENCY_SYMBOL, len(users_list)))
            return

        receivers = []
        for active_user in users_list:
            print(active_user)
            print(active_user.mention)
            receivers.append(active_user.mention)
            self.rainlog.info('{:40s} {} {:17.8f} {}'.format(
                str(active_user), active_user.id,
                float(amount_split), CURRENCY_SYMBOL))
            mysql.add_rain(snowflake, active_user.id, amount_split)

        if len(receivers) == 0:
            await ctx.send("{}, you are all alone if we don't include bots! Trying raining when people are online and active.".format(ctx.message.author.mention))
            return

        self.rainlog.info('{:40s} {} {:17.8f} {}'.format(
            str(ctx.message.author), ctx.message.author.id,
            -float(amount), CURRENCY_SYMBOL))

        totalrain = round(amount_split * float(len(receivers)), 8)
        print('totalrain:', totalrain)
        await ctx.send(":cloud_rain: {} **Rained {:.8f} {} on {} users** (Total {:.8f} {}) :cloud_rain:".format(
            ctx.message.author.mention, float(amount_split), CURRENCY_SYMBOL, len(receivers), totalrain, CURRENCY_SYMBOL))
        users_soaked_msg = []
        idx = 0
        for x in receivers:
            users_soaked_msg.append(x)
            idx += 1
            if (len(users_soaked_msg) >= 50) or (idx == len(receivers)):
                await ctx.send("{}".format(' '.join(users_soaked_msg)))
                del users_soaked_msg[:]
                users_soaked_msg = []


def setup(bot):
    bot.add_cog(Rain(bot))
