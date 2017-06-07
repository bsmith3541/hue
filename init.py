import ssdp
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time
from urlparse import urlparse
from pprint import pprint
import json
import numpy.polynomial.polynomial as poly

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

def calculate24HourTimeFrom12HourTime(currentTime):
    currentTimeAsTimeObject = time.strptime(currentTime, '%I:%M:%S %p')
    if currentTime[-2:] == "AM":
        currentTimeAsString = time.strftime('%H:%M:%S', currentTimeAsTimeObject)
        return currentTimeAsString
    else:
        print "it's PM so I have to work..."
        convertedTime = timedelta(hours=currentTimeAsTimeObject.tm_hour+12,
            minutes=currentTimeAsTimeObject.tm_min,
            seconds=currentTimeAsTimeObject.tm_sec)
        print convertedTime
        return convertedTime

def calculateTimeSinceSunrise(sunrise):
    sunriseInSeconds = convertTimeStringToSeconds(sunrise)
    currentTimeInSeconds = convertTimeStringToSeconds(datetime.utcnow().time().strftime('%H:%M:%S'))
    timeSinceSunrise = currentTimeInSeconds - sunriseInSeconds

    return timeSinceSunrise

def calculateBrightness(daylength, timeSinceSunrise):
    dayLengthInSeconds = convertTimeStringToSeconds(daylength)

    coefs = poly.polyfit([0.0, float(dayLengthInSeconds/2.0), dayLengthInSeconds],
        [10.0, 254.0, 10.0], 2)
    ffit = poly.Polynomial(coefs)
    calculatedBrightness = ffit(timeSinceSunrise)
    roundedBrightness = int(round(calculatedBrightness))

    return roundedBrightness

def calculateHueTemperatureFromKelvin(kelvinTemperature):
    tempInMireks = (1.0/kelvinTemperature)*1000000.0
    roundedTemp = int(round(tempInMireks))

    return roundedTemp

def calculateColorTemperature(daylength, timeSinceSunrise):
    dayLengthInSeconds = convertTimeStringToSeconds(daylength)

    coefs = poly.polyfit([0.0, float(dayLengthInSeconds/2.0), dayLengthInSeconds],
        [2700.0, 6500.0, 2700.0], 2)
    ffit = poly.Polynomial(coefs)

    calculatedColorTemp = ffit(timeSinceSunrise)
    print "Calculated Temperature (in Kelvin)"
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
        return json.loads(sunriseAndSunset.text)

def updateHueBulb():
    sunriseAndSunset = getSunriseAndSunset()
    timeSinceSunrise = calculateTimeSinceSunrise(calculate24HourTimeFrom12HourTime(sunriseAndSunset["results"]["sunrise"]))
    kelvinTemp = calculateColorTemperature(sunriseAndSunset["results"]["day_length"], timeSinceSunrise)
    brightness = calculateBrightness(sunriseAndSunset["results"]["day_length"], timeSinceSunrise)
    hueTemp = calculateHueTemperatureFromKelvin(kelvinTemp)
    print "Rounded Hue Temperature (in Mireks)"
    print hueTemp
    payload = {
        "ct": hueTemp,
        "bri": brightness
    }
    updateResponse = requests.put('http://10.0.1.2/api/{0}/lights/3/state'.format('w1nlqIyiImsfb0-lMGgm2lZr7k3AWp7MnH1xtRCY'),json=payload)
    requests.put('http://10.0.1.2/api/{0}/lights/4/state'.format('w1nlqIyiImsfb0-lMGgm2lZr7k3AWp7MnH1xtRCY'),json=payload)

updateHueBulb()
