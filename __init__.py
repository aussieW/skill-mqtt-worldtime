import time

from os.path import dirname

from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import getLogger
from mycroft.api import DeviceApi

#from urllib2 import urlopen  # <<< not sure if this is required
import paho.mqtt.client as mqtt

__author__ = 'aussieW'  # based on the original work of 'jamiehoward430'

LOGGER = getLogger(__name__)

dataRequestTopic = 'send/#'
actionConfirmationTopic = 'automation/action/confirm'

class mqttskill(MycroftSkill):

    def __init__(self):
        super(mqttskill, self).__init__(name="mqttskill")

        self.default_location = self.room_name
       
        self.protocol = self.settings.get('protocol')
        self.mqttssl = self.settings.get('ssl')
        self.mqttca = self.settings.get('ca_certificate')
        self.mqtthost = self.settings.get('host')
        self.mqttport = self.settings.get('port')
        self.mqttauth = self.settings.get('auth')
        self.mqttuser = self.settings.get('username')
        self.mqttpass = self.settings.get('password')
    
    def initialize(self):
        pass
		
    def mqtt_connect(self, topic=None):
        self.mqttc = mqtt.Client("MycroftAI_" + self.default_location)
        if (self.mqttauth == "yes"):
            self.mqttc.username_pw_set(self.mqttuser,self.mqttpass)
        if (self.mqttssl == "yes"):
            self.mqttc.tls_set(self.mqttca)
        LOGGER.info("AJW - connect to: " + self.mqtthost + ":" + str(self.mqttport) + " as MycroftAI_" + self.default_location )
        self.mqttc.connect(self.mqtthost,self.mqttport,10)
        # if s topic is provided then set up a listener
        if topic:
            self.mqttc.on_message = self.on_message
            self.mqttc.loop_start()
            self.mqttc.subscribe(topic)
		
    def mqtt_publish(self, topic, msg):
        LOGGER.info("AJW: Published " + topic + ", " + msg)
        self.mqttc.publish(topic, msg)
		
    def mqtt_disconnect(self):
        self.mqttc.disconnect()
	
    # from steve-mycroft wink skill
    @property	
    def room_name(self):
        # assume the "name" of the device is the "room name"
        device = DeviceApi().get()
        return device['description'].replace(' ', '_')

    @intent_handler(IntentBuilder('handle_automation_command').require("CommandKeyword").require("ModuleKeyword").require("ActionKeyword").optionally("LocationKeyword"))
    def handle_automation_command(self, message):
        LOGGER.info('AJW: mqtt automation command')

        cmd_name = message.data.get("CommandKeyword")
        mdl_name = message.data.get("ModuleKeyword")
        mdl_name = mdl_name.replace(' ', '_')
        mdl_name = mdl_name.replace('-', '_')
        act_name = message.data.get("ActionKeyword")
        loc_name = message.data.get("LocationKeyword")

        # set a default location in none provided
        if loc_name:
            loc_name = loc_name.replace(' ', '_')
        else:
            loc_name = self.default_location
        
        if act_name:
            cmd_name += '_' + act_name

        LOGGER.info('AJW: Heard: ' + cmd_name + '; mdl: ' + mdl_name + '; act: ' + act_name + '; loc: ' + loc_name)

        if mdl_name in ('air_conditioning', 'air_conditioner'):
            self.mqtt_connect(actionConfirmationTopic)
            self.mqtt_publish(loc_name + "/" + mdl_name, act_name)
            # allow time for the action to be performed and a confirmation to be returned
            time.sleep(10)
            self.mqtt_disconnect()
            LOGGER.info(mdl_name + "-" + cmd_name)
        else:
            self.mqtt_connect(actionConfirmationTopic)
            self.mqtt_publish(loc_name + "/" + mdl_name, act_name)
            # allow time for the action to be performed and a confirmation to be returned
            time.sleep(10)
            self.mqtt_disconnect()
            LOGGER.info(mdl_name + "-" + cmd_name)

    @intent_handler(IntentBuilder('handle_control_command').require("ModuleKeyword").require("AttributeKeyword").require("ValueKeyword").optionally("LocationKeyword"))
    def handle_control_command(self, message):
    # example: "set the kitchen display brightness to 40"
	
        LOGGER.info('AJW: handle control command')
		
        att_name = message.data.get("AttributeKeyword")
        mdl_name = message.data.get("ModuleKeyword")
        mdl_name = mdl_name.replace(' ', '_')
        val_name = message.data.get("ValueKeyword")
        loc_name = message.data.get("LocationKeyword")

        # set a default location in none provided
        if loc_name:
            loc_name = loc_name.replace(' ', '_')
        else:
            loc_name = self.default_location

        LOGGER.info('AJW: att: ' + att_name + '; mdl: ' + mdl_name + '; val: ' + val_name + '; loc: ' + loc_name)

        self.mqtt_connect(actionConfirmationTopic)
        self.mqtt_publish(loc_name + "/" + mdl_name + "/" + att_name, val_name)
        self.speak_dialog("cmd.sent")
        # wait for a response before disconnecting
        time.sleep(10)
        self.mqtt_disconnect()

    @intent_handler(IntentBuilder('').require("CommandKeyword").require("Sonoff").require("ActionKeyword"))
    def hanle_sonoff_command(self,message):

        LOGGER.info('AJW: handle sonoff command')

        cmnd = message.data.get("Sonoff")
        command = cmnd.replace(' ', '_')
        action = message.data.get("ActionKeyword")

        self.mqtt_connect()
        self.mqtt_publish('cmnd/' + command + '/POWER', action)
        self.speak_dialog("cmd.sent")
        self.mqtt_disconnect()


    @intent_handler(IntentBuilder('').require("ShowWorldTime").require("WorldTime").optionally("LocationKeyword"))
    def handle_show_world_time(self, message):
	    # examples: "show the world time on the kitchen display"
	    #           "display the world time"
		
        LOGGER.info('AJW: handle show world time')
	
	# ask for the city to display
        response = self.get_response('ask.for.city')
        if not response:
            return
        city = response
	
        loc_name = message.data.get("LocationKeyword")
        # set a default location in none provided
        if loc_name:
            loc_name = loc_name.replace(' ', '_')
        else:
            loc_name = self.default_location
        
        self.mqtt_connect(actionConfirmationTopic)
        LOGGER.info("AJW - connect to: " + self.mqtthost)
        LOGGER.info("AJW - connect to: " + str(self.mqttport))
        self.mqtt_publish(loc_name + "/display/worldtime", city)
        self.speak_dialog("cmd.sent")
        # wait for a response before disconnecting
        time.sleep(10)
        self.mqtt_disconnect()

    @intent_handler(IntentBuilder('').require("ShowWorldTime").require("WorldTime").require("city_name").optionally("LocationKeyword"))
    def handle_show_world_time_city(self, message):
        # examples: "show the world time for shanghi on the kitchen display"
        #           "display the world time for shanghi"
		
        city = message.data.get("city_name")
        loc_name = message.data.get("LocationKeyword")

        # set a default location in none provided
        if loc_name:
            loc_name = loc_name.replace(' ', '_')
        else:
            loc_name = self.default_location
        
        self.mqtt_connect(actionConfirmationTopic)
        LOGGER.info("AJW - connect to: " + self.mqtthost)
        LOGGER.info("AJW - connect to: " + str(self.mqttport))
        self.mqtt_publish(loc_name + "/display/worldtime", city)
        self.speak_dialog("cmd.sent")
        # wait for a response before disconnecting
        time.sleep(10)
        self.mqtt_disconnect()

    @intent_handler(IntentBuilder('handle_hide_world_time').require("HideWorldTime").require("WorldTime").optionally("LocationKeyword"))
    def handle_hide_world_time(self, message):
	# examples: "hide the world time on the kitchen display"
	#           "hide the world time"
        #           "remove the world time"
		
        LOGGER.info('AJW: handle show world time')
		
        loc_name = message.data.get("LocationKeyword")

        # set a default location in none provided
        if loc_name:
            loc_name = loc_name.replace(' ', '_')
        else:
            loc_name = self.default_location

        if (self.protocol == "mqtt"):
            mqttc = mqtt.Client("MycroftAI")            
            if (self.mqttssl == "yes"):
                mqttc.tls_set(self.mqttca)
            LOGGER.info("AJW - connect to: " + self.mqtthost)
            LOGGER.info("AJW - connect to: " + str(self.mqttport))
            mqttc.connect(self.mqtthost,self.mqttport,10)
            mqttc.publish(loc_name + "/display/worldtime", "")
            mqttc.disconnect()
            self.speak_dialog("cmd.sent")
        else:
#            self.speak_dialog("not.found", {"command": cmd_name, "action": act_name, "module": dev_name})
            LOGGER.error("Error: {0}".format(e))

    @intent_handler(IntentBuilder('handle_dataRequest_command').require("RequestKeyword").require("SensorKeyword").require("LocationKeyword"))
    def handle_dataRequest_command(self, message):
	# example: "what is the temperature on the deck"
		
        LOGGER.info('AJW: handle control command')
		
        req_name = message.data.get("RequestKeyword")
        sen_name = message.data.get("SensorKeyword")
        loc_name = message.data.get("LocationKeyword")

        # set a default location in none provided
        if loc_name:
            loc_name = loc_name.replace(' ', '_')
        else:
            loc_name = self.default_location

        self.mqtt_connect(dataRequestTopic)
        self.mqtt_publish("request/" + sen_name + "/" + loc_name, "")
        self.mqtt_disconnect()

#    def stop(self):
#        pass

    def on_message(self, mqttClient, userdata, msg):
        LOGGER.info('AJW: Topic = ' + msg.topic)
        splitTopic = msg.topic.split('/')
        if splitTopic[0] == 'send':
            LOGGER.info('AJW: Received a message')
            self.speak_dialog("sensor.value", {"location": splitTopic[2], "sensor": splitTopic[1], "value": msg.payload})
            return
        if msg.topic == actionConfirmationTopic:
            if msg.payload == '1':
                LOGGER.info('AJW: Requested action was successful')
                self.speak_dialog('action.successful')
            else:
                LOGGER.info('AJW: Requested action was unsuccessful')
                self.speak_dialog('action.unsuccessful')
            return


#    def converse(self, utterances, lang="en-us"):
#        if utterances != None:
#            LOGGER.info('Utterance = ' + str(utterances))
#            return True  # Conversation handled successfully
#        else:
#            LOGGER.info('Received a NULL utterance. Why??')
#            return False


def create_skill():
    return mqttskill()
