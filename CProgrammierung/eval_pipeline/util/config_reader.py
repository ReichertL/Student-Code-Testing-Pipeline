import json

"""
Reads config files in json format.
"""

class ConfigReader:

    def __init__(self):
        self.path = ""

    def read_file(self, path):
        """
        Reads config file.
        Parameters:
            path (string):path to json file
            
        Returns: 
            configuration (json) 
        
        """
        with open(path) as configFile:
            configuration = json.load(configFile)
        return configuration
