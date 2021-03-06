# DigitalMoneyBot
# DMB-Tip-Bot


These files are intended to function as a multi-functional tipbot for DigitalMoneyBits (DMB).

# Requirements
* discord.py installed
* Python 3.6+
* A MySQL database
* The DMB wallet w/ RPC enabled.

# Functions
* Display general wallet information
* Display individual user balances
* Store user balance information in database
* Generate new deposit addresses for users
* Automatically add users to database
* Allow users to withdraw coins from the wallet with respect to how many coins they have in the DB

# Instructions
These instructions were used to create a working bot in March 2018.
Once a VPS is obtained, follow these instructions.
## mySQL
These instructions will help you install and setup a mySQL database if not already installed
### Install mySQL
```
sudo apt install mysql-server
```
When prompted, set up a password for root.
### Configure mySQL Security
```
mysql_secure_installation
```
Press "Y" and ENTER to accept all the questions, with the exception of the one that asks if you'd like to change the root password.
### Verify mySQL is Running
```
systemctl status mysql.service
```
You should see a status message that says "active (running)".
## Update Python
Python should be updated to version 3.6 because version 3.5 is not compatible with some libraries
```
sudo apt update
sudo apt install python3
```
## Install Python's pip
Python's pip is a useful tool used to install python libraries
```
sudo apt install python3-pip
```
or
```
wget https://bootstrap.pypa.io/get-pip.py
sudo python3 get-pip.py
```

## Install Discord Library
Install the discord library used for the bot
```
python3 -m pip install -U discord.py
```

## Install PyMySQL Library
```
sudo apt install python3-pymysql
```
or
```
pip install PyMySQL
```

## Clone tipbot repository
```
git clone https://github.com/digitalmoneybits2/DigitalMoneyBot
```

## Configuration

Rename config-sample.json to config.json
Configure config.json

## Run bot
```
cd DigitalMoneyBot-main

python3 digitalmoneybot.py
```

## Please donate some if you use this bot.. Thanks !
BTC: 1LGvSbXGersy6aoMGd2gLhDwLEANABnusJ
