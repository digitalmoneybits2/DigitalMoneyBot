import discord
from discord.ext import commands
from utils import parsing
from utils import mysql_module

mysql = mysql_module.Mysql()


class Deposit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        config = parsing.parse_json('config.json')
        self.currency_symbol = config["currency_symbol"]
        self.stakeflake = config["stake_bal"]
        self.treasurer = config["treasurer"]
        self.donate = config["donation"]
        self.game_id = config["game_bal"]
        self.coin_name = config["currency_name"]
        self.bot_name = config["description"]
        self.explorer = config["explorer_url"]

        # parse the embed section of the config file
        embed_config = parsing.parse_json('config.json')["embed_msg"]
        self.thumb_embed = embed_config["thumb_embed_url"]
        self.footer_text = embed_config["footer_msg_text"]
        self.embed_color = int(embed_config["color"], 16)

    @commands.command(aliases=['dep', 'DEP', 'Deposit', 'DEPOSIT'])
    async def deposit(self, ctx):
        """Show Your Deposit Address on this Tip Bot Service.

        Use the address to send coins to your account on this Tip Bot.
        """
        user = ctx.message.author
        snowflake = ctx.message.author.id
        user_addy = mysql.get_address(snowflake)
        if not user_addy:
            if mysql.check_for_user(snowflake):
                user_addy = mysql.new_address(snowflake)
                print('new user_addy:', user_addy)
            else:
                print('no such user')
                return
        balance = mysql.get_user_balance(snowflake, check_update=True)
        balance_unconfirmed = mysql.get_user_unconfirmed_balance(snowflake)

        embed = discord.Embed(title="You requested your **Deposit Address**", color=self.embed_color)
        embed.set_author(name="{}".format(self.bot_name))
        embed.set_thumbnail(url="http://{}".format(self.thumb_embed))
        embed.add_field(name="User", value="{}".format(user), inline=False)
        embed.add_field(name="Deposit Address", value="{}".format(user_addy), inline=False)
        embed.add_field(name="Balance", value="{:.8f} {}".format(round(float(balance), 8), self.currency_symbol))
        if float(balance_unconfirmed) != 0.0:
            embed.add_field(name="Unconfirmed Deposits", value="{:.8f} {}".format(round(float(balance_unconfirmed), 8), self.currency_symbol))
        embed.set_footer(text=self.footer_text)
        try:
            await ctx.message.author.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission to send this")
        if ctx.message.guild is not None:
            await ctx.send("{}, I have send your **Deposit Address** by PM! Make sure to double check that it is from me!".format(user.mention))

    @commands.command()
    async def mobile(self, ctx):
        """Show Your Deposit Address on this Tip Bot Service.

        Use the address to send coins to your account on this Tip Bot.
        Formatted for easy copying on Mobile.
        """
        user = ctx.message.author
        snowflake = ctx.message.author.id
        user_addy = mysql.get_address(snowflake)
        if not user_addy:
            if mysql.check_for_user(snowflake):
                user_addy = mysql.new_address(snowflake)
            else:
                return
        await ctx.message.author.send("Your {} ({}) Deposit Address: \n".format(self.coin_name, self.currency_symbol))
        await ctx.message.author.send("**{}**".format(user_addy))

        if ctx.message.guild is not None:
            await ctx.send("{}, I have send your **Deposit Address** by PM! Make sure to double check that it is from me!".format(user.mention))


def setup(bot):
    bot.add_cog(Deposit(bot))
