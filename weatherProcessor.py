#!/usr/bin/env python

#---------------------------------------------------------------------------------------
# Load configuration values
#
#---------------------------------------------------------------------------------------

# see https://wiki.python.org/moin/ConfigParserShootout
from configobj import ConfigObj
config = ConfigObj('/home/pi/WhatsUpWithTheWeather/weatherProcessor.cfg')
#config = ConfigObj('weatherProcessor.cfg')


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
# Configure global variables
#
#---------------------------------------------------------------------------------------

# global variables
tempc           = float(config['var_init']['tempc'])
wind_gust_spd   = float(config['var_init']['wind_gust_spd'])
# to keep track of daily data (midnight to midnight)
tempc_daily_max = float(config['var_init']['tempc_daily_max'])
tempc_daily_min = float(config['var_init']['tempc_daily_min'])
rainmmdaily     = float(config['var_init']['rainmmdaily'])
# global variables to keep track of day/night data (9am to 9am)
tempc_to9_max   = float(config['var_init']['tempc_to9_max'])
tempc_to9_min   = float(config['var_init']['tempc_to9_min'])
rainmm9am       = float(config['var_init']['rainmm9am'])
# global variables to keep track of hourly data
rainmm          = float(config['var_init']['rainmm'])

report = {}


#---------------------------------------------------------------------------------------
# Modules and methods for processing weather data
#
#---------------------------------------------------------------------------------------

import numericalunits as nu
nu.reset_units()

# conversion of degrees Celcius to degrees
def degCtoF(tempc) :
	return( float(tempc) * (9/5.0) + 32 )

# calculate dewpoint based on temperature and humidity
def dewpoint_calc(tempc, humidity) :
	from math import log
	tempc    = float(tempc)
	humidity = float(humidity)
	from math import log
	if (tempc > 0.0) :
		Tn = 243.12
		m = 17.62
	else :
		Tn = 272.62
		m = 22.46
	dewpoint = (Tn*(log(humidity/100.0)+((m*tempc)/(Tn+tempc)))/(m-log(humidity/100.0)-((m*tempc)/(Tn+tempc))))
#	print("dewpoint: {0}".format(dewpoint))
	return dewpoint

# conversion of station pressure to mean sea level pressure
# source: http://www.sandhurstweather.org.uk/barometric.pdf
def pressure_station_to_msl(pressure,
                            temperature,
                            elevation = float(config['station_location']['ELEVATION'])
                            ) :
	from math import exp
	factor = exp(-elevation / ((temperature+273.15) * 29.263))
	return(pressure / factor)

def wind_degrees_to_direction(degrees) :
	degrees = float(degrees)
	if degrees == 0.0 :
		return "N"
	elif degrees == 22.5 :
		return "NNE"
	elif degrees == 45.0 :
		return "NE"
	elif degrees == 67.5 :
		return "ENE"
	elif degrees == 90.0 :
		return "E"
	elif degrees == 112.5 :
		return "ESE"
	elif degrees == 135.0 :
		return "SE"
	elif degrees == 157.5 :
		return "SSE"
	elif degrees == 180.0 :
		return "S"
	elif degrees == 202.5 :
		return "SSW"
	elif degrees == 225.0 :
		return "SW"
	elif degrees == 247.5 :
		return "WSW"
	elif degrees == 270.0 :
		return "W"
	elif degrees == 292.5 :
		return "WNW"
	elif degrees == 315.0 :
		return "NW"
	elif degrees == 337.5 :
		return "NNW"
	else :
		return "ERROR"

def reformat_datetime(time_str) :
	format = "%a %b %d %H:%M:%S %Y"
	return(time_str.strftime(format))

def reformat_time(time_str) :
	format = "%H:%M"
	return(time_str.strftime(format))


#---------------------------------------------------------------------------------------
# Modules and methods to support MQTT
#
#---------------------------------------------------------------------------------------

import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc) :

	print("Connected with result code "+str(rc))

	# Subscribing in on_connect() means that if the connection is lost
	# the subscriptions will be renewed when reconnecting.

	# weather station measurement topics
	for topic in config['mqtt_topics']['MEASUREMENT_TOPICS'] :
		client.subscribe(topic)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg) :

	global msg_arrival_time_local, msg_arrival_time_utc

	msg_arrival_time_local = datetime.now()	# local time
	msg_arrival_time_utc   = datetime.utcnow()

	global tempc_msg_arrival_time, tempc
	global tempc_daily_min, tempc_daily_max
	global wind_gust_spd
	global rainmm, rainmmdaily, rainmm9am

#	print(msg.topic+" "+str(msg.payload))

	if msg.topic == config['mqtt_data_topics']['TEMPERATURE_TOPIC'] :
		# in degrees Celcius
		tempc = float(msg.payload)
		tempc_msg_arrival_time = msg_arrival_time_local
		report['Temperature'] = {'value'     : str(msg.payload),  # add as string rather than float
					 'time_local': reformat_datetime(msg_arrival_time_local),
					 'time_utc'  : reformat_datetime(msg_arrival_time_utc),
					 'units'     : 'oC',
					 }
		report['Time'] = reformat_datetime(tempc_msg_arrival_time)
		report['Time_UTC'] = reformat_datetime(msg_arrival_time_utc)
		if tempc > tempc_daily_max :
			tempc_daily_max = tempc
			report['Temperature_Max_to9am'] = {'value'  : '{:.1f}'.format(tempc_daily_max),
					  		'time_local': reformat_datetime(msg_arrival_time_local),
							'time_utc'  : reformat_datetime(msg_arrival_time_utc),
							'units'     : 'oC',
							}
			report['Temp_Max'] = '{:.1f}'.format(tempc_daily_max)
			report['Temp_Max_Time'] = reformat_time(msg_arrival_time_utc)
			report['Temp_Max_@_Time'] = '{:.1f}'.format(tempc_daily_max) + " @ " + reformat_time(tempc_msg_arrival_time)
			client.publish("weather/temperature/daily_max", '{:.1f}'.format(tempc_daily_max))
			client.publish("weather/temperature/daily_max_time", str(msg_arrival_time_local))
		if tempc < tempc_daily_min :
			tempc_daily_min = tempc
			report['Temperature_Min_to9am'] = {'value'     : '{:.1f}'.format(tempc_daily_min),
					  		'time_local': reformat_datetime(msg_arrival_time_local),
							'time_utc'  : reformat_datetime(msg_arrival_time_utc),
							'units'     : 'oC',
							}
			report['Temp_Min'] = '{:.1f}'.format(tempc_daily_min)
			report['Temp_Min_Time'] = reformat_time(msg_arrival_time_utc)
			report['Temp_Min_@_Time'] = '{:.1f}'.format(tempc_daily_min) + " @ " + reformat_time(tempc_msg_arrival_time)
			client.publish("weather/temperature/daily_min", '{:.1f}'.format(tempc_daily_min))
			client.publish("weather/temperature/daily_min_time", str(msg_arrival_time_local))

	if msg.topic == config['mqtt_data_topics']['HUMIDITY_TOPIC'] :
		# as a percentage
		report['Humidity'] = {'value'     : msg.payload,	# add as string rather than float
					'time_local': reformat_datetime(msg_arrival_time_local),
					'time_utc'  : reformat_datetime(msg_arrival_time_utc),
					'units'     : '%',
					}
		# check temperature is in report
		if (msg_arrival_time_local - datetime.strptime(report['Temperature'].get('time_local'), "%a %b %d %H:%M:%S %Y")) < timedelta(seconds=2) :
			dewpoint = dewpoint_calc(float(report['Temperature'].get('value',tempc)), float(msg.payload))
			report['Dewpoint'] = {'value'     : '{0:.1f}'.format(dewpoint),
						'time_local': reformat_datetime(msg_arrival_time_local),
						'time_utc'  : reformat_datetime(msg_arrival_time_utc),
						'units'     : 'oC',
						}
			client.publish("weather/dewpoint/SHT15_dewpoint", '{0:.1f}'.format(dewpoint))

	# weather station will not report measurements from pressure sensor
	# if error code generated when sensor is initialised, or
	# if error code generated when taking reading
	if msg.topic == config['mqtt_data_topics']['PRESSURE_TOPIC'] :
		# in mbar
		report['Station_Pressure'] = {'value'     : msg.payload,
						'time_local': reformat_datetime(msg_arrival_time_local),
						'time_utc'  : reformat_datetime(msg_arrival_time_utc),
						'units'     : 'mbar',
						}

	if msg.topic == config['mqtt_data_topics']['BMP085_TEMP_TOPIC'] :
		# in degrees Celcius
		# check pressure is in report
		if (msg_arrival_time_local - datetime.strptime(report['Station_Pressure'].get('time_local'), "%a %b %d %H:%M:%S %Y")) < timedelta(seconds=2) :
			MSLP = pressure_station_to_msl(float(report['Station_Pressure'].get('value')), float(msg.payload))
			report['Pressure'] = {'value'     : '{0:.1f}'.format(MSLP),
					      'time_local': reformat_datetime(msg_arrival_time_local),
					      'time_utc'  : reformat_datetime(msg_arrival_time_utc),
					      'units'     : 'mbar',
						}
			client.publish("weather/pressure/BMP085_MSLP", '{0:.1f}'.format(MSLP))

	# weather station will not report measurements from the weather sensors
	# (wind and rain) if error code generated by wind direction reading
	if msg.topic == config['mqtt_data_topics']['WIND_DIR_TOPIC'] :
		# in degrees
		report['Wind_Dir'] = {'value'     : msg.payload,
					'time_local': reformat_datetime(msg_arrival_time_local),
					'time_utc'  : reformat_datetime(msg_arrival_time_utc),
					'units'     : 'deg',
					'direction' : wind_degrees_to_direction(msg.payload),
					}

	if msg.topic == config['mqtt_data_topics']['WIND_SPEED_TOPIC'] :
		# in knots
		report['Wind_Spd'] = {'value'     : msg.payload,
					'time_local': reformat_datetime(msg_arrival_time_local),
					'time_utc'  : reformat_datetime(msg_arrival_time_utc),
					'units'     : 'knots',
					}

	if msg.topic == config['mqtt_data_topics']['WIND_SPEED_MAX_TOPIC'] :
		# in knots
		# capture max wind gust per post to BoM WoW
		# value is reset once published
		# only publish if greater than 0
		if float(msg.payload) > wind_gust_spd :
			wind_gust_spd = float(msg.payload)
			report['Wind_Spd_Max'] = {'value'     : wind_gust_spd,
						'time_local': reformat_datetime(msg_arrival_time_local),
						'time_utc'  : reformat_datetime(msg_arrival_time_utc),
						'units'     : 'knots',
						}

	if msg.topic == config['mqtt_data_topics']['RAIN_TOPIC'] :
		# in millimetres
		# only update rain records if rain was recorded
		if float(msg.payload) > 0.0 :
			# rainmm value is reset to 0 on hour
			rainmm += float(msg.payload)
			# rainmm9am is the rain since 9am - value is reset to 0 at 9am
			rainmm9am += float(msg.payload)
			# rainmmdaily is the rain since midnight - value is reset to 0 at midnight
			rainmmdaily += float(msg.payload)
		report['Rain_last_hour'] = {'value'     : '{0:.1f}'.format(rainmm),
						'time_local': reformat_datetime(msg_arrival_time_local),
						'time_utc'  : reformat_datetime(msg_arrival_time_utc),
						'units'     : 'mm',
						}
		report['Rain_since_9am'] = {'value'     : '{0:.1f}'.format(rainmm9am),
						'time_local': reformat_datetime(msg_arrival_time_local),
						'time_utc'  : reformat_datetime(msg_arrival_time_utc),
						'units'     : 'mm',
						}
		client.publish("weather/rainfall/since9am", '{0:.1f}'.format(rainmmdaily))
		report['Rain_since_midnight'] = {'value'     : '{0:.1f}'.format(rainmmdaily),
						'time_local': reformat_datetime(msg_arrival_time_local),
						'time_utc'  : reformat_datetime(msg_arrival_time_utc),
						'units'     : 'mm',
						}
		client.publish("weather/rainfall/sincemidnight", '{0:.1f}'.format(rainmmdaily))

	if msg.topic == config['mqtt_data_topics']['BATTERY_VOLTAGE_TOPIC'] :
		report['Battery_Voltage'] = {'value'     : msg.payload,
						'time_local': reformat_datetime(msg_arrival_time_local),
						'time_utc'  : reformat_datetime(msg_arrival_time_utc),
						'units'     : 'volts',
						}

	if msg.topic == config['mqtt_data_topics']['SOLAR_VOLTAGE_TOPIC'] :
		report['Solar_Voltage'] = {'value'     : msg.payload,
						'time_local': reformat_datetime(msg_arrival_time_local),
						'time_utc'  : reformat_datetime(msg_arrival_time_utc),
						'units'     : 'volts',
						}

	if msg.topic == config['mqtt_data_topics']['OUTPUT_VOLTAGE_TOPIC'] :
		report['Output_Voltage'] = {'value'     : msg.payload,
						'time_local': reformat_datetime(msg_arrival_time_local),
						'time_utc'  : reformat_datetime(msg_arrival_time_utc),
						'units'     : 'volts',
						}

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

client.loop_start()


#---------------------------------------------------------------------------------------
# Initialisation of time  and schedules
#
#---------------------------------------------------------------------------------------

from datetime import datetime
from datetime import timedelta

msg_arrival_time_local    = datetime.min    # keep track of the time corresponding to the first data for a new report
msg_arrival_time_utc      = datetime.min
tempc_msg_arrival_time    = datetime.min		# used to ensure tempc measurement is not too old for dewpoint calculation
publish_power_last_sent   = datetime.now()
publish_on_hour_last_sent = datetime.now()	# keep track of the time a report was last sent
publish_daily_last_sent   = datetime.now()
publish_bom_wow_last_sent = datetime.now()

# define schedule callbacks

def publish_power_summary() :
	global publish_power_last_sent
	if msg_arrival_time_local > publish_power_last_sent :
		summary = {x: report[x] for x in config['summary_power']['DATA'] if x in report}
		if len(summary) > 1 :
			print("Topic: {0}".format(str(config['summary_power']['TOPIC'])))
			print("Summary: {0}".format(str(summary)))
			client.publish(config['summary_power']['TOPIC'], str(summary))
		publish_power_last_sent = msg_arrival_time_local

def publish_on_hour_summary() :
	global publish_on_hour_last_sent
	if msg_arrival_time_local > publish_on_hour_last_sent :
		summary = {x: report[x] for x in config['summary_hourly']['DATA'] if x in report}
		if len(summary) > 1 :
			print("Topic: {0}".format(str(config['summary_hourly']['TOPIC'])))
			print("Summary: {0}".format(str(summary)))
			client.publish(config['summary_hourly']['TOPIC'], str(summary))
		publish_on_hour_last_sent = msg_arrival_time_local

def publish_daily_summary() :
	global publish_daily_last_sent
	if msg_arrival_time_local > publish_daily_last_sent :
		summary = {x: report[x] for x in config['summary_daily']['DATA'] if x in report}
		if len(summary) > 1 :
			print("Topic: {0}".format(str(config['summary_daily']['TOPIC'])))
			print("Summary: {0}".format(str(summary)))
			client.publish(config['summary_daily']['TOPIC'], str(summary))
		publish_daily_last_sent = msg_arrival_time_local

def publish_bom_wow_summary() :
	global wind_gust_spd
	global publish_bom_wow_last_sent
	if msg_arrival_time_local > publish_bom_wow_last_sent :
		summary = {x: report[x] for x in config['summary_bom_wow']['DATA'] if x in report}
		if len(summary) > 1 :
			print("Topic: {0}".format(str(config['summary_bom_wow']['TOPIC'])))
			print("Summary: {0}".format(str(summary)))
			client.publish(config['summary_bom_wow']['TOPIC'], str(summary))
			# reset max wind gust
			wind_gust_spd = 0
		publish_bom_wow_last_sent = msg_arrival_time_local

def on_hour() :
	publish_on_hour_summary()
	print("hourly data reset on hour")
	global rainmm
	rainmm = float(config['var_init']['rainmm'])

def at_9am() :
	publish_daily_summary()
	print("9am data reset at 0900")
	global tempc_to9_max, tempc_to9_min, rainmm9am
	tempc_to9_max = float(config['var_init']['tempc_to9_max'])
	tempc_to9_min = float(config['var_init']['tempc_to9_min'])
	rainmm9am     = float(config['var_init']['rainmm9am'])

def at_midnight() :
	print("daily data reset at midnight")
	global tempc_daily_max, tempc_daily_min, rainmmdaily
	tempc_daily_max = float(config['var_init']['tempc_daily_max'])
	tempc_daily_min = float(config['var_init']['tempc_daily_min'])
	rainmmdaily     = float(config['var_init']['rainmmdaily'])

import schedule
import time

# define schedules

schedule.every(int(config['summary_bom_wow']['INTERVAL'])).minutes.do(publish_bom_wow_summary)
schedule.every(int(config['summary_power']['INTERVAL'])).minutes.do(publish_power_summary)
schedule.every().hour.at(':00').do(on_hour)
schedule.every().day.at("9:00").do(at_9am)
schedule.every().day.at("0:00").do(at_midnight)


#---------------------------------------------------------------------------------------
# Program loops continuously from here
#
#---------------------------------------------------------------------------------------

while True :

	schedule.run_pending()
