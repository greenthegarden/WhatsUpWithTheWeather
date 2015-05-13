#!/usr/bin/env python

#---------------------------------------------------------------------------------------
# Load configuration values
#
#---------------------------------------------------------------------------------------

# see https://wiki.python.org/moin/ConfigParserShootout
from configobj import ConfigObj
config = ConfigObj('/home/pi/WhatsUpWithTheWeather/weatherToBomWow.cfg')


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
# Modules and details to support Bom WoW feed
#
#---------------------------------------------------------------------------------------

import requests
import json

# http://wow.metoffice.gov.uk/automaticreading?siteid=123456&siteAuthenticationKey=654321&dateutc=2011-02-02+10%3A32%3A55&winddir=230&windspeedmph=12&windgustmph=12& windgustdir=25&humidity=90&dewptf=68.2&tempf=70&rainin=0&dailyrainin=5&baromin=29.1&soiltempf=25&soilmoisture=25&visibility=25&softwaretype=weathersoftware1.0

# payload initialised with BoM WoW siteid and siteAuthenticationKey
payload = {'siteid': config['bom_wow_cfg']['SITE_ID'],
           'siteAuthenticationKey': config['bom_wow_cfg']['SITE_AUTHENTICATION_KEY'],
           }


#---------------------------------------------------------------------------------------
# Modules and methods to support MQTT
#
#---------------------------------------------------------------------------------------

import ast

import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc) :

	print("Connected with result code "+str(rc))

	client.subscribe(config['REPORT_TOPIC'])

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg) :

	if msg.topic == config['REPORT_TOPIC'] :

		# convert the message payload back to a dict
		payload.update(ast.literal_eval(msg.payload))

		print("payload: {0}".format(payload))

		# POST with form-encoded data1
		r = requests.post(config['bom_wow_cfg']['BOM_WOW_URL'], data=payload)

		# All requests will return a status code.
		# A success is indicated by 200.
		# Anything else is a failure.
		# A human readable error message will accompany all errors in JSON format.
		print("POST request status code: {0}".format(r.json))


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
