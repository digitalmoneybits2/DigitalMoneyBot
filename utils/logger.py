import logging
import os

from logging.handlers import RotatingFileHandler

LOGPATH = 'log'


def create_logger(name, level=logging.DEBUG, steam=False, messagelog=False):
    if not os.path.exists(LOGPATH):
        os.makedirs(LOGPATH)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if messagelog:
        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(message)s',
            datefmt='%Y/%m/%d %H:%M:%S')
    else:
        file_formatter = logging.Formatter(
            fmt='%(asctime)s %(module)s %(lineno)d %(levelname)s | %(message)s',
            datefmt='%Y/%m/%d %H:%M:%S')  # %I:%M:%S %p AM|PM format
    fname = '{}/{}.log'.format(LOGPATH, str(name))
    file_handler = RotatingFileHandler(fname, 'a', 5242880, 10)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    if steam:
        steam_handler = logging.StreamHandler()
        steam_handler.setFormatter(file_formatter)
        logger.addHandler(steam_handler)
    return logger
