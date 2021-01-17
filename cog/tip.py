import discord
from discord.ext import commands
from utils import checks
from utils import mysql_module
from utils import parsing
from utils import rpc_module as rpc


rpc = rpc.Rpc()
mysql = mysql_module.Mysql()


class Tip(commands.Cog):
    """Tip users"""

    def __init__(self, bot):
        self.bot = bot
        config = parsing.parse_json('config.json')
        self.currency_symbol = config["currency_symbol"]
        self.treasurer_id = config["treasurer"]
        self.stake_bal_id = config["stake_bal"]
        self.donation_id = config["donation"]
        self.game_bal = config["game_bal"]
        # parse the embed section of the config file
        embed_config = parsing.parse_json('config.json')["embed_msg"]
        self.thumb_embed = embed_config["thumb_embed_url"]
        self.footer_text = embed_config["footer_msg_text"]
        self.embed_color = int(embed_config["color"], 16)

    @commands.command()
    @commands.check(checks.in_server)
    async def tip(self, ctx, amount: float):
        """Tip users coins. You can tip multiple users. Amount is per user!"""
        # async def tip(self, ctx, amount: float, *args: discord.Member):
        snowflake = ctx.message.author.id

        if amount <= 0.0:
            await ctx.send("{} **:warning: You cannot tip a negative amount :warning:**".format(ctx.message.author.mention))
            return

        tipusers = []
        for user in ctx.message.mentions:
            if mysql.check_for_user(user.id) is not None:
                tipusers.append(user)
            else:
                await ctx.send("{} **:warning: You cannot tip {}. That user is not Registered :warning:**".format(ctx.message.author.mention, user.mention))
                return
        tipusers = list(set(tipusers))

        if ctx.message.author in tipusers:
            await ctx.send("{} **:warning: You cannot tip yourself! :warning:**".format(ctx.message.author.mention))
            return

        total = len(tipusers) * amount
        balance = mysql.get_user_balance(snowflake, check_update=True)
        if not balance or (float(balance) < total):
            await ctx.send("{} **:warning: You cannot tip more money than you have! :warning:**".format(ctx.message.author.mention))
            return

        for tip_user in tipusers:
            print('tip_user:', tip_user)
            print('tip_user.id:', tip_user.id)
            mysql.add_rain(snowflake, tip_user.id, amount)
            await ctx.send("**{} Tipped {:.8f} {} {}! :moneybag:**".format(ctx.message.author.mention, amount, self.currency_symbol, tip_user.mention))

    @commands.command()
    async def donate(self, ctx, amount: float, tip_user=None):
        """Donate to a system account

            system accounts:

        treasurer:             0
        stake rewards:         1
        donation dev/promo:    2
        games/bets:            3
        """
        donateaccounts = {100000000000000010: 'treasurer', 100000000000000011: 'stake rewards', 100000000000000012: 'donation dev/promo', 100000000000000013: 'games/bets'}
        snowflake = ctx.message.author.id
        print('snowflake:', snowflake)
        if not tip_user:
            tip_user = self.donation_id
        if tip_user in ['0', '1', '2', '3']:
            tip_user = '10000000000000001' + tip_user
        else:
            await ctx.send("{} **:warning: You can only donate a system account :warning:**".format(ctx.message.author.mention))
            return

        tip_user_id = int(tip_user.lstrip('<@').rstrip('>'))
        print('tip_user:', tip_user)
        print('tip_user_id:', tip_user_id)

        # check if sender is trying to send to themselves and return error to user in chat
        if snowflake == tip_user_id:
            await ctx.send("{} **:warning: You cannot donate to yourself! :warning:**".format(ctx.message.author.mention))
            return
        # check if amount is negative and return error to user in chat
        if amount <= 0.0:
            await ctx.send("{} **:warning: You cannot donate a negative amount!:warning:**".format(ctx.message.author.mention))
            return
        # check if receiver is in database
        if mysql.check_for_user(tip_user_id) is not None:
            balance = mysql.get_user_balance(snowflake, check_update=True)
            # check the senders balance for overdraft and return error to user in chat
            if float(balance) < amount:
                await ctx.send("{} **:warning:You cannot donate more money than you have!:warning:**".format(ctx.message.author.mention))
            else:
                if tip_user_id in donateaccounts.keys():
                    tip_user = 'to system account ' + donateaccounts[tip_user_id]

                mysql.add_tip(snowflake, tip_user_id, amount)
                donations = sum(mysql.get_total_tip_amounts_from_id(snowflake))
                if donations >= 100000.0:
                    member = ctx.message.author
                    try:
                        role = discord.utils.get(ctx.guild.roles, name="VIP")
                        # print(role)
                        print('**VIP**')
                        await member.add_roles(role)
                    except Exception as e:
                        print('Exception: {}'.format(Exception))

                await ctx.send("{} **Donated {} {} {} ! Thank You :tada:**".format(ctx.message.author.mention, str(amount), self.currency_symbol, tip_user))

        # if receiver not in database return error to user in chat
        else:
            await ctx.send("{} **:warning:You cannot tip {}. That user is not Registered:warning:**".format(ctx.message.author.mention, tip_user))


def setup(bot):
    bot.add_cog(Tip(bot))
