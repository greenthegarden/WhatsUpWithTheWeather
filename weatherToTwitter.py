#!/usr/bin/env python

#---------------------------------------------------------------------------------------
# Load configuration values
#
#---------------------------------------------------------------------------------------

# see https://wiki.python.org/moin/ConfigParserShootout
from configobj import ConfigObj
config = ConfigObj('/home/pi/WhatsUpWithTheWeather/weatherToTwitter.cfg')
#config = ConfigObj('weatherToTwitter.cfg')


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
# Modules and details to support Twitter feed
#
#---------------------------------------------------------------------------------------

import tweepy

# for information about setting up Twitter see
# http://raspi.tv/2014/tweeting-with-python-tweepy-on-the-raspberry-pi-part-2-pi-twitter-app-series

# OAuth process, using the keys and tokens
auth = tweepy.OAuthHandler(config['twitter_cfg']['CONSUMER_KEY'],
                           config['twitter_cfg']['CONSUMER_SECRET'],
                           )
auth.set_access_token(config['twitter_cfg']['ACCESS_TOKEN'],
                      config['twitter_cfg']['ACCESS_TOKEN_SECRET'],
                      )

# Creation of the actual interface, using authentication
api = tweepy.API(auth)

#TWITTER_PREFIX = config['twitter_cfg']['TWITTER_PREFIX']


#---------------------------------------------------------------------------------------
# Modules and methods to support MQTT
#
#---------------------------------------------------------------------------------------

import ast

import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc) :

	print("Connected with result code "+str(rc))

	for topic in config['REPORT_TOPICS'] :
		client.subscribe(topic)
		print("Subscribed to topic {0}".format(topic))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg) :

#	if msg.topic == config['REPORT_TOPIC'] :

	# convert the message payload back to a dict
	try :
		report = ast.literal_eval(msg.payload)

		twitter_str = config['twitter_cfg']['TWITTER_PREFIX']

	#	if msg.topic == 'weather/summary/daily' :	# needs to be a config element
		if msg.topic == config['REPORT_TOPICS'][1] :
			twitter_str += config['twitter_cfg']['TWITTER_DAILY_TXT']

		if len(report) > 1 :
			for key, value in report.iteritems() :
				twitter_str += key + ": " + str(value) + ", "
			twitter_str = twitter_str[:-2]	# remove last comma and space

			assert len(twitter_str) < int(config['twitter_cfg']['MAX_MESSAGE_LENGTH']), "Twitter messages must have a length less than 140 characters!"

			print("Twitter string: {0}".format(twitter_str))

			try :
				api.update_status(status=twitter_str)
			except :
				print "Twitter post error"

	except :
		print "Failed to convert msg.payload to dict"

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
