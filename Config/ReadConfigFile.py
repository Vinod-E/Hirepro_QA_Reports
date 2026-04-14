import configparser
from Config import configfile


config = configparser.RawConfigParser()
config.read(configfile.CONFIG_DIR)


class ReadConfig:

    @staticmethod
    def get_web_hook_details(option):
        try:
            username = config.get('WEBHOOK', option)
            return username
        except configparser.NoSectionError:
            print("Section 'WEBHOOK' not found in the configuration file.")