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


class AdminTools(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.rpc = rpc.Rpc()
        # parse the config file
        config = parsing.parse_json('config.json')
        self.currency_symbol = config["currency_symbol"]
        self.stakeflake = config["stake_bal"]
        self.treasurer = config["treasurer"]
        self.donate = config["donation"]
        self.game_id = config["game_bal"]
        self.coin_name = config["currency_name"]
        self.bot_name = config["description"]
        # parse the embed section of the config file
        embed_config = parsing.parse_json('config.json')["embed_msg"]
        self.thumb_embed = embed_config["thumb_embed_url"]
        self.footer_text = embed_config["footer_msg_text"]
        self.embed_color = int(embed_config["color"], 16)

    async def do_all_embed(self, ctx, accountname, request, db_bal, stake_total):
        # Simple embed function for displaying username and balance
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

    @commands.command()
    @commands.check(checks.is_owner)
    async def fees(self, ctx):
        """Display the Fee Balance [ADMINS ONLY]"""
        snowflake = str(self.treasurer)
        name = str("Treasury Account - Withdrawal and Staking Fees")
        balance = mysql.get_user_balance(snowflake, check_update=True)
        stakes = mysql.get_tip_amounts_from_id(self.stakeflake, snowflake)
        await self.do_all_embed(ctx, name, "Treasury Balance", balance, sum(stakes))

    @commands.command(aliases=['usercoins'])
    @commands.check(checks.is_owner)
    async def balancestotal(self, ctx):
        # users_list = []
        totalbalances = 0.0
        totalstaking = 0.0
        users = mysql.get_reg_users_id()
        users = [x for x in users if x not in [
            self.stakeflake, self.treasurer, self.donate, self.game_id]]
        while users:
            prnt = '```{:>18s} {:>18s} {:>18s} {:>18s} {:>18s}'.format(
                'user', 'balances', 'unconfirmed', 'staking', 'total')
            for user in users[-8:]:
                balances = mysql.get_all_balance(int(user))
                totalbalances = round(
                    totalbalances + round(float(balances['balance']), 8), 8)
                totalstaking = round(
                    totalstaking + round(float(balances['staking_balance']), 8), 8)
                prnt += '\n{:18d} {:18.8f} {:18.8f} {:18.8f} {:18.8f}'.format(
                    int(user),
                    balances['balance'],
                    balances['balance_unconfirmed'],
                    balances['staking_balance'],
                    balances['balance'] + balances['staking_balance'])

            await ctx.send(prnt + '```')
            users = users[:-8]
        print('total balances:   {:18.8f}'.format(totalbalances))
        print('total staking:    {:18.8f}'.format(totalstaking))
        print('total user coins: {:18.8f}'.format(totalbalances + totalstaking))
        await ctx.send('```total balances:   {:18.8f}\ntotal staking:    {:18.8f}\ntotal user coins: {:18.8f}```'.format(
            totalbalances, totalstaking, totalbalances + totalstaking))

    @commands.command(aliases=['usertotals'])
    @commands.check(checks.is_owner)
    async def usertotal(self, ctx):
        totalbalances = 0.0
        totalstaking = 0.0
        users = mysql.get_reg_users_id()
        for user in users:
            balances = mysql.get_all_balance(int(user))
            totalbalances = round(
                totalbalances + round(float(balances['balance']), 8), 8)
            totalstaking = round(
                totalstaking + round(float(balances['staking_balance']), 8), 8)
        print('total balances:   {:18.8f}'.format(totalbalances))
        print('total staking:    {:18.8f}'.format(totalstaking))
        print('total user coins: {:18.8f}'.format(totalbalances + totalstaking))
        await ctx.send('```total balances:   {:18.8f}\ntotal staking:    {:18.8f}\ntotal user coins: {:18.8f}```'.format(
            totalbalances, totalstaking, totalbalances + totalstaking))

    @commands.command()
    @commands.check(checks.is_owner)
    async def pay_stake(self, ctx, amount: float, testing=False):
        if not testing:
            await ctx.message.delete()
        totalstaking = 0.0
        users = mysql.get_reg_users_id()
        users = [x for x in users if x not in [
            self.stakeflake, self.treasurer, self.game_id]]
        users_staking = {}
        for user in users:
            balances = mysql.get_all_balance(int(user))
            users_staking[int(user)] = float(balances['staking_balance'])
            if int(user) == self.donate:
                users_staking[int(user)] += float(balances['balance'])

        print('users_staking:\n{}'.format(users_staking))
        for user in users_staking:
            if users_staking[user] == 0.0:
                users.remove(user)
            totalstaking = round(totalstaking + round(users_staking[user], 8), 8)
        print('total staking:    {:18.8f}'.format(totalstaking))
        totalpay = 0.0
        # pay:
        for user in users:
            share = round(users_staking[user] / totalstaking, 8)
            pay = round(share * amount - 5e-09, 8)
            totalpay += pay
            if not testing:
                mysql.add_to_balance(user, pay)
            print('{} {:17.8f} {:.8f} {:17.8f}'.format(user, users_staking[user], share, pay))
        print('total pay:   {:18.8f}'.format(totalpay))
        await ctx.send('**@everyone Staking Payout:**\n```DMB staking:    {:18.8f}\ntotal payed:    {:18.8f}```'.format(
            totalstaking, totalpay))

    @commands.command()
    @commands.check(checks.is_owner)
    async def add_balance(self, ctx, amount: float, snowflake=None):
        # await ctx.message.delete()
        if not snowflake:
            snowflake = ctx.message.author.id
        mysql.give_rain(snowflake, amount)
        await ctx.send('**done**')

    @commands.command()
    @commands.check(checks.is_owner)
    async def rem_balance(self, ctx, amount: float, snowflake=None):
        # await ctx.message.delete()
        if not snowflake:
            snowflake = ctx.message.author.id
        mysql.pay_rain(snowflake, amount)
        await ctx.send('**done**')


def setup(bot):
    bot.add_cog(AdminTools(bot))
