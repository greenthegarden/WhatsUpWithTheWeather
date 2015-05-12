# config file creator

from configobj import ConfigObj
config = ConfigObj()
config.filename = 'weatherToBomWow.cfg'

# BoM WoW report topic
config['REPORT_TOPIC'] = "weather/bom_wow/report"

# BoM WoW configuration
bom_wow_cfg = {
	'BOM_WOW_URL'             : 'http://wow.metoffice.gov.uk/automaticreading?',
	'SITE_ID'                 : 'Replace with site id!',
	'SITE_AUTHENTICATION_KEY' : 'Replace with site authentication key!',
	}
config['bom_wow_cfg'] = bom_wow_cfg

# mqtt configuration
mqtt_configuration = {
	'MQTT_BROKER_IP'           : "192.168.1.55",
	'MQTT_BROKER_PORT'         : "1883",
	'MQTT_BROKER_PORT_TIMEOUT' : "60",
	}
config['mqtt_configuration'] = mqtt_configuration


config.write()
