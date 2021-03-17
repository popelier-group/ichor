from ..constants import ichor_logo
from ..arguments import Arguments

class ConfigProvider(dict):
    """
    Class to read in a config file and create a dictionary of key, val pairs
    Parameters
    ----------
    source: String
          Optional parameter to specify the config file to read
          If no source file is specified, defaults to "config.properties"
    Example
    -------
    >>config.properties
    'SYSTEM_NAME=WATER
     DETERMINE_ALF=False
     ALF=[[1,2,3],[2,1,3],[3,1,2]]'
     {'SYSTEM_NAME': 'WATER', 'DETERMINE_ALF': 'False', 'ALF': '[[1,2,3],[2,1,3],[3,1,2]]'}
    Notes
    -----
    >> If you would like to interpret the config file as literals, 'import ast' and use ast.evaluate_literal()
       when reading in the key value
       -- Undecided on whether to automatically do this or leave it for the user to specify
       -- May add function to evaluate all as literals at some point which can then be 'switched' ON/OFF
    >> Included both .properties and .yaml file types, to add more just create a function to interpret it and add
       an extra condition to the if statement in loadConfig()
    """

    def __init__(self, source=Arguments.config_file):
        self.src = source
        self.load_config()

    def load_config(self):
        if self.src.endswith(".properties"):
            self.load_properties_config()
        elif self.src.endswith(".yaml"):
            self.load_yaml_config()

    def print_key_vals(self):
        for key in self:
            print("%s:\t%s" % (key, self[key]))

    def load_file_data(self):
        global _config_read_error
        try:
            with open(self.src, "r") as finput:
                return finput.readlines()
        except IOError:
            _config_read_error = True
        return ""

    def load_properties_config(self):
        for line in self.load_file_data():
            if not line.strip().startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                self[self.cleanup_key(key)] = val.strip()

    def load_yaml_config(self):
        import yaml

        entries = yaml.load(self.load_file_data())
        if entries:
            self.update(entries)

    def cleanup_key(self, key):
        return key.strip().replace(" ", "_").upper()

    def add_key_val(self, key, val):
        self[key] = val

    def write_key_vals(self):
        with open(self.src, "w+") as f:
            f.write(ichor_logo)
            f.write("\n")
            for key in self:
                f.write("%s=%s\n" % (key, self[key]))