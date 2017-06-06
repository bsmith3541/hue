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

def convertTimeStringToSeconds(currentTimeString):
    currentTimeObject = time.strptime(currentTimeString,'%H:%M:%S')
    return timedelta(hours=currentTimeObject.tm_hour,
        minutes=currentTimeObject.tm_min,
        seconds=currentTimeObject.tm_sec).total_seconds()

def convertFrom12Hourto24HourTime(twelveHourTime):
    sunrisein24HourTime = datetime.strptime(twelveHourTime, '%I:%M:%S %p')
    return sunrisein24HourTime.strftime('%H:%M:%S')

def calculateCurrenTimeOffset(sunrise):
    sunriseInSeconds = convertTimeStringToSeconds(sunrise)
    currentTimeInSeconds = convertTimeStringToSeconds(datetime.utcnow().time().strftime('%H:%M:%S'))
    timeSinceSunrise = currentTimeInSeconds - sunriseInSeconds
    print "Time Since Sunrise"
    print timeSinceSunrise
    return timeSinceSunrise

def calculateBrightness(daylength, timeSinceSunrise):
    dayLengthInSeconds = convertTimeStringToSeconds(daylength)

    z = np.polyfit(np.array([0.0, float(dayLengthInSeconds/2.0), dayLengthInSeconds]),
        np.array([10.0, 254.0, 10.0]), 2)
    p = np.poly1d(z)
    calculatedBrightness = p(timeSinceSunrise)
    print "Calculated Brightness"
    print calculatedBrightness
    return calculatedBrightness

def calculateHueTemperatureFromKelvin(kelvinTemperature):
    return (1.0/kelvinTemperature)*1000000.0;

def calculateColorTemperature(daylength, timeSinceSunrise):
    dayLengthInSeconds = convertTimeStringToSeconds(daylength)

    z = np.polyfit(np.array([0.0, float(dayLengthInSeconds/2.0), dayLengthInSeconds]),
        np.array([2700.0, 6500.0, 2700.0]), 2)
    p = np.poly1d(z)
    calculatedColorTemp = p(timeSinceSunrise)
    print "Calculated Temperature"
    print calculatedColorTemp
    return calculatedColorTemp

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
kelvinTemp = calculateColorTemperature(sunriseAndSunset["results"]["day_length"], timeSinceSunrise)
brightness = calculateBrightness(sunriseAndSunset["results"]["day_length"], timeSinceSunrise)
print "Calculated Hue Temperature"
print calculateHueTemperatureFromKelvin(kelvinTemp)
