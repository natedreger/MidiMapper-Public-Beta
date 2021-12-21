#! /usr/bin/python3

# logger.py

import logging
from logging.handlers import RotatingFileHandler

logFile = './logs/log.log'
logLevel = logging.DEBUG

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s(%(lineno)d) - %(message)s')
log_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024,
                                 backupCount=2, encoding=None, delay=0)
log_handler.setFormatter(log_formatter)

logs = logging.getLogger()
logs.setLevel(logLevel)
logs.addHandler(log_handler)

def loadLog():
    file = open(logFile, 'r')
    log = file.readlines()
    file.close()
    return log

def clearLog():
    file = open(logFile, 'w')
    file.write()
    file.close()

def setLogLevel(level):
    if level == "DEBUG":
        logLevel = logging.DEBUG
    elif level == "INFO":
        logLevel = logging.INFO
    elif level == "WARNING":
        logLevel = logging.WARNING
    elif level == "ERROR":
        logLevel = logging.ERROR
    logs.setLevel(logLevel)
