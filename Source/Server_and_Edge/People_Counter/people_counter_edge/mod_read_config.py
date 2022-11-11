import json
import yaml
import os.path

#fucntion reads a configfile in YAML or JSON Format an returns is as a dictionary
def get_server_config(config_file="server_config.yaml"):

    #Check if Config file exists
    if os.path.isfile(config_file):
        #get the filetype (yaml or json)
        config_type = config_file.split(".")[-1]
        
        #handling for yaml-config-files
        if config_type.lower() == "yaml":
            try:
                yaml_config = open(config_file,'r')
                yaml_server_config = yaml.full_load(yaml_config)
                #return config
                return yaml_server_config
            except:
                print("ERROR: \t{} invalid Yaml-file".format)
                return "error in yaml handler"
            finally:
                yaml_config.close()

        #handling for json-config-files
        elif config_type.lower() == "json":
            try:
                json_config = open(config_file,'r')
                json_server_config = json.load(json_config)
                #return config
                return json_server_config
            except:
                print("ERROR: \t{} invalid JSON-file".format)
                return "error in json handler"
            finally:
                json_config.close()

    #handling if config-file does not exists
    else:
        print("ERROR:\tFile {} not found or does not exist!".format(config_file))
        return "error in file handler"

if __name__ == "__main__":

    #some testing
    json_config = get_server_config("server_config.json")
    yaml_config = get_server_config("server_config.yaml")

    MQTT_SUBS = []

    for sub in yaml_config['mqtt_config']['mqtt_subs']:
        MQTT_SUBS.append((sub,0))
    pass
    