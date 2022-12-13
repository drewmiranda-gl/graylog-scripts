#       Install python 3.10
# sudo apt install software-properties-common -y
# sudo add-apt-repository ppa:deadsnakes/ppa
# sudo apt install python3.10
#       set as default
# sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

#       crontab
# */5 * * * * sudo python3 /home/drew/export-http.py --config /home/drew/auth.ini --out /var/www/html/prom/out.out >/dev/null 2>&1

import requests
from requests.auth import HTTPBasicAuth
import configparser
import json
import glob
import argparse
import re
import sqlite3
from os.path import exists
import os

# defaults
parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--debug", "-d", help="For debugging", action=argparse.BooleanOptionalAction)
parser.add_argument("--config", help="Config Filename", default="config.ini")
parser.add_argument("--verbose", help="Verbose output.", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--out", help="Output file", default="out.out")

args = parser.parse_args()
configFromArg = vars(args)

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
#   Blue        44
#   Purple      45
#   Cyan        46
#   White       47

print("Arguments: ")
print(configFromArg)
print("")

sAuthFile = configFromArg['config']

if configFromArg['debug']:
    print("DEBUG ENABLED")
    print("")

# load config file for server info, auth info
config = configparser.ConfigParser()
config.read(sAuthFile)

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

# print("Graylog Server: " + sArgHost)
print(alertText + "Graylog Server: " + sArgHost + defText + "\n")

# build server:host and concat with URI
sArgBuildUri=sArgBuildUri+sArgHost+":"+sArgPort

def queryGraylog(strArgFields):
    dictRs = {}
    thisKey = ""
    thisValue = ""

    # print(alertText + "Searching Graylog " + defText + ": " + strArgQuery + defText)
    sResult = ""

    sUrl = sArgBuildUri + "/api/views/search"
    
    sHeaders = {"Accept":"application/json", "X-Requested-By":"python"}

    strQueryConcat = ""
    for sField in strArgFields:
        if len(strQueryConcat) > 0:
            strQueryConcat = strQueryConcat + " OR "
        strQueryConcat = strQueryConcat + "_exists_:" + sField
    strQueryConcat = "(" + strQueryConcat + ")"

    # oJson = {"parameters":{},"comment":""}
    oPayload = {}
    oQuery = {}
    oQuery["query"] = {"type": "elasticsearch", "query_string": strQueryConcat}
    oQuery["timerange"] = {"from": 3600, "type": "relative"}

    lSeries = []
    for sField in strArgFields:
        lSeries.append({"field": str(sField), "id": str(sField), "type": "latest"})
    
    oQuerySearchTypes = {
        "name": "chart",
        "series": lSeries,
        "rollup": True,
        "row_groups": [],
        "type": "pivot"
    }
    oQuery["search_types"] = [oQuerySearchTypes]
    
    oPayload["queries"] = [oQuery]

    r = requests.post(sUrl, json = oPayload, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
    
    if configFromArg['verbose']:
        print(r.status_code)
        print(r.headers)
        print(r.text)

    oRespJson = json.loads(r.text)
    sSearchId = oRespJson['id']
    
    sUrl = sArgBuildUri + "/api/views/search/" + str(sSearchId) + "/execute"
    oJsonExecute = {"parameter_bindings":{}}
    r = requests.post(sUrl, json = oJsonExecute, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
    if configFromArg['verbose']:
        print(r.status_code)
        print(r.headers)
        print(r.text)

    oSearchRsJson = json.loads(r.text)
    # print(r.text)
    oRs = oSearchRsJson['results']

    for oSearchResult in oRs:
        oResultInResult = oRs[oSearchResult]['search_types']
        for oFinalResultGuid in oResultInResult:
            thisKey = ""
            thisValue = ""

            if 'rows' in oRs[oSearchResult]['search_types'][oFinalResultGuid]:
                lRows = oRs[oSearchResult]['search_types'][oFinalResultGuid]['rows']

                if len(lRows) > 0:
                    if 'values' in lRows[0]:
                        oValues = lRows[0]['values']
                        if len(oValues) > 0:
                            for value in oValues:

                                if 'key' in value:
                                    if len(value['key']) > 0:
                                        thisKey = value['key'][0]
                            
                                if 'value' in value:
                                    thisValue = value['value']
                                
                                if len(str(thisKey)) and len(str(thisValue)):
                                    dictRs[thisKey] = thisValue
    
    return dictRs

def writeToFile(handle, text):
    handle.write(text + "\n")

rs = queryGraylog(["aq_co2", "aq_temp_f"])
if len(rs) > 0:
    sFileTemp = configFromArg['out'] + ".tmp"
    if exists(sFileTemp):
        os.remove(sFileTemp)

    f = open(sFileTemp, "a")

    for metric in rs:
        sLineToWrite = metric + "{} " + str(rs[metric])
        writeToFile(f, sLineToWrite)

    if exists(sFileTemp):
        os.rename(sFileTemp,configFromArg['out'])
