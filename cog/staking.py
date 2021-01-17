import discord
from discord.ext import commands
from utils import mysql_module
from utils import parsing
from utils import checks

# rpc = rpc_module.Rpc()
mysql = mysql_module.Mysql()


class Staking(commands.Cog):
    """Get the best rewards with our staking pool !

    Together we will rise!"""

    def __init__(self, bot):
        self.bot = bot
        config = parsing.parse_json('config.json')
        self.currency_symbol = config["currency_symbol"]
        # self.treasurer_id = config["treasurer"]
        self.stake_bal_id = config["stake_bal"]
        # self.donation_id = config["donation"]
        # self.game_bal = config["game_bal"]

        # parse the embed section of the config file
        embed_config = parsing.parse_json('config.json')["embed_msg"]
        self.thumb_embed = embed_config["thumb_embed_url"]
        self.footer_text = embed_config["footer_msg_text"]
        self.embed_color = int(embed_config["color"], 16)

    @commands.command()
    async def stake(self, ctx, amount):
        """Move coins from your Balance to your Staking Balance.

        Stake your coins in our great staking pool. Better rewards with our pool!"""
        snowflake = ctx.message.author.id
        author = ctx.message.author.mention
        if mysql.check_for_user(snowflake) is None:
            return
        balance = float(mysql.get_user_balance(snowflake, check_update=True))
        if type(amount) == str:
            if amount.lower() == 'all':
                amount = balance
                if amount == 0:
                    await ctx.send("{} **:warning: You are staking all :warning:**".format(author))
                    return
        try:
            amount = round(float(amount), 8)
        except ValueError:
            return
        if amount == 0:
            await ctx.send("{} **:warning:You cannot stake zero coins!:warning:**".format(author))
            return
        if amount < 0:
            await ctx.send("{} **:warning:You cannot stake a negative amount!:warning:**".format(author))
            return
        if amount > balance:
            amount = balance

        mysql.add_to_staking_balance(snowflake, amount)
        mysql.remove_from_balance(snowflake, amount)
        await ctx.send("{} **You moved {:.8f} {} from your balance to the staking pool! :moneybag:**".format(author, amount, self.currency_symbol))

    @commands.command()
    async def unstake(self, ctx, amount: float):
        """Move coins from your Staking Balance to your Balance.

        Unstake your coins from our great staking pool.
        You only get rewards for coins in your Staking Balance in the next payout round !"""
        snowflake = ctx.message.author.id
        author = ctx.message.author.mention
        amount = round(amount, 8)
        if amount == 0:
            await ctx.send("{} **:warning:You cannot unstake zero coins!:warning:**".format(author))
            return
        elif amount < 0:
            await ctx.send("{} **:warning:You cannot unstake a negative amount!:warning:**".format(author))
            return
        # check if receiver is in database
        elif mysql.check_for_user(snowflake) is not None:
            stakebalance = mysql.get_user_staking_balance(snowflake)
            print('stake balance')
            print(stakebalance)
            # check the senders balance for overdraft and return error to user in chat
            if float(stakebalance) < amount:
                await ctx.send("{} **:warning:You cannot unstake more coins than what you currently have staking!:warning:**".format(author))
            else:
                mysql.remove_from_staking_balance(snowflake, amount)
                mysql.add_to_balance(snowflake, amount)
                await ctx.send("{} **You moved {:.8f} {} from the staking pool to your balance! :moneybag:**".format(author, amount, self.currency_symbol))
        # if receiver not in database return error to user in chat
        else:
            await ctx.send("{} **:warning:You cannot unstake. You are not Registered:warning:**".format(author))


def setup(bot):
    bot.add_cog(Staking(bot))
