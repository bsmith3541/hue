import ssdp
import requests
import xml.etree.ElementTree as ET
from urlparse import urlparse
from pprint import pprint
import json

def findBridgeIP():
    devicesOnNetwork = ssdp.discover("IpBridge");
    for device in devicesOnNetwork:
        print device
        url = device.location
        response = requests.get(url)
        if 'Philips' in response.text:
            root = ET.fromstring(response.text)
            for child in root:
                if 'URLBase' in child.tag:
                    bridgeHost = urlparse(child.text).hostname
                    print "Bridge IP"
                    print bridgeHost
                    return bridgeHost

def getOrFindUsername():
    bridgeIP = findBridgeIP();
    bridgeAPI = "http://{0}/api".format(bridgeIP)
    with open('config.json') as data_file:
        configData = json.load(data_file)
        print "Config: Username"
        if not configData["username"]:
            payload = { "devicetype" : "FluxHue#Server" }
            username = requests.post(bridgeAPI, json=payload)
            print "--We just got a username--"
            return username.text
        else:
            print "--We already have a username--"
            return configData["username"]

print getOrFindUsername()
