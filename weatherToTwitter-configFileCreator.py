# config file creator

from configobj import ConfigObj
config = ConfigObj()
config.filename = 'weatherToTwitter.cfg'


# topics to publish
config['REPORT_TOPICS'] = {}
config['REPORT_TOPICS'] = ['weather/summary/hourly', 'weather/summary/daily', 'weather/summary/power']
config['PUBLISH'] = True	# set to False to test code with out actually publishing

# log configuration
log_cfg = {
	'LOG_FILE' : "/tmp/weatherToTwitter.log",
	}
config['log_cfg'] = log_cfg

# twitter configuration
twitter_cfg = {
	'CONSUMER_KEY'        : "Replace with consumer key!",
	'CONSUMER_SECRET'     : "Replace with consumer secret!",
	'ACCESS_TOKEN'        : "Replace with access token!",
	'ACCESS_TOKEN_SECRET' : "Replace with access token secret!",
	'TWITTER_PREFIX'      : "Weather @ Home => ",
	'TWITTER_DAILY_TXT'   : "Daily Summary: ",
	'MAX_MESSAGE_LENGTH'  : 140,
	}
config['twitter_cfg'] = twitter_cfg

# mqtt configuration
mqtt_configuration = {
	'MQTT_BROKER_IP'           : "192.168.1.55",
	'MQTT_BROKER_PORT'         : "1883",
	'MQTT_BROKER_PORT_TIMEOUT' : "60",
	}
config['mqtt_configuration'] = mqtt_configuration


config.write()
