import ssdp
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time
from urlparse import urlparse
from pprint import pprint
import json
import numpy as np

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

def calculateTimeInSeconds(currentTimeString):
    currentTimeObject = time.strptime(currentTimeString,'%H:%M:%S')
    return timedelta(hours=currentTimeObject.tm_hour,
        minutes=currentTimeObject.tm_min,
        seconds=currentTimeObject.tm_sec).total_seconds()

def convertFrom12Hourto24HourTime(twelveHourTime):
    sunrisein24HourTime = datetime.strptime(twelveHourTime, '%I:%M:%S %p')
    print "sunrise in 24 hour time"
    print sunrisein24HourTime
    return sunrisein24HourTime.strftime('%H:%M:%S')

def calculateCurrenTimeOffset(sunrise):
    print "the value of sunrise is"
    print sunrise
    print "--------------------"
    sunriseInSeconds = calculateTimeInSeconds(sunrise)
    currentTimeInSeconds = calculateTimeInSeconds(datetime.utcnow().time().strftime('%H:%M:%S'))
    print "current time"
    print datetime.utcnow().time()
    print "Time Delta"
    print currentTimeInSeconds - sunriseInSeconds
    return currentTimeInSeconds - sunriseInSeconds

def calculateColorTemperature(sunriseAndSunset, timeSinceSunrise):
    daylength = sunriseAndSunset["results"]["day_length"]
    daylengthTime = time.strptime(daylength,'%H:%M:%S')
    dayLengthInSeconds = timedelta(hours=daylengthTime.tm_hour,
        minutes=daylengthTime.tm_min,
        seconds=daylengthTime.tm_sec).total_seconds()
    print dayLengthInSeconds

    print "POLYFIT"
    z = np.polyfit(np.array([0.0, float(dayLengthInSeconds/2.0), dayLengthInSeconds]),
        np.array([2700.0, 6500.0, 2700.0]), 3)
    p = np.poly1d(z)
    print p(timeSinceSunrise)

def getSunriseAndSunset():
    sunriseSunsetAPIUrl = "https://api.sunrise-sunset.org/json"
    with open('config.json') as data_file:
        configData = json.load(data_file)
        payload = {
            "lat": configData["lat"],
            "long": configData["long"]
        }
        sunriseSunsetRequestUrl = "{0}?lat={1}&lng={2}&date=today".format(sunriseSunsetAPIUrl,
            configData["lat"], configData["long"])
        sunriseAndSunset = requests.get(sunriseSunsetRequestUrl)
        print sunriseAndSunset.json()
        return json.loads(sunriseAndSunset.text)

# print getOrFindUsername()
sunriseAndSunset = getSunriseAndSunset()
timeSinceSunrise = calculateCurrenTimeOffset(convertFrom12Hourto24HourTime(sunriseAndSunset["results"]["sunrise"]))
calculateColorTemperature(sunriseAndSunset, timeSinceSunrise)
