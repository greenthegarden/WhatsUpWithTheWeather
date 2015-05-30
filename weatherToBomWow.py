#!/usr/bin/env python

#---------------------------------------------------------------------------------------
# Load configuration values
#
#---------------------------------------------------------------------------------------

# see https://wiki.python.org/moin/ConfigParserShootout
from configobj import ConfigObj
config = ConfigObj('/home/pi/WhatsUpWithTheWeather/weatherToBomWow.cfg')
#config = ConfigObj('weatherToBomWow.cfg')


#---------------------------------------------------------------------------------------
# Enable logging
#
#---------------------------------------------------------------------------------------

# Code from
# http://blog.scphillips.com/posts/2013/07/getting-a-python-script-to-run-in-the-background-as-a-service-on-boot/

import logging
import logging.handlers
import sys

# Defaults
LOG_FILENAME = config['log_cfg']['LOG_FILE']
LOG_LEVEL = logging.INFO  # Could be e.g. "DEBUG" or "WARNING"

# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)

# Make a class that will be used to capture stdout and sterr in the log
class MyLogger(object) :

	def __init__(self, logger, level) :
		"""Needs a logger and a logger level."""
		self.logger = logger
		self.level = level

	def write(self, message) :
		# Only log if there is a message (not just a new line)
		if message.rstrip() != "" :
			self.logger.log(self.level, message.rstrip())

# Replace stdout with logging to file at INFO level
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)


#---------------------------------------------------------------------------------------
# Modules and methods for processing weather data
#
#---------------------------------------------------------------------------------------

# conversion of degrees Celcius to degrees
def degCtoF(temperature) :
	return( float(temperature) * (9/5.0) + 32 )

# 1 millibar (or hectopascal/hPa), is equivalent to 0.02953 inches of mercury (Hg).
# source: http://weatherfaqs.org.uk/node/72
def hectopascalToIn(pressure) :
	return float(pressure) * 0.02953

# km/h to mph
def speed_knotsToMilePerHour(speed) :
	return float(speed) * 1.15078

# mm to inches
def length_mmToinch(distance) :
#		report['Rain_last_hour'] = str(rainmm)
#		bom_wow_report['rainin'] = (rainmm*nu.mm)/nu.inch
	return float(distance) / 25.4

#---------------------------------------------------------------------------------------
# Modules and details to support Bom WoW feed
#
#---------------------------------------------------------------------------------------

# payload initialised with BoM WoW siteid and siteAuthenticationKey
payload = {'siteid': config['bom_wow_cfg']['SITE_ID'],
           'siteAuthenticationKey': config['bom_wow_cfg']['SITE_AUTHENTICATION_KEY'],
           }

data_to_post = {}

# sends a report to the BoM WOW in format

# http://wow.metoffice.gov.uk/automaticreading?siteid=123456&siteAuthenticationKey=654321&dateutc=2011-02-02+10%3A32%3A55&winddir=230&windspeedmph=12&windgustmph=12& windgustdir=25&humidity=90&dewptf=68.2&tempf=70&rainin=0&dailyrainin=5&baromin=29.1&soiltempf=25&soilmoisture=25&visibility=25&softwaretype=weathersoftware1.0

# Weather Data (from http://wow.metoffice.gov.uk/support/dataformats)

# The following is a list of items of weather data that can be uploaded to WOW.
# Provide each piece of information as a key/value pair, e.g. winddir=225.5 or tempf=32.2.
# Note that values should not be quoted or escaped.
# Key           Value                                                              Unit
# winddir       Instantaneous Wind Direction                                       Degrees (0-360)
# windspeedmph  Instantaneous Wind Speed                                           Miles per Hour
# windgustdir   Current Wind Gust Direction (using software specific time period)  0-360 degrees
# windgustmph   Current Wind Gust (using software specific time period)            Miles per Hour
# humidity      Outdoor Humidity                                                   0-100 %
# dewptf        Outdoor Dewpoint                                                   Fahrenheit
# tempf         Outdoor Temperature                                                Fahrenheit
# rainin        Accumulated rainfall in the past 60 minutes                        Inches
# dailyrainin   Inches of rain so far today                                        Inches
# baromin       Barometric Pressure (see note)                                     Inches
# soiltempf     Soil Temperature                                                   Fahrenheit
# soilmoisture  % Moisture                                                         0-100 %
# visibility    Visibility                                                         Nautical Miles

from datetime import datetime

def timestr_to_time(date_str) :
	return(datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y"))

def format_time(date_str) :
	# add time to report
	# The date must be in the following format: YYYY-mm-DD HH:mm:ss,
	# where ':' is encoded as %3A, and the space is encoded as either '+' or %20.
	# An example, valid date would be: 2011-02-29+10%3A32%3A55, for the 2nd of Feb, 2011 at 10:32:55.
	# Note that the time is in 24 hour format.
	# Also note that the date must be adjusted to UTC time - equivalent to the GMT time zone.
	# first convert string back to datetime
	# reformat
	format = "%Y-%m-%d+%H:%M:%S"
	return(timestr_to_time(date_str).strftime(format))

latest_time = datetime.utcnow()

def get_latest_time(new_time) :
	global latest_time
	if new_time > latest_time :
		latest_time = new_time
	return(latest_time)

import ast

def process_payload(report) :

	global data_to_post
	data_to_post = {}

	# convert the message payload back to a dict
	try :
		report_dict = ast.literal_eval(report)
	except :
		print("{0}".format("String not able to be converted to dict"))
		return

	for key, value in report_dict.items() :
		print("key, value: {0}, {1}".format(key, value))
#		if key == 'Time_UTC' :
#			data_to_post['dateutc'] = format_time(value)
		if key == 'Temperature' :
			# convert from degree Celsius to Farhenhiet
			data_to_post['tempf'] = '{0:.1f}'.format(degCtoF(value.get('value')))
			data_to_post['dateutc'] = format_time(get_latest_time(timestr_to_time(value.get('time_utc'))))
		if key == 'Humidity' :
			data_to_post['humidity'] = value.get('value')
			data_to_post['dateutc'] = format_time(get_latest_time(timestr_to_time(value.get('time_utc'))))
		if key == 'Dewpoint' :
			# convert from degree Celsius to Fahrenheit
			data_to_post['dewptf'] = '{0:.1f}'.format(degCtoF(value.get('value')))
		if key == 'Pressure' :
			# convert from hectopascal to inches
			data_to_post['baromin'] = '{0:.1f}'.format(hectopascalToIn(value.get('value')))
			data_to_post['dateutc'] = get_latest_time(timestr_to_time(value.get('time_utc')))
		if key == 'Wind_Dir' :
			data_to_post['winddir'] = value
		if key == 'Wind_Spd' :
			data_to_post['windspeedmph'] = '{0:.1f}'.format(speed_knotsToMilePerHour(value.get('value')))
		if key == 'Rain_last_hour' :
			data_to_post['rainin'] = '{0:.1f}'.format(length_mmToinch(value.get('value')))
		if key == 'Rain_since_midnight' :
			data_to_post['dailyrainin'] = '{0:.1f}'.format(length_mmToinch(value.get('value')))

	# ensure time was set and one other field otherwise do not send data
	if not 'dateutc' in data_to_post :
		print "dateutc not set!!"
		data_to_post = {}
		return
	if not (len(data_to_post) > 1) :
		print "data_to_post does not contain any data to post!!"
		data_to_post = {}
	else :
		payload.update(data_to_post)
		print("payload: {0}".format(payload))


import requests
import json

def post_payload() :

	global data_to_post

	# check there is data to be posted before posting
	if len(data_to_post) > 1 :
		# POST with form-encoded data1
		r = requests.post(config['bom_wow_cfg']['BOM_WOW_URL'], data=payload)

		# All requests will return a status code.
		# A success is indicated by 200.
		# Anything else is a failure.
		# A human readable error message will accompany all errors in JSON format.
		print("POST request status code: {0}".format(r.json))

	# clear data that was posted once sent
	data_to_post = {}


#---------------------------------------------------------------------------------------
# Modules and methods to support MQTT
#
#---------------------------------------------------------------------------------------

import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc) :

	print("Connected with result code "+str(rc))

	client.subscribe(config['REPORT_TOPIC'])

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg) :

	if msg.topic == config['REPORT_TOPIC'] :
		process_payload(msg.payload)
		if config['bom_wow_cfg']['POST_DATA'] == 'True' :
			post_payload()

# Definition of MQTT client and connection to MQTT Broker

client = mqtt.Client()

client.connect(config['mqtt_configuration']['MQTT_BROKER_IP'],
               int(config['mqtt_configuration']['MQTT_BROKER_PORT']),
               int(config['mqtt_configuration']['MQTT_BROKER_PORT_TIMEOUT'])
               )

print("Connected to MQTT broker at {0}".format(config['mqtt_configuration']['MQTT_BROKER_IP']))

# link to callback functions
client.on_connect = on_connect
client.on_message = on_message

client.loop_forever()
