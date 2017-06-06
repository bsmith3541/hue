import ssdp
import requests
import xml.etree.ElementTree as ET


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
                    bridgeIP = child.text
            print "Bridge IP"
            print bridgeIP

findBridgeIP();
