import yaml
from typing import List, Tuple, Dict

def readConfig(filename):
    with open(filename, 'r') as f:
        config = yaml.safe_load(f)
    return config

def createServernamePortTopicListDict(config) -> List[Dict]:
    servernamePortTopicList = []
    for name in config:
        ip = config[name]['ip']
        ports = list(config[name].keys())
        # Remove the ip key
        ports.remove('ip')
        for port in ports:
            if config[name][port]['topics'] is None:
                dataType = config[name][port]['DataType']
                updateRate = config[name][port].get('UpdateRate', 3)
                servernamePortTopicList.append({'name': name, 'port': port, 'topic': None, 'dataType': dataType, 'ip': ip, 'UpdateRate': updateRate})
            else:
                for topic in config[name][port]['topics']:
                    dataType = config[name][port]['topics'][topic]['DataType']
                    updateRate = config[name][port]['topics'][topic].get('UpdateRate', 3)
                    servernamePortTopicList.append({'name': name, 'port': port, 'topic': topic, 'dataType': dataType, 'ip': ip, 'UpdateRate': updateRate})
    return tuple(servernamePortTopicList)

def createHumanReadableNames(config) -> List[Tuple[str, dict]]:
    names = []
    for item in config:
        name = item.get('name')
        port = item.get('port')
        ip = item.get('ip')
        topic = item.get('topic')
        updateRate = item.get('UpdateRate')
        if topic is None:
            names.append((f"/{name}/{port}", {'ip': ip, 'port': port, 'topic': None, 'UpdateRate': updateRate}))
        else:
            names.append((f"/{name}/{port}/{topic}", {'ip': ip, 'port': port, 'topic': topic, 'UpdateRate': updateRate}))
    return names

def validateConfig(config):
    return True
    # Check that the config is a dictionary
    if not isinstance(config, dict):
        raise ValueError('Config must be a dictionary')
    # Check that each key in the config is a string
    for key in config.keys():
        if not isinstance(key, str):
            raise ValueError('Config keys must be strings')
    # Walk the config and check that it follows the schema above
    for key, value in config.items():
        # Check that the value is a dictionary
        if not isinstance(value, dict):
            raise ValueError('Config values must be dictionaries')
        # Check that the dictionary has an ip key
        if 'ip' not in value:
            raise ValueError('Config values must have an ip key')
        # Check that the ip is a string
        if not isinstance(value['ip'], str):
            raise ValueError('Config values ip key must be a string')
        # Check that the dictionary has an APortNumber key
        if 'APortNumber' not in value:
            raise ValueError('Config values must have an APortNumber key')
        # Check that the APortNumber exists
        # TODO: Check that the APortNumber is an integer
    return True