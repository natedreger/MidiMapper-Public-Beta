with open("database/ta.config", 'w') as config_file:
    json.dump(configs, config_file)
    print(configs['title'], print(values3['appname']))


with open("database/ta.config", 'r') as config_file:
    configs = json.load(config_file)
    print(configs['title'], print(values3['appname']))

class DataManager(object):
    def __init__(self):
        self.configs = ""
        logging.info("DatMan: Init")

        try:
            with open("database/ta.config") as config:
                self.configs = json.load(config)

        except:
            Sg.PopupOK("You are either missing or misconfigured\nthe config file ("
                                                    "database/ta.config)\n JSON "
                                                    "Format")

            logging.error("DatMan: Quitting due to issue with ta.config")
            quit()

    def save_configs(self):
        testername = configWindow.FindElement('testername')
        browsertype = configWindow.FindElement('browsertype')
        appuri = configWindow.FindElement('appuri')
        appname = configWindow.FindElement('appname')
        # emailfrom = configWindow.FindElement('emailfrom')
        # emailto = configWindow.FindElement('emailto')
        # emailusername = configWindow.FindElement('emailusername')
        # emailpassword = configWindow.FindElement('emailpassword')
        databasecheck = configWindow.FindElement('databasecheck')
        emailcheck = configWindow.FindElement('emailcheck')
        dbhost = configWindow.FindElement('dbhost')
        dbip = configWindow.FindElement('dbip')
        dbun = configWindow.FindElement('dbun')
        dbpw = configWindow.FindElement('dbpw')
        dbport = configWindow.FindElement('dbport')
        repositorypath = configWindow.FindElement('repositorypath')
        sideload = configWindow.FindElement('sideload')


        self.configs['platform'] = str(values3['browsertype'])
        self.configs['url'] = values3['appuri']
        self.configs['title'] = str(values3['appname'])
        self.configs['engineer'] = values3['testername']
        self.configs['repository'] = values3['repositorypath']

        # database
        self.configs['database_ip'] = values3['dbip']
        self.configs['database_port'] = values3['dbport']
        self.configs['database_name'] = values3['dbhost']
        self.configs['database_username'] = values3['dbun']
        self.configs['database_password'] = values3['dbpw']

        # email
        # self.configs['email_from'] = values3['emailfrom']
        # self.configs['email_to'] = values3['emailto']
        # self.configs['email_username'] = values3['emailusername']
        # self.configs['email_password'] = values3['emailpassword']

        # checkboxes
        self.configs['sql'] = values3['databasecheck']
        # SQL database
        self.configs['sl'] = values3['sideload']  # sideload mods
        # usage
        self.configs['email_check'] = values3['emailcheck']

        with open("database/ta.config", 'w') as config_file:
            json.dump(self.configs, config_file)
            # print(self.configs['title'], print(values3['appname']))
        with open("database/ta.config", 'r') as config_file:
            self.configs = json.load(config_file)
            # print(self.configs['title'], print(values3['appname']))

        logging.info("DatMan: Saved Configs Successfully")
        # return True


        # logging.warning("DatMan: Issue saving configs")
        # Sg.PopupOK("Issue saving configs")
        # return False

    def load_configs(self):
        logging.info("Config: Pressed Load")
        self.testername = configWindow.FindElement('testername')
        self.browsertype = configWindow.FindElement('browsertype')
        self.appuri = configWindow.FindElement('appuri')
        self.appname = configWindow.FindElement('appname')
        # self.emailfrom = configWindow.FindElement('emailfrom')
        # self.emailto = configWindow.FindElement('emailto')
        # .emailusername = configWindow.FindElement('emailusername')
        # self.emailpassword = configWindow.FindElement('emailpassword')
        self.databasecheck = configWindow.FindElement('databasecheck')
        self.emailcheck = configWindow.FindElement('emailcheck')
        self.dbhost = configWindow.FindElement('dbhost')
        self.dbip = configWindow.FindElement('dbip')
        self.dbun = configWindow.FindElement('dbun')
        self.dbpw = configWindow.FindElement('dbpw')
        self.dbport = configWindow.FindElement('dbport')
        self.repositorypath = configWindow.FindElement('repositorypath')
        self.sideload = configWindow.FindElement('sideload')


        # MAIN SETTINGS
        self.browsertype.Update(self.configs['platform'])
        self.appuri.Update(self.configs['url'])
        self.appname.Update(self.configs['title'])
        self.testername.Update(self.configs['engineer'])

        # EMAIL SETTINGS
        # self.emailto.Update(self.configs['email_to'])
        # self.emailfrom.Update(self.configs['email_from'])
        # self.emailusername.Update(self.configs['email_username'])

        # CHECKBOX SETTINGS
        self.databasecheck.Update(self.configs['sql'])
        self.sideload.Update(self.configs['sl'])
        self.emailcheck.Update(self.configs['email_check'])

        # DATABASE SETTINGS
        self.dbhost.Update(self.configs['database_name'])
        self.dbip.Update(self.configs['database_ip'])
        self.dbun.Update(self.configs['database_username'])
        self.dbport.Update(self.configs['database_port'])

        # REPOSITORY SETTINGS
        self.repositorypath.Update(self.configs['repository'])

        # Passwords can optionally be enabled (Insecure):
        # emailpassword.Update(configs['email_password'])
        # dbpw.Update(configs['database_password'])

        # Now make available to the rest of the app:

        self.browsertype = self.configs['platform']
        self.appuri = self.configs['url']
        self.appname = self.configs['title']
        self.testername = self.configs['engineer']

        # EMAIL SETTINGS
        # self.emailto = self.configs['email_to']
        # self.emailfrom = self.configs['email_from']
        # self.emailusername = self.configs['email_username']

        # CHECKBOX SETTINGS
        self.databasecheck = self.configs['sql']
        self.sideload = self.configs['sl']
        self.emailcheck = self.configs['email_check']

        # DATABASE SETTINGS
        self.dbhost = self.configs['database_name']
        self.dbip = self.configs['database_ip']
        self.dbun = self.configs['database_username']
        self.dbport = self.configs['database_port']

        # REPOSITORY SETTINGS
        self.repositorypath = self.configs['repository']

        logging.info("DatMan: Updated Configs Successfully")
        # return True


        # logging.warning("DatMan: Issue loading from Config")
        # Sg.PopupOK("Issue loading from Config")
        # return False

data_man = DataManager()
data_man.load_config()
data_man.save_config()
