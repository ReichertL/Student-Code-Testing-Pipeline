import json
from pprint import pprint


class ConfigReader:

    def __init__(self):
        self.path = ""

    def read_file(self, path):
        with open(path) as configFile:
            configuration = json.load(configFile)
        pprint(configuration)
        return configuration
