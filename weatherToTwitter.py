#!/usr/bin/env python

#---------------------------------------------------------------------------------------
# Load configuration values
#
#---------------------------------------------------------------------------------------

# see https://wiki.python.org/moin/ConfigParserShootout
from configobj import ConfigObj
config = ConfigObj('weatherToTwitter.cfg')

print("{0}".format("Weather to Twitter Publisher"))


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

TWITTER_PREFIX = config['twitter_cfg']['TWITTER_PREFIX']


#---------------------------------------------------------------------------------------
# Modules and methods to support MQTT
#
#---------------------------------------------------------------------------------------

import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc) :

	print("Connected with result code "+str(rc))

	client.subscribe(config['TWITTER_REPORT_TOPIC'])

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg) :

	if msg.topic == config['TWITTER_REPORT_TOPIC'] :

		twitter_str = TWITTER_PREFIX + str(msg.payload)

		assert len(twitter_str) < 140, "Twitter messages must be less than 140 characters!"

		print("Twitter string: {0}".format(twitter_str))

		try :
			api.update_status(status=twitter_str)
		except :
			print "Twitter post error"


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
