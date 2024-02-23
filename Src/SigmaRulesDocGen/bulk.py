import argparse
import json
import re
import glob
import requests
from requests.auth import HTTPBasicAuth
import configparser
from os.path import exists
import math
import yaml
import urllib3

# Disable HTTPS/TLS certificate warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--debug", "-d", help="For debugging", action=argparse.BooleanOptionalAction)
parser.add_argument("--config", help="Config Filename", default="config.ini")
parser.add_argument("--verbose", help="Verbose output.", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--function", help="Type of operation/function to do [delete]",choices=['delete'], required=True)
parser.add_argument("--file", help="File to use for bulk operation", required=True)

args = parser.parse_args()
configFromArg = vars(args)

strIndentOne = "    "
strIndentTwo = "        "
strIndentThree = "            "
strIndentFour = "                "

# font
#           Style
#           v Color
#           v v  Background
#           v v  v
defText = "\033[0;30;50m"
alertText = "\033[1;33;50m"
errorText = "\033[1;31;50m"
successText = "\033[1;32;50m"

print(defText)

# Colors
# 
# Example
# Text Style;Color;Background
# 
# Text Style
#   No Effect   0
#   Bold        1
#   Underline   2
#   Negative1   3
#   Negative2   5
# 
# Color
#   Black       30
#   Red         31
#   Green       32
#   Yellow      33
#   Blue        34
#   Purple      35
#   Cyan        36
#   White       37
# 
# Backgrounds
#   Black       40
#   Red         41
#   Green       42
#   Yellow      43
#   Blue        4475
#   Purple      45
#   Cyan        46
#   White       47

sAuthFile = configFromArg['config']

if configFromArg['debug']:
    print("DEBUG ENABLED")
    print("")

# load config file for server info, auth info
config = configparser.ConfigParser()
if exists(sAuthFile):
    config.read(sAuthFile)
else:
    print(errorText + "ERROR! Config file " + sAuthFile + " does not exist!" + defText)
    exit()

# build URI
sArgBuildUri = ""
sArgHttps = config['DEFAULT']['https']
if sArgHttps == "true":
    sArgBuildUri = "https://"
else:
    sArgBuildUri = "http://"

sArgHost = config['DEFAULT']['host']
sArgPort = config['DEFAULT']['port']
sArgUser = config['DEFAULT']['user']
sArgPw = config['DEFAULT']['password']

# build server:host and concat with URI
sArgBuildUri=sArgBuildUri+sArgHost+":"+sArgPort

# print("Graylog Server: " + sArgHost)
print(alertText + "Target Graylog Server: " + successText + sArgHost + defText)

def doHttpToDeleteRulesByIdList(argListOfIds):
    # specify URL
    sUrl = sArgBuildUri + "/api/plugins/org.graylog.plugins.securityapp.sigma/sigma/rules/bulk/delete"
    # headers
    sHeaders = {"Accept":"application/json", "X-Requested-By":"python"}
    # send req, upload json content pack file
    oJson = {"ids": argListOfIds}
    r = requests.put(sUrl, json = oJson, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
    if r.status_code == 200:
        print(successText + "SUCCESS" + defText)
        print(r.text)
    else:
        print(errorText + "Error: " + str(r.status_code) + " (" + r.text + ")" + defText)

def convertIdsOnePerLineToList(argRaw):
    lOutput = []
    list = argRaw.split('\n')
    for item in list:
        if item != "":
            lOutput.append(item)
    
    return lOutput

def doDeleteRulesByIds(argFileWithIds):
    if exists(argFileWithIds):
        raw = open(argFileWithIds).read()
        listIds = convertIdsOnePerLineToList(raw)
        print(listIds)
        doHttpToDeleteRulesByIdList(listIds)
    else:
        print(errorText + "ERROR! File " + argFileWithIds + " does not exist!" + defText)

if configFromArg['function'] == "delete":
    print(alertText + "Deleting Rules by ID..." + defText)
    doDeleteRulesByIds(configFromArg['file'])
elif configFromArg['function'] == "ids":
    print("1")
else:
    print(errorText + "ERROR! Invalid function." + defText)
