#! /usr/bin/python3

# logger.py

import logging
from logging.handlers import RotatingFileHandler

logFile = 'log.log'

logging.basicConfig(filename=logFile, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)


# log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
#
#
# my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024,
#                                  backupCount=2, encoding=None, delay=0)
# my_handler.setFormatter(log_formatter)
# my_handler.setLevel(logging.INFO)
#
# logger = logging.getLogger('root')
# logger.setLevel(logging.INFO)
#
# logger.addHandler(my_handler)


def loadLog():
    file = open(logFile, 'r')
    log = file.readlines()
    file.close()
    return log
