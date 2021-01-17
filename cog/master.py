from discord.ext import commands
from utils import rpc_module, mysql_module

# result_set = database response with parameters from query
# db_bal = nomenclature for result_set["balance"]
# snowflake = snowflake from message context, identical to user in database
# wallet_bal = nomenclature for wallet reponse

rpc = rpc_module.Rpc()
mysql = mysql_module.Mysql()


class Master(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Master(bot))
