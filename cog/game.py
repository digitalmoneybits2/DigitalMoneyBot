import discord
from discord.ext import commands
from utils import checks
from utils import mysql_module
from utils import parsing
from utils import rpc_module as rpc
import random

rpc = rpc.Rpc()
mysql = mysql_module.Mysql()


class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        config = parsing.parse_json('config.json')
        self.currency_symbol = config["currency_symbol"]
        self.donation_id = config["donation"]
        self.game_id = config["game_bal"]
        self.stake_id = config["stake_bal"]
        self.treasury_id = config["treasurer"]
        self.chars = {
            0: "zero",
            1: "one",
            2: "two",
            3: "three",
            4: "four",
            5: "five",
            6: "six",
            7: "seven",
            8: "eight",
            9: "nine"}

    def format_chars(self, number):
        ret = ''
        for x in str(number):
            ret += ':{}:'.format(self.chars[int(x)])
        return ret

    @commands.command()
    @commands.check(checks.in_server)
    async def bet(self, ctx, amount: float, winmulti: int=2):
        """
        Bet an amount on the outcome of a random generated number (0-100)

        DEFAULT (amount only):
        if the number is 0 the coins will be donated for dev/promo
        double or nothing, winmulti: 2 = 49.5% win chance

        OPTIONAL (winmulti also):
        you win the amount*winmulti when the random number devided by the winmulti is a round number
        winmulti can be (2 - 10)

        TOTAL WIN AMOUNT IS AFTER PAYING FOR PLAYING !
        """
        if amount < 0.000001:
            await ctx.send("{} **:warning: 0.00000100 DMB minimum :warning:**".format(ctx.message.author.mention))
            return
        if amount > 1000.0:
            await ctx.send("{} **:warning: 1000 DMB max :warning:**".format(ctx.message.author.mention))
            return
        if winmulti < 2:
            await ctx.send("{} **:warning: winmulti must be 2 minimum :warning:**".format(ctx.message.author.mention))
            return
        if winmulti > 10:
            await ctx.send("{} **:warning: winmulti can be 10 maximum :warning:**".format(ctx.message.author.mention))
            return
        snowflake = ctx.message.author.id

        bet_user_bal = mysql.get_user_balance(self.game_id)

        if amount > round(bet_user_bal / 10, 8):
            await ctx.send("{} **:warning: You cannot bet more then: {:.8f} {} :warning:**".format(ctx.message.author.mention, bet_user_bal / 10, self.currency_symbol))
            return
        balance = mysql.get_user_balance(snowflake, check_update=True)
        if float(balance) < amount:
            await ctx.send("{} **:warning: Cannot do that ! Your balance is only {:.8f} {}! :warning:**".format(ctx.message.author.mention, float(balance), self.currency_symbol))
            return
        else:
            # begin the betting - choose a random int between 0-999999999 if even win, if odd lose
            secret_number = random.randint(0, 100)
            if secret_number == 0:
                mysql.add_rain(snowflake, self.donation_id, amount)
                await ctx.send("{} **NUMBER {} You LOSE, bot wins {:.8f} {} for ZEV dev/promo! :purple_heart::ok_hand_tone1:** You should try again.".format(ctx.message.author.mention, self.format_chars(secret_number), amount, self.currency_symbol))
            elif secret_number % winmulti == 0:
                mysql.add_rain(self.game_id, snowflake, amount * float(winmulti - 1))
                await ctx.send("{} **NUMBER {} can be divided by {} You WIN {:.8f} {}! :tada:**".format(ctx.message.author.mention, self.format_chars(secret_number), winmulti, amount * float(winmulti - 1), self.currency_symbol))
            else:
                mysql.add_rain(snowflake, self.game_id, amount)
                await ctx.send("{} **NUMBER {} You LOSE {:.8f} {}!** You should try again.".format(ctx.message.author.mention, self.format_chars(secret_number), amount, self.currency_symbol))

    @commands.command()
    @commands.check(checks.in_server)
    async def allin(self, ctx):
        """Bet max amount on the Even outcome of a random generated number (0-100)
        if the number is 0 the coins will be donated for dev/promo

        double or nothing"""
        snowflake = ctx.message.author.id
        bet_user = str(self.game_id)
        bet_user_bal = mysql.get_user_balance(self.game_id)
        balance = mysql.get_user_balance(snowflake, check_update=True)
        amount = min(bet_user_bal / 10, float(balance))
        if amount <= 0.0:
            await ctx.send("{} **:warning: You cannot bet zero coins :warning:**".format(ctx.message.author.mention))
            return
        secret_number = random.randint(0, 100)
        if secret_number == 0:
            mysql.add_rain(snowflake, self.donation_id, amount)
            await ctx.send("{} **NUMBER {} You LOSE, bot wins {:.8f} {} for ZEV dev/promo! :purple_heart::ok_hand_tone1:** You should try again.".format(ctx.message.author.mention, self.format_chars(secret_number), amount, self.currency_symbol))
        elif secret_number % 2 == 0:
            mysql.add_rain(bet_user, snowflake, amount)
            await ctx.send("{} **EVEN NUMBER! {} You WIN {:.8f} {}! :tada:**".format(ctx.message.author.mention, self.format_chars(secret_number), amount, self.currency_symbol))
        else:
            mysql.add_rain(snowflake, bet_user, amount)
            await ctx.send("{} **ODD NUMBER! {} You LOSE {:.8f} {}!** You should try again.".format(ctx.message.author.mention, self.format_chars(secret_number), amount, self.currency_symbol))


def setup(bot):
    bot.add_cog(Game(bot))
