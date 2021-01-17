import discord
from discord.ext import commands
from utils import checks
from utils import mysql_module
from utils import parsing
from utils import rpc_module as rpc

# result_set = database response with parameters from query
# db_bal = nomenclature for result_set["balance"]
# snowflake = snowflake from message context, identical to user in database
# wallet_bal = nomenclature for wallet reponse

mysql = mysql_module.Mysql()


class Balance(commands.Cog):

    def __init__(self, bot):
        self.rpc = rpc.Rpc()
        self.bot = bot
        config = parsing.parse_json('config.json')
        self.currency_symbol = config["currency_symbol"]
        self.stake_id = config["stake_bal"]
        self.donate_id = config["donation"]
        self.game_id = config["game_bal"]
        self.coin_name = config["currency_name"]
        self.bot_name = config["description"]
        embed_config = parsing.parse_json('config.json')["embed_msg"]
        self.thumb_embed = embed_config["thumb_embed_url"]
        self.footer_text = embed_config["footer_msg_text"]
        self.embed_color = int(embed_config["color"], 16)

    async def make_embed(self, uname, db_bal, db_bal_unconfirmed, staking, stake_total, donate_total, ctx):
        embed = discord.Embed(title="You requested your **Balance**", color=self.embed_color)
        embed.set_author(name=self.bot_name)
        embed.set_thumbnail(url="http://{}".format(self.thumb_embed))
        embed.add_field(name="User", value=uname.mention, inline=False)
        embed.add_field(name="Balance", value="{:.8f} {}".format(round(float(db_bal), 8), self.currency_symbol), inline=True)
        if float(db_bal_unconfirmed) != 0.0:
            embed.add_field(name="Unconfirmed Deposits", value="{:.8f} {}".format(float(db_bal_unconfirmed), self.currency_symbol), inline=True)
        if float(staking) != 0.0:
            embed.add_field(name="Staking Balance", value="{:.8f} {}".format(float(staking), self.currency_symbol), inline=False)
        if float(staking) + float(db_bal_unconfirmed) + float(stake_total) != 0.0:
            embed.add_field(name="Total Balance", value="{:.8f} {}".format(round(float(staking), 8) + round(float(db_bal), 8), self.currency_symbol), inline=True)
        if float(stake_total) != 0.0:
            embed.add_field(name="Your Total Staking Rewards", value="{:.8f} {}".format(float(stake_total), self.currency_symbol), inline=True)
        if float(donate_total) != 0.0:
            embed.add_field(name="Your Total Donations", value="{:.8f} {}".format(float(donate_total), self.currency_symbol), inline=True)
        embed.set_footer(text=self.footer_text)
        return embed

    async def do_embed(self, uname, server, db_bal, db_bal_unconfirmed, staking, stake_total, donate_total, ctx):
        embed = await self.make_embed(uname, db_bal, db_bal_unconfirmed, staking, stake_total, donate_total, ctx)
        try:
            print('embed send')
            await ctx.message.author.send(embed=embed)
            if server is not None:
                await ctx.send("{}, I Have send you a DM with your **Balance**! Make sure to double check that it is from me!".format(uname.mention))
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission to send this")

    async def do_all_embed(self, ctx, accountname, request, db_bal, stake_total):
        embed = discord.Embed(title="You requested the **{}**".format(request), color=self.embed_color)
        embed.set_author(name="{}".format(self.bot_name))
        embed.set_thumbnail(url="http://{}".format(self.thumb_embed))
        embed.add_field(name="User", value="{} {}".format(self.coin_name, accountname), inline=False)
        embed.add_field(name="Balance", value="{:.8f} {}".format(round(float(db_bal), 8), self.currency_symbol))
        embed.set_footer(text=self.footer_text)
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission to send this")

    async def do_showembed(self, uname, db_bal, db_bal_unconfirmed, staking, stake_total, donate_total, ctx):
        embed = await self.make_embed(uname, db_bal, db_bal_unconfirmed, staking, stake_total, donate_total, ctx)
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission to send this")

    @commands.command(aliases=['BALANCE', 'Balance'])
    async def balance(self, ctx):
        """Sends your account balance via DM"""
        snowflake = ctx.message.author.id
        balances = mysql.get_all_balance(snowflake, check_update=True)
        stakes = mysql.get_tip_amounts_from_id(self.stake_id, snowflake)
        donations = sum(mysql.get_total_tip_amounts_from_id(snowflake))
        await self.do_embed(
            ctx.message.author, ctx.message.guild, balances['balance'],
            balances['balance_unconfirmed'], balances['staking_balance'],
            sum(stakes), donations, ctx)

    @commands.command(aliases=['BAL', 'Bal', 'bals', 'BALS', 'showbal'])
    async def bal(self, ctx):
        """Display your balance publicly in the chat"""
        snowflake = ctx.message.author.id
        balances = mysql.get_all_balance(snowflake, check_update=True)
        stakes = mysql.get_tip_amounts_from_id(self.stake_id, snowflake)
        donations = sum(mysql.get_total_tip_amounts_from_id(snowflake))
        await self.do_showembed(
            ctx.message.author, balances['balance'],
            balances['balance_unconfirmed'], balances['staking_balance'],
            sum(stakes), donations, ctx)

    @commands.check(checks.is_owner)
    @commands.command()
    async def userbal(self, ctx):
        """Display a registred user balance [ADMIN ONLY]"""
        for member in ctx.message.mentions:
            print(member)
            snowflake = member.id
            balances = mysql.get_all_balance(snowflake, check_update=True)
            stakes = mysql.get_tip_amounts_from_id(self.stake_id, snowflake)
            donations = mysql.get_total_tip_amounts_from_id(snowflake)
            await self.do_showembed(
                member, balances['balance'],
                balances['balance_unconfirmed'], balances['staking_balance'],
                sum(stakes), sum(donations), ctx)

    @commands.check(checks.is_owner)
    @commands.command()
    async def useridbal(self, ctx, snowflake):
        """Display a registred user balance [ADMIN ONLY]"""
        balances = mysql.get_all_balance(snowflake, check_update=True)
        await ctx.send("{}".format(str(balances)))

    @commands.command()
    @commands.check(checks.is_owner)
    async def donations(self, ctx):
        """Display the Donations Balance [ADMINS ONLY]"""
        snowflake = str(self.donate_id)
        name = str("Donations Account")
        balance = mysql.get_user_balance(snowflake, check_update=True)
        stakes = mysql.get_tip_amounts_from_id(self.stake_id, snowflake)
        if not stakes:
            stakes = [0.0]
        await self.do_all_embed(ctx, name, "Donation Balance", balance, sum(stakes))

    # @commands.check(checks.is_owner)
    @commands.command()
    async def gamebal(self, ctx):
        """Display the Game Balance [ADMINS ONLY]"""
        snowflake = str(self.game_id)
        name = str("Game Account")
        balance = mysql.get_user_balance(snowflake, check_update=True)
        stakes = mysql.get_tip_amounts_from_id(self.stake_id, snowflake)
        await self.do_all_embed(ctx, name, "Game Balance", balance, sum(stakes))

    @commands.command()
    @commands.check(checks.is_owner)
    async def stakebal(self, ctx):
        """Display the Staking Balance [ADMINS ONLY]"""
        snowflake = str(self.stake_id)
        name = str("Staking Pool Extra Rewards")
        balance = mysql.get_user_balance(snowflake, check_update=True)
        stakes = mysql.get_tip_amounts_from_id(self.stake_id, snowflake)
        await self.do_all_embed(ctx, name, "Staking Balance", balance, sum(stakes))


def setup(bot):
    bot.add_cog(Balance(bot))
