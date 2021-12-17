#! /usr/bin/python3

# logger.py

import logging

logfile = 'log.log'
logging.basicConfig(filename=logfile, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
