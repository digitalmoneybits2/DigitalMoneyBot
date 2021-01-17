import pymysql.cursors
import warnings
from utils import parsing

config = parsing.parse_json('config.json')["mysql"]
host = config["db_host"]
try:
    port = int(config["db_port"])
except KeyError:
    port = 3306
db_user = config["db_user"]
db_pass = config["db_pass"]
db = config["db"]
connection = pymysql.connect(
    host=host,
    port=port,
    user=db_user,
    password=db_pass,
    db=db)
cursor = connection.cursor(pymysql.cursors.DictCursor)

# cursor.execute("DROP DATABASE IF EXISTS {};".format(database))
# cursor.execute("CREATE DATABASE IF NOT EXISTS {};".format(database))
# conn.commit()

# cursor.execute("USE {};".format(database))


def run():
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')

        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            snowflake_pk BIGINT UNSIGNED NOT NULL,
            balance DECIMAL(20, 8) NOT NULL,
            balance_unconfirmed DECIMAL(20, 8) NOT NULL,
            staking_balance DECIMAL(20, 8) NOT NULL,
            address VARCHAR(34) DEFAULT NULL,
            last_msg_time DATETIME,
            rain_last_msg_time DATETIME,
            rain_msg_count INT NOT NULL DEFAULT 0,
            PRIMARY KEY (snowflake_pk)
            )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS deposit (
            snowflake_fk BIGINT UNSIGNED NOT NULL,
            amount DECIMAL(20, 8) NOT NULL,
            txid VARCHAR(256) NOT NULL,
            status VARCHAR(20) NOT NULL,
            FOREIGN KEY (snowflake_fk) REFERENCES users(snowflake_pk)
            )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS withdrawal (
            snowflake_fk BIGINT UNSIGNED NOT NULL,
            amount DECIMAL(20, 8) NOT NULL,
            txid VARCHAR(256) NOT NULL,
            FOREIGN KEY (snowflake_fk) REFERENCES users(snowflake_pk)
            )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS tip (
            snowflake_from_fk BIGINT UNSIGNED NOT NULL,
            snowflake_to_fk BIGINT UNSIGNED NOT NULL,
            amount DECIMAL(20, 8) NOT NULL,
            FOREIGN KEY (snowflake_from_fk) REFERENCES users(snowflake_pk),
            FOREIGN KEY (snowflake_to_fk) REFERENCES users(snowflake_pk)
            )""")

