import discord
from discord.ext import commands
from utils import mysql_module
from utils import parsing
from utils import rpc_module
import math

rpc = rpc_module.Rpc()
mysql = mysql_module.Mysql()


class Withdraw(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        config = parsing.parse_json('config.json')
        self.is_treasurer = config["treasurer"]
        self.explorer = config["explorer_url"]
        self.currency_symbol = config["currency_symbol"]
        self.coin_name = config["currency_name"]
        self.withdrawfee = config["txfee"]
        self.withdrawmaxfee = config["withdraw_max_fee"]
        self.minwithdraw = config["min_withdrawal"]
        self.bot_name = config["description"]
        # parse the embed section of the config file
        embed_config = parsing.parse_json('config.json')["embed_msg"]
        self.thumb_embed = embed_config["thumb_embed_url"]
        self.footer_text = embed_config["footer_msg_text"]
        self.embed_color = int(embed_config["color"], 16)

    @commands.command()
    async def fee(self, ctx):
        """Get the current withdraw Fee
        """
        await ctx.send("{} **The current withdraw Fee is {:.2f} {}**".format(
            ctx.message.author.mention, self.withdrawfee, self.currency_symbol))

    @commands.command()
    async def withdraw(self, ctx, address: str, amount: float):
        """Withdraw coins from your account to any address.

        You agree to pay a withdrawal fee to support the costs of this service
        """
        snowflake = ctx.message.author.id
        print('withdraw snowflake:', snowflake)
        if amount < self.minwithdraw:
            await ctx.send("{} **:warning: Minimum withdrawal amount is {:.8f} {} :warning:**".format(
                ctx.message.author.mention, self.minwithdraw, self.currency_symbol))
            return
        print('withdraw amount > minwithdraw')

        abs_amount = abs(amount)
        if math.log10(abs_amount) > 8:
            await ctx.send(":warning: **Invalid amount!** :warning:")
            return
        print('1')

        conf = rpc.validateaddress(address)
        if not conf["isvalid"]:
            await ctx.send("{} **:warning: Invalid address! :warning:**".format(ctx.message.author.mention))
            return
        print('2')

        account_name = rpc.getaccount(address)
        print('3')

        if rpc.getaccountaddress(account_name) is not None:
            await ctx.send("{} **:warning: You cannot withdraw to an address owned by this bot! :warning:** Please use tip instead!".format(ctx.message.author.mention))
            return
        print('4')

        balance = mysql.get_user_balance(snowflake, check_update=True)
        print('5')
        if float(balance) < amount:
            await ctx.send("{} **:warning: You cannot withdraw more {} than you have! :warning:**".format(ctx.message.author.mention, self.currency_symbol))
            return
        print('doing withdraw')
        txid = mysql.create_withdrawal(snowflake, address, amount)
        # if txid is None:
        if not txid:
            await ctx.send("{} your withdraw failed despite having the necessary balance! Please contact the bot owner".format(ctx.message.author.mention))
        else:
            usermention = ctx.message.author.mention
            updbalance = mysql.get_user_balance(snowflake, check_update=True)
            # send an embed receipt to the user
            embed = discord.Embed(title="You made a **Withdrawal**", color=self.embed_color)
            embed.set_author(name="{}".format(self.bot_name))
            embed.set_thumbnail(url="http://{}".format(self.thumb_embed))
            embed.add_field(name="User", value="{}".format(usermention), inline=True)
            embed.add_field(name="New Balance", value="{:.8f} {}".format(round(float(updbalance), 8), self.currency_symbol), inline=True)
            embed.add_field(name="TXID", value="http://{}{}".format(self.explorer, str(txid)), inline=False)
            embed.add_field(name="Withdrawal Address", value="{}".format(address), inline=False)
            embed.add_field(name="Withdraw Amount", value="{:.8f} {}".format(float(amount), self.currency_symbol), inline=True)
            embed.add_field(name="Withdraw Fee", value="{:.8f} {}".format(self.withdrawfee, self.currency_symbol), inline=True)
            embed.set_footer(text=self.footer_text)
            try:
                await ctx.message.author.send(embed=embed)
            except discord.HTTPException:
                await ctx.send("I need the `Embed links` permission to send this")

            if ctx.message.guild is not None:
                await ctx.send("{}, I have send your **Withdrawal Confirmation** by PM! Make sure to double check that it is from me!".format(usermention))
                await ctx.send(":warning: {}, To Protect Your Privacy, please make Withdrawals by messaging me directly next time. :warning:".format(usermention))


def setup(bot):
    bot.add_cog(Withdraw(bot))
