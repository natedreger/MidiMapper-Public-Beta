#! /usr/bin/python3

# logger.py

import logging
import json
from logging.handlers import RotatingFileHandler

logFile = './logs/log.log'
logLevel = logging.DEBUG
logLevelName = 'DEBUG'

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s.py - %(funcName)s(%(lineno)d) - %(message)s')
log_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024,
                                 backupCount=2, encoding=None, delay=0)
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logLevel)

logs = logging.getLogger('root')
logs.setLevel(logLevel)
logs.addHandler(log_handler)

def loadLog():
    file = open(logFile, 'r')
    log = file.readlines()
    file.close()
    return log

def clearLog():
    file = open(logFile, 'w')
    file.write('')
    file.close()

# NOTSET=0, DEBUG=10, INFO=20, WARN=30, ERROR=40, and CRITICAL=50

def setLogLevel(level):
    global logLevel, logLevelName
    level = int(level)
    if level == 0:
        logLevel = logging.NOTSET
        logLevelName = 'NOTSET'
    elif level == 10:
        logLevel = logging.DEBUG
        logLevelName = 'DEBUG'
    elif level == 20:
        logLevel = logging.INFO
        logLevelName = 'INFO'
    elif level == 30:
        logLevel = logging.WARN
        logLevelName = 'WARN'
    elif level == 40:
        logLevel = logging.ERROR
        logLevelName = 'ERROR'
    elif level == 50:
        logLevel = logging.CRITICAL
        logLevelName = 'CRITICAL'
    logs.setLevel(logLevel)
    log_handler.setLevel(logLevel)
    logs.critical(f'Log Level changed to {logLevel}: {logLevelName}')

def getLogLevel():
    return json.dumps({'logLevel':logLevel, 'logLevelName':logLevelName})
