#!/usr/bin/env python

#---------------------------------------------------------------------------------------
# Load configuration values
#
#---------------------------------------------------------------------------------------

# see https://wiki.python.org/moin/ConfigParserShootout
from configobj import ConfigObj
config = ConfigObj('weatherToBomWow.cfg')

print("{0}".format("Weather to BoM WoW Publisher"))


#---------------------------------------------------------------------------------------
# Modules and details to support Bom WoW feed
#
#---------------------------------------------------------------------------------------

import requests
import json

# http://wow.metoffice.gov.uk/automaticreading?siteid=123456&siteAuthenticationKey=654321&dateutc=2011-02-02+10%3A32%3A55&winddir=230&windspeedmph=12&windgustmph=12& windgustdir=25&humidity=90&dewptf=68.2&tempf=70&rainin=0&dailyrainin=5&baromin=29.1&soiltempf=25&soilmoisture=25&visibility=25&softwaretype=weathersoftware1.0

# details for Bom WoW site
BOM_WOW_URL              = config['bom_wow_cfg']['BOM_WOW_URL']
#SITE_ID                 = config['bom_wow_cfg']['SITE_ID']
#SITE_AUTHENTICATION_KEY = config['bom_wow_cfg']['SITE_AUTHENTICATION_KEY']	# 6 digit number

# payload initialised with BoM WoW siteid and siteAuthenticationKey
payload = {'siteid': config['bom_wow_cfg']['SITE_ID'],
           'siteAuthenticationKey': config['bom_wow_cfg']['SITE_AUTHENTICATION_KEY'],
           }


#---------------------------------------------------------------------------------------
# Modules and methods to support MQTT
#
#---------------------------------------------------------------------------------------

import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc) :

	print("Connected with result code "+str(rc))

	client.subscribe(config['BOM_WOW_REPORT_TOPIC'])

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg) :

	if msg.topic == config['BOM_WOW_REPORT_TOPIC'] :

		print("topic message: {0}".format(msg.payload))

		# POST with form-encoded data1
		#	r = requests.post(BOM_WOW_URL, data=payload)

		# All requests will return a status code.
		# A success is indicated by 200.
		# Anything else is a failure.
		# A human readable error message will accompany all errors in JSON format.
	#	print("POST request status code: {0}".format(r.json))


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
