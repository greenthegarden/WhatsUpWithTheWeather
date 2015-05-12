# config file creator

from configobj import ConfigObj
config = ConfigObj()
config.filename = 'weatherToTwitter.cfg'

# report topic
config['REPORT_TOPIC'] = "weather/bom_wow/report"

# twitter configuration
twitter_cfg = {
	'CONSUMER_KEY'        : "Replace with consumer key!",
	'CONSUMER_SECRET'     : "Replace with consumer secret!",
	'ACCESS_TOKEN'        : "Replace with access token!",
	'ACCESS_TOKEN_SECRET' : "Replace with access token secret!",
	'TWITTER_PREFIX'      : "Weather @ Home => ",
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
