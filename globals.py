import pwd
import sys
import os

from dotenv import load_dotenv


####### GLOBAL CONSTANTS ############
sys.path.insert(0, os.path.dirname(__file__))
load_dotenv('.env')
SETTINGS_FILE=os.environ.get('SETTINGS_FILE')
VERSION=os.environ.get('VERSION')



############## GLOBAL FUNCTIONS ###############

UID   = 1
EUID  = 2

def owner(pid):
    '''Return username of UID of process pid'''
    for ln in open('/proc/%d/status' % pid):
        if ln.startswith('Uid:'):
            uid = int(ln.split()[UID])
            return pwd.getpwuid(uid).pw_name
