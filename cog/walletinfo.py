import discord
from discord.ext import commands
from utils import checks
from utils import mysql_module
from utils import parsing
from utils import rpc_module as rpc


mysql = mysql_module.Mysql()
config = parsing.parse_json('config.json')

botaccounts = 4


class Wallet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rpc = rpc.Rpc()
        config = parsing.parse_json('config.json')
        self.currency_symbol = config["currency_symbol"]
        self.stake_id = config["stake_bal"]
        self.coin_name = config["currency_name"]
        self.bot_name = config["description"]
        # parse the embed section of the config file
        embed_config = parsing.parse_json('config.json')["embed_msg"]
        self.thumb_embed = embed_config["thumb_embed_url"]
        self.footer_text = embed_config["footer_msg_text"]
        self.embed_color = int(embed_config["color"], 16)

    @commands.command()
    @commands.check(checks.is_owner)
    async def wallet(self, ctx):
        """Show wallet info [ADMIN ONLY]"""
        # rpc commands for getinfo
        info = self.rpc.getinfo()
        print('info:', info)
        wallet_version = str(info["version"])
        wallet_balance = float(info["balance"])
        staking_balance = float(info["stake"])
        connection_count = float(info["connections"])
        block_height = info["blocks"]
        money_supply = float(info["moneysupply"])
        paytxfee = float(info["paytxfee"])
        # number of registered users in database
        num_uses = len(mysql.get_reg_users_id()) - botaccounts
        # below used for active user calculation
        rain_config = parsing.parse_json('config.json')['rain']
        RAIN_MINIMUM = rain_config['min_amount']
        RAIN_REQUIRED_USER_ACTIVITY_M = rain_config['user_activity_required_m']
        USE_MAX_RECIPIENTS = rain_config['use_max_recipients']
        MAX_RECIPIENTS = rain_config['max_recipients']
        active_id_users = mysql.get_active_users_id(RAIN_REQUIRED_USER_ACTIVITY_M, True)
        # embed starts here
        embed = discord.Embed(title="You requested the **Wallet**", color=self.embed_color, inline=False)
        embed.set_author(name="{} ADMIN".format(self.bot_name))
        embed.set_thumbnail(url="http://{}".format(self.thumb_embed))
        embed.add_field(name="Available", value="{:.8f} {}".format(wallet_balance, self.currency_symbol), inline=True)
        embed.add_field(name="Staking", value="{:.8f} {}".format(staking_balance, self.currency_symbol), inline=True)
        embed.add_field(name="Total Balance", value="{:.8f} {}".format(wallet_balance + staking_balance, self.currency_symbol), inline=False)
        embed.add_field(name="Total {} Moneysupply".format(self.currency_symbol), value="{:.8f}".format(money_supply), inline=True)
        embed.add_field(name="Connections", value=connection_count, inline=True)
        embed.add_field(name="Block Height", value=block_height, inline=True)
        embed.add_field(name="Transaction Fee", value="{:.8f}".format(paytxfee), inline=False)
        # user information below
        embed.add_field(name="Number of Registered Users", value=num_uses, inline=False)
        embed.add_field(name="Number of Active Users", value='{} (timeout {} minutes)'.format(
            len(active_id_users), RAIN_REQUIRED_USER_ACTIVITY_M))
        embed.set_footer(text=self.footer_text)
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission to send this")

    @commands.command(hidden=True)
    @commands.check(checks.is_owner)
    async def moneysupply(self, ctx):
        """Show Money Supply [ADMIN ONLY]"""
        info = self.rpc.getinfo()
        print('info:', info)
        try:
            await ctx.send("moneysupply: {:.8f}".format(float(info["moneysupply"])))
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission to send this")

    @commands.command()
    @commands.check(checks.is_owner)
    async def newbal(self, ctx, check_update=False):
        """Show wallet new coins [ADMIN ONLY]"""
        if ctx.guild:
            await ctx.message.delete()
        info = self.rpc.getinfo()
        print(info)
        wallet_balance = float(info["balance"])
        staking = float(info["stake"])
        totalwallet = round(wallet_balance + staking, 8)
        totalbalances = 0.0
        users = mysql.get_reg_users_id()
        for user in users:
            balances = mysql.get_all_balance(int(user), check_update=check_update)
            usertotal = round(float(balances['balance']) + float(balances['staking_balance']) + float(balances['balance_unconfirmed']), 8)
            totalbalances = round(totalbalances + usertotal, 8)
            print('{}  {:17.8f} {:17.8f} {:17.8f}'.format(int(user), float(balances['balance']), float(balances['staking_balance']), float(balances['balance_unconfirmed'])))
        print('total wallet coins: {:18.8f}\ntotal user coins:   {:18.8f}\ntotal new coins:    {:18.8f}'.format(
            totalwallet, totalbalances, totalwallet - totalbalances))
        await ctx.send('```total wallet coins: {:18.8f}\ntotal user coins:   {:18.8f}\ntotal new coins:    {:18.8f}```'.format(
            totalwallet, totalbalances, totalwallet - totalbalances))


def setup(bot):
    bot.add_cog(Wallet(bot))
