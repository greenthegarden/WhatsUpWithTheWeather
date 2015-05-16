# config file creator

from configobj import ConfigObj
config = ConfigObj()
config.filename = 'weatherProcessor.cfg'


# log configuration
log_cfg = {
	'LOG_FILE' : "/tmp/weatherProcessor.log",
	}
config['log_cfg'] = log_cfg

# global variable initialisation
var_init = {
	'tempc'           : -100,
	'tempc_daily_max' : -100,
	'tempc_daily_min' : 100,
	'rainmmdaily'     : 0,
	'tempc_to9_max'   : -100,
	'tempc_to9_min'   : 100,
	'rainmm9am'       : 0,
	'rainmm'          : 0,
	}
config['var_init'] = var_init

# summary report configuration
summary_hourly = {
	'DATA'  : ['Temperature', 'Humidity', 'Wind_Dir', 'Wind_Spd', 'Rain_last_hour', 'Rain_since_9am'],
	'TOPIC' : "weather/summary/hourly",
	}
config['summary_hourly'] = summary_hourly

summary_daily = {
	'DATA'  : ['Temp_Max', 'Temp_Min', 'Rain_since_9am'],
	'TOPIC' : "weather/summary/daily",
	}
config['summary_daily'] = summary_daily

# BoM WoW configuration
summary_bom_wow = {
	'DATA'  : ['Time_UTC', 'Temperature', 'Humidity', 'Wind_Dir', 'Wind_Spd', 'Rain_last_hour', 'Rain_since_midnight'],
#	'DATA'  : ['Time', 'Temperature', 'Humidity', 'Dewpoint', 'Wind_Dir', 'Wind_Spd', 'Rain_last_hour', 'Rain_since_9am'],
	'TOPIC'    : "weather/summary/bom_wow",
	'INTERVAL' : 15,
	}
config['summary_bom_wow'] = summary_bom_wow

# mqtt configuration
mqtt_configuration = {
	'MQTT_BROKER_IP'           : "192.168.1.55",
	'MQTT_BROKER_PORT'         : "1883",
	'MQTT_BROKER_PORT_TIMEOUT' : "60",
	}
config['mqtt_configuration'] = mqtt_configuration

# Weather station measurement topics
config['mqtt_topics'] = {}
config['mqtt_topics']['MEASUREMENT_TOPICS'] = ['weather/measurement/#', 'weather/sunairplus/#']

# Specific data measurement topics
mqtt_data_topics = {
	'TEMPERATURE_TOPIC'     : 'weather/measurement/SHT15_temp',
	'HUMIDITY_TOPIC'        : 'weather/measurement/SHT15_humidity',
	'PRESSURE_TOPIC'        : 'weather/measurement/BMP085_pressure',
	'WIND_DIR_TOPIC'        : 'weather/measurement/wind_dir',
	'WIND_SPEED_TOPIC'      : 'weather/measurement/wind_spd',
	'RAIN_TOPIC'            : 'weather/measurement/rain',
	'BATTERY_VOLTAGE_TOPIC' : 'weather/sunairplus/battery_voltage',
	'SOLAR_VOLTAGE_TOPIC'   : 'weather/sunairplus/solar_voltage',
	'OUTPUT_VOLTAGE_TOPIC'  : 'weather/sunairplus/output_voltage',
	}
config['mqtt_data_topics'] = mqtt_data_topics


config.write()
