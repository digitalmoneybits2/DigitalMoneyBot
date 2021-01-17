import pymysql.cursors
from utils import parsing
from utils import rpc_module
from utils import helpers
from decimal import Decimal
import datetime

rpc = rpc_module.Rpc()


class Mysql:
    """
    Singleton helper for complex database methods
    """
    instance = None

    def __init__(self):
        if not Mysql.instance:
            Mysql.instance = Mysql.__Mysql()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    class __Mysql:
        def __init__(self):
            config = parsing.parse_json('config.json')["mysql"]
            self.__host = config["db_host"]
            self.__port = int(config.get("db_port", 3306))
            self.__db_user = config["db_user"]
            self.__db_pass = config["db_pass"]
            self.__db = config["db"]
            self.__connected = 1
            self.__setup_connection()
            self.txfee = parsing.parse_json('config.json')["txfee"]
            self.treasurer = parsing.parse_json('config.json')["treasurer"]
            self.stake_bal = parsing.parse_json('config.json')["stake_bal"]
            self.donation = parsing.parse_json('config.json')["donation"]
            self.game_bal = parsing.parse_json('config.json')["game_bal"]
            self.stake_pay = parsing.parse_json('config.json')["stake_pay"]
            self.MIN_CONFIRMATIONS_FOR_DEPOSIT = parsing.parse_json('config.json')["MIN_CONFIRMATIONS_FOR_DEPOSIT"]
            # "treasurer": 100000000000000010,
            # "stake_bal": 100000000000000011,
            # "donation": 100000000000000012,
            # "game_bal": 100000000000000013,
            # "stake_pay": 10000000000009999,

        def __setup_connection(self):
            self.__connection = pymysql.connect(
                host=self.__host,
                port=self.__port,
                user=self.__db_user,
                password=self.__db_pass,
                db=self.__db)

        def __setup_cursor(self, cur_type):
            # ping the server and reset the connection if it is down
            self.__connection.ping(True)
            return self.__connection.cursor(cur_type)

# region User
        def make_user(self, snowflake):
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "INSERT INTO users (snowflake_pk, balance, balance_unconfirmed, staking_balance) VALUES(%s, %s, %s, %s)"
            cursor.execute(to_exec, (str(snowflake), '0', '0', '0'))
            cursor.close()
            self.__connection.commit()

        def check_for_user(self, snowflake):
            """
            Checks for a new user (NO LONGER CREATES A NEW USER - THAT IS HANDLED BY bot.py)
            """
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_pk FROM users WHERE snowflake_pk LIKE %s"
            cursor.execute(to_exec, (str(snowflake)))
            result_set = cursor.fetchone()
            cursor.close()
            return result_set

        def messages_user(self, snowflake):
            """
            Checks for a new user (NO LONGER CREATES A NEW USER - THAT IS HANDLED BY bot.py)
            """
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_pk, last_msg_time, rain_last_msg_time, rain_msg_count FROM users WHERE snowflake_pk LIKE %s"
            cursor.execute(to_exec, (str(snowflake)))
            result_set = cursor.fetchone()
            cursor.close()
            return result_set

        def register_user(self, snowflake):
            """
            Registers a new user
            """
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_pk, address, balance, balance_unconfirmed, staking_balance, last_msg_time, rain_last_msg_time, rain_msg_count FROM users WHERE snowflake_pk LIKE %s"
            cursor.execute(to_exec, (str(snowflake)))
            result_set = cursor.fetchone()
            cursor.close()
            if result_set is None:
                # address = rpc.getnewaddress(str(snowflake))
                self.make_user(snowflake)

        def new_address(self, snowflake):
            address = rpc.getnewaddress(str(snowflake))
            print('address:', address)
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = """
                UPDATE users
                SET address = "{:s}"
                WHERE snowflake_pk = {:s}
                """
            print('to_exec:', to_exec.format(str(address), str(snowflake)))
            cursor.execute(to_exec.format(str(address), str(snowflake)))
            print('execute:', )
            print('execute done')
            cursor.close()
            self.__connection.commit()
            return str(address)

        def get_user(self, snowflake):
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT balance, balance_unconfirmed, staking_balance, address FROM users WHERE snowflake_pk LIKE %s"
            cursor.execute(to_exec, (str(snowflake)))
            result_set = cursor.fetchone()
            cursor.close()
            return result_set

        # TODO
        def get_staking_user(self, snowflake):
            # print('get_staking_user', snowflake, self.stake_bal)
            if snowflake == self.stake_bal:
                cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
                to_exec = "SELECT snowflake_pk, balance, balance_unconfirmed FROM users WHERE snowflake_pk LIKE %s"
                cursor.execute(to_exec, (str(snowflake)))
                result_set = cursor.fetchone()
                cursor.close()
                return result_set
            else:
                return None

        def get_all_balance(self, snowflake, check_update=False):
            if check_update:
                self.check_for_updated_balance(snowflake)
            result_set = self.get_user(snowflake)
            return result_set

        def get_user_balance(self, snowflake, check_update=False):
            if check_update:
                self.check_for_updated_balance(snowflake)
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT balance FROM users WHERE snowflake_pk LIKE %s"
            cursor.execute(to_exec, (str(snowflake)))
            result_set = cursor.fetchone()
            cursor.close()
            return result_set.get("balance")

        def get_user_unconfirmed_balance(self, snowflake):
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT balance_unconfirmed FROM users WHERE snowflake_pk LIKE %s"
            cursor.execute(to_exec, (str(snowflake)))
            result_set = cursor.fetchone()
            cursor.close()
            return result_set.get("balance_unconfirmed")

        def get_user_staking_balance(self, snowflake):
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT staking_balance FROM users WHERE snowflake_pk LIKE %s"
            cursor.execute(to_exec, (str(snowflake)))
            result_set = cursor.fetchone()
            cursor.close()
            return result_set.get("staking_balance")

        def get_user_by_address(self, address):
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_pk FROM users WHERE address LIKE %s"
            cursor.execute(to_exec, (str(address)))
            result_set = cursor.fetchone()
            cursor.close()
            return result_set.get('snowflake_pk')

        def get_address(self, snowflake):
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT address FROM users WHERE snowflake_pk LIKE %s"
            cursor.execute(to_exec, (str(snowflake)))
            result_set = cursor.fetchone()
            cursor.close()
            return result_set.get("address")

# region Balance
        def set_balance(self, snowflake, to, is_unconfirmed=False, is_staking=False):
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            if is_unconfirmed:
                to_exec = "UPDATE users SET balance_unconfirmed = %s WHERE snowflake_pk = %s"
            elif is_staking:
                to_exec = "UPDATE users SET staking_balance = %s WHERE snowflake_pk = %s"
            else:
                to_exec = "UPDATE users SET balance = %s WHERE snowflake_pk = %s"
            cursor.execute(to_exec, (to, str(snowflake),))
            cursor.close()
            self.__connection.commit()

        def add_to_balance(self, snowflake, amount):
            self.set_balance(snowflake, self.get_user_balance(
                snowflake) + Decimal(amount))

        def add_to_staking_balance(self, snowflake, amount):
            self.set_balance(snowflake, Decimal(self.get_user_staking_balance(
                snowflake)) + Decimal(amount), is_staking=True)

        def remove_from_staking_balance(self, snowflake, amount):
            self.set_balance(snowflake, Decimal(self.get_user_staking_balance(
                snowflake)) - Decimal(amount), is_staking=True)

        def remove_from_balance(self, snowflake, amount):
            self.set_balance(snowflake, self.get_user_balance(
                snowflake) - Decimal(amount))

        def add_to_balance_unconfirmed(self, snowflake, amount):
            balance_unconfirmed = self.get_user_unconfirmed_balance(snowflake)
            self.set_balance(
                snowflake, balance_unconfirmed + Decimal(amount),
                is_unconfirmed=True)

        def remove_from_balance_unconfirmed(self, snowflake, amount):
            balance_unconfirmed = self.get_user_unconfirmed_balance(snowflake)
            self.set_balance(
                snowflake, balance_unconfirmed - Decimal(amount),
                is_unconfirmed=True)

        def check_for_updated_balance(self, snowflake):
            """
            Uses RPC to get the latest transactions and updates
            the user balances accordingly

            This code is based off of parse_incoming_transactions in
            https://github.com/tehranifar/ZTipBot/blob/master/src/wallet.py
            """
            transaction_list = rpc.listtransactions(str(snowflake), 100)
            for tx in transaction_list:
                if tx["category"] != "receive":
                    continue
                txid = tx["txid"]
                amount = tx["amount"]
                confirmations = tx["confirmations"]
                user = tx["account"]
                if user != str(snowflake):
                    continue

                status = self.get_transaction_status_by_txid(txid)
                if status == "DOESNT_EXIST" and confirmations >= self.MIN_CONFIRMATIONS_FOR_DEPOSIT:
                    print("NEW DEPOSIT {}".format(txid))
                    self.add_to_balance(user, amount)
                    self.add_deposit(user, amount, txid, 'CONFIRMED')
                elif status == "DOESNT_EXIST" and confirmations < self.MIN_CONFIRMATIONS_FOR_DEPOSIT:
                    self.add_deposit(user, amount, txid, 'UNCONFIRMED')
                    self.add_to_balance_unconfirmed(user, amount)
                elif status == "UNCONFIRMED" and confirmations >= self.MIN_CONFIRMATIONS_FOR_DEPOSIT:
                    self.add_to_balance(user, amount)
                    self.remove_from_balance_unconfirmed(snowflake, amount)
                    self.confirm_deposit(txid)

        def get_transaction_status_by_txid(self, txid):
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT status FROM deposit WHERE txid = %s"
            cursor.execute(to_exec, (txid,))
            result_set = cursor.fetchone()
            cursor.close()
            if not result_set:
                return "DOESNT_EXIST"
            return result_set["status"]
# endregion

# region Deposit/Withdraw/Tip/Soak
        def add_deposit(self, snowflake, amount, txid, status):
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "INSERT INTO deposit(snowflake_fk, amount, txid, status) VALUES(%s, %s, %s, %s)"
            cursor.execute(to_exec, (str(snowflake), '{:.8f}'.format(amount), str(txid), str(status)))
            cursor.close()
            self.__connection.commit()

        def confirm_deposit(self, txid):
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "UPDATE deposit SET status = %s WHERE txid = %s"
            cursor.execute(to_exec, ('CONFIRMED', str(txid)))
            cursor.close()
            self.__connection.commit()

        def create_withdrawal(self, snowflake, address, amount):
            txfee = self.txfee
            amount = float(amount)
            res = rpc.settxfee(txfee)
            print('res =', res)
            if res is False:
                return None
            txid = rpc.sendtoaddress(address, round(amount - txfee, 8))
            print('txid =', txid)
            if not txid:
                return None
            self.remove_from_balance(snowflake, amount)
            return self.add_withdrawal(snowflake, amount, txid)

        def add_withdrawal(self, snowflake, amount, txid):
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "INSERT INTO withdrawal(snowflake_fk, amount, txid) VALUES(%s, %s, %s)"
            cursor.execute(to_exec, (str(snowflake), '{:.8f}'.format(amount), str(txid)))
            cursor.close()
            self.__connection.commit()
            return txid

        def add_tip(self, snowflake_from_fk, snowflake_to_fk, amount):
            self.remove_from_balance(snowflake_from_fk, amount)
            self.add_to_balance(snowflake_to_fk, amount)
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            tip_exec = "INSERT INTO tip(snowflake_from_fk, snowflake_to_fk, amount) VALUES(%s, %s, %s)"
            cursor.execute(tip_exec, (str(snowflake_from_fk), str(snowflake_to_fk), '{:.8f}'.format(amount)))
            cursor.close()
            self.__connection.commit()

        def add_rain(self, snowflake_from_fk, snowflake_to_fk, amount):
            self.remove_from_balance(snowflake_from_fk, amount)
            self.add_to_balance(snowflake_to_fk, amount)

        def pay_rain(self, snowflake_from_fk, amount):
            self.remove_from_balance(snowflake_from_fk, amount)

        def give_rain(self, snowflake_to_fk, amount):
            self.add_to_balance(snowflake_to_fk, amount)
# endregion

# region Last message
        def user_last_msg_check(self, user_id, content, is_private):
            # if the user is not registered
            if self.get_user(user_id) is None:
                return False
            else:
                user = self.messages_user(user_id)
                # if user is missing return false
                if user is None:
                    return False
                # Get difference in seconds between now and last msg. If it is less than 1s, return False
                if user["last_msg_time"] is not None:
                    since_last_msg_s = (datetime.datetime.utcnow() - user["last_msg_time"]).total_seconds()
                    if since_last_msg_s < 1:
                        return False
                else:
                    since_last_msg_s = None
                # Do not process the messages made in DM
                if not is_private:
                    self.update_last_msg(user, since_last_msg_s, content)
                return True

        def update_last_msg(self, user, last_msg_time, content):
            rain_config = parsing.parse_json('config.json')['rain']
            min_num_words_required = rain_config["min_num_words_required"]
            delay_between_messages_required_s = rain_config["delay_between_messages_required_s"]
            user_activity_required_m = rain_config["user_activity_required_m"]
            content_adjusted = helpers.unicode_strip(content)
            words = content_adjusted.split(' ')
            adjusted_count = 0
            prev_len = 0
            for word in words:
                word = word.strip()
                cur_len = len(word)
                if cur_len > 0:
                    if word.startswith(":") and word.endswith(":"):
                        continue
                    if prev_len == 0:
                        prev_len = cur_len
                        adjusted_count += 1
                    else:
                        res = prev_len % cur_len
                        prev_len = cur_len
                        if res != 0:
                            adjusted_count += 1
                if adjusted_count >= min_num_words_required:
                    break

            if last_msg_time is None:
                user["rain_msg_count"] = 0
            else:
                if last_msg_time >= (user_activity_required_m * 60):
                    user["rain_msg_count"] = 0

            is_accepted_delay_between_messages = False
            if user["rain_last_msg_time"] is None:
                is_accepted_delay_between_messages = True
            elif (datetime.datetime.utcnow() - user["rain_last_msg_time"]).total_seconds() > delay_between_messages_required_s:
                is_accepted_delay_between_messages = True

            if adjusted_count >= min_num_words_required and is_accepted_delay_between_messages:
                user["rain_msg_count"] += 1
                user["rain_last_msg_time"] = datetime.datetime.utcnow()
            user["last_msg_time"] = datetime.datetime.utcnow()

            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "UPDATE users SET last_msg_time = %s, rain_last_msg_time = %s, rain_msg_count = %s WHERE snowflake_pk = %s"
            cursor.execute(to_exec, (user["last_msg_time"], user["rain_last_msg_time"], user["rain_msg_count"], user["snowflake_pk"]))

            cursor.close()
            self.__connection.commit()
# endregion

# region Active users

        def get_active_users_id(self, user_activity_since_minutes, is_rain_activity):
            since_ts = datetime.datetime.utcnow() - datetime.timedelta(minutes=user_activity_since_minutes)
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            if not is_rain_activity:
                to_exec = "SELECT snowflake_pk FROM users WHERE last_msg_time > %s ORDER BY snowflake_pk"
            else:
                to_exec = "SELECT snowflake_pk FROM users WHERE rain_last_msg_time > %s ORDER BY snowflake_pk"
            cursor.execute(to_exec, (str(since_ts)))
            users = cursor.fetchall()
            cursor.close()
            return_ids = []
            for user in users:
                return_ids.append(user["snowflake_pk"])
            return return_ids

# endregion

# region Registered users

        def get_reg_users_id(self):
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_pk FROM users ORDER BY snowflake_pk"
            cursor.execute(to_exec)
            users = cursor.fetchall()
            cursor.close()
            return_reg_ids = []
            for user in users:
                return_reg_ids.append(user["snowflake_pk"])
            return return_reg_ids
# endregion

# transaction history related calls - deposits
        # return a list of txids of a users deposit transactions
        def get_deposit_list(self, status):
            # database search
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT txid FROM deposit WHERE status = %s"
            cursor.execute(to_exec, str(status))
            deposits = cursor.fetchall()
            cursor.close()
            return_deptxid_list = []
            for transaction in deposits:
                return_deptxid_list.append(transaction["txid"])
            return return_deptxid_list

        # return a list of txids of a users deposit transactions
        def get_deposit_list_byuser(self, snowflake):
            # database search
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT txid FROM deposit WHERE snowflake_fk = %s"
            cursor.execute(to_exec, str(snowflake))
            deposits = cursor.fetchall()
            cursor.close()
            return_deptxid_list = []
            for transaction in deposits:
                return_deptxid_list.append(transaction["txid"])
            return return_deptxid_list

        # get deposit info from txid
        def get_deposit_amount(self, txid):
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT amount FROM deposit WHERE txid = %s"
            cursor.execute(to_exec, str(txid))
            deposit = cursor.fetchone()
            cursor.close()
            return deposit["amount"]
# endregion

# transaction history related calls - withdrawals
        # return a list of txids of a users withdrawal transactions
        def get_withdrawal_list_byuser(self, snowflake):
            # database search
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT txid FROM withdrawal WHERE snowflake_fk = %s"
            cursor.execute(to_exec, str(snowflake))
            deposits = cursor.fetchall()
            cursor.close()
            return_wittxid_list = []
            for transaction in deposits:
                return_wittxid_list.append(transaction["txid"])
            return return_wittxid_list

        # get deposit info from txid
        def get_withdrawal_amount(self, txid):
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT amount FROM withdrawal WHERE txid = %s"
            cursor.execute(to_exec, str(txid))
            withdrawal = cursor.fetchone()
            cursor.close()
            return withdrawal["amount"]
# endregion

# tip information calls
        def get_tip_amounts_from_id(self, snowflake, snowflake_to):
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_to_fk, amount FROM tip WHERE snowflake_from_fk = %s"
            cursor.execute(to_exec, str(snowflake))
            user_tips = cursor.fetchall()
            cursor.close()
            return_tip_amounts = []
            for tips in user_tips:
                if int(tips["snowflake_to_fk"]) == int(snowflake_to):
                    return_tip_amounts.append(tips["amount"])
            return return_tip_amounts

        def get_total_tip_amounts_from_id(self, snowflake):
            donate_accounts = [int(self.treasurer), int(self.donation), int(self.stake_pay), int(self.game_bal)]
            cursor = self.__setup_cursor(pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_to_fk, amount FROM tip WHERE snowflake_from_fk = %s"
            cursor.execute(to_exec, str(snowflake))
            user_tips = cursor.fetchall()
            cursor.close()
            return_tip_amounts = []
            for tips in user_tips:
                if int(tips["snowflake_to_fk"]) in donate_accounts:
                    return_tip_amounts.append(tips["amount"])
            return return_tip_amounts
# end region
