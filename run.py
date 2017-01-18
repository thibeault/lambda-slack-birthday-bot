# coding: latin-1

from __future__ import print_function

import json
import boto3 #### NEW
import os #### NEW
from datetime import datetime, date
from slackclient import SlackClient
from base64 import b64decode #### NEW


#### NEW
# The base-64 encoded, encrypted key (CiphertextBlob) stored in the kmsEncryptedHookUrl environment variable
ENCRYPTED_TOKEN = os.environ['kmsEncryptedToken']
# The Slack channel to send a message to stored in the slackChannel environment variable
SLACK_CHANNEL = os.environ['slackChannel']

token =  boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTED_TOKEN))['Plaintext']
#### NEW

print('Loading function')


def lambda_handler(event, context):
    # The 2 lines below work to open the json file and read the json file
    # This is where the bot is very bare, as you need to download the list of users on your team
    json_file = open('file.json')
    json_string = json_file.read()

    # This is where the json data is being stored into a dictionary
    jdata = json.loads(json_string)

    #gets todays date
    today = date.today()
    sc = SlackClient(token)
    friends = "None"
    #rtm_connect is a command from the slack-client docs
    for value in jdata['members']:
        checker = datetime.strptime(value['birthday'], "%Y-%m-%d").date()
        if checker.month == today.month and checker.day == today.day:

            if sc.rtm_connect():

                #custom message for the birthday person
                message = " Bonne fête @" + value['name'] + " :birthday:. De tous les snoros :-)"
                friends = value['name']
                # The actual command to post the message, which is also printed out to the console
                # The print may be a good way to keep logs :)
                #print message
                print(sc.api_call("chat.postMessage", as_user="true:", channel=SLACK_CHANNEL, text=message))
            else:
                print("Connection Failed, invalid token?")

    #return token
    return str(datetime.now())

