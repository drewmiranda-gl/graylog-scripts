import requests
from requests.auth import HTTPBasicAuth
import configparser
import json
import glob
import argparse
import re
import sqlite3
from os.path import exists
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# defaults
parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--debug", "-d", help="For debugging", action=argparse.BooleanOptionalAction)
parser.add_argument("--config", help="Config Filename", default="config.ini")
parser.add_argument("--verbose", help="Verbose output.", action=argparse.BooleanOptionalAction, default=False)

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
blueText = "\033[0;34;50m"

print(defText)

print("Script START - dns_ip_search")

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
if exists(sAuthFile):
    config.read(sAuthFile)
else:
    print(errorText + "ERROR, cannot load config file or does not exist: " + blueText + sAuthFile + defText)
    exit(1)

# build URI
sArgBuildUri = ""
sArgHttps = config['DEFAULT']['https']
if sArgHttps == "true":
    sArgBuildUri = "https://"
    bApiHttps = True
else:
    sArgBuildUri = "http://"
    bApiHttps = False

sArgHost = config['DEFAULT']['host']
sArgPort = config['DEFAULT']['port']
sArgUser = config['DEFAULT']['user']
sArgPw = config['DEFAULT']['password']

dictGraylogApi = {
    "https": bApiHttps,
    "host": sArgHost,
    "port": sArgPort,
    "user": sArgUser,
    "password": sArgPw
}

# print("Graylog Server: " + sArgHost)
print(alertText + "Graylog Server: " + sArgHost + defText + "\n")

# build server:host and concat with URI
sArgBuildUri=sArgBuildUri+sArgHost+":"+sArgPort

def graylogApiConfigIsValid():
    if 'https' in dictGraylogApi:
        if not dictGraylogApi['https'] == True and not dictGraylogApi['https'] == False:
            return False
    else:
        return False
    
    if 'host' in dictGraylogApi:
        if not len(dictGraylogApi['host']) > 0:
            return False
    else:
        return False

    if 'port' in dictGraylogApi:
        if not len(dictGraylogApi['port']) > 0 and not int(dictGraylogApi['port']) > 0:
            return False
    else:
        return False

    if 'user' in dictGraylogApi:
        if not len(dictGraylogApi['user']) > 0:
            return False
    else:
        return False

    if 'password' in dictGraylogApi:
        if not len(dictGraylogApi['password']) > 0:
            return False
    else:
        return False
    
    return True

def mergeDict(dictOrig: dict, dictToAdd: dict, allowReplacements: bool):
    for item in dictToAdd:
        
        bSet = True
        if item in dictOrig:
            if allowReplacements == False:
                bSet = False
        
        if bSet == True:
            dictOrig[item] = dictToAdd[item]
    
    return dictOrig

def doGraylogApi(argMethod: str, argApiUrl: str, argHeaders: dict, argJson: dict, argFiles: dict, argExpectedReturnCode: int, argReturnJson: bool):
    if graylogApiConfigIsValid() == True:
        # build URI
        sArgBuildUri = ""
        if dictGraylogApi['https'] == True:
            sArgBuildUri = "https://"
        else:
            sArgBuildUri = "http://"

        sArgHost    = dictGraylogApi['host']
        sArgPort    = dictGraylogApi['port']
        sArgUser    = dictGraylogApi['user']
        sArgPw      = dictGraylogApi['password']

        # print(alertText + "Graylog Server: " + sArgHost + defText + "\n")

        # build server:host and concat with URI
        sArgBuildUri=sArgBuildUri+sArgHost+":"+sArgPort
        
        sUrl = sArgBuildUri + argApiUrl

        # add headers
        sHeaders = {"Accept":"application/json", "X-Requested-By":"python-ctpk-upl"}
        sHeaders = mergeDict(sHeaders, argHeaders, True)
        
        if argMethod.upper() == "GET":
            try:
                r = requests.get(sUrl, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
            except Exception as e:
                return {
                    "success": False,
                    "exception": e
                }
        elif argMethod.upper() == "POST":
            if argFiles == False:
                try:
                    r = requests.post(sUrl, json = argJson, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
                except Exception as e:
                    return {
                        "success": False,
                        "exception": e
                    }
            else:
                try:
                    r = requests.post(sUrl, json = argJson, files=argFiles, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
                except Exception as e:
                    return {
                        "success": False,
                        "exception": e
                    }
        
        if r.status_code == argExpectedReturnCode:
            if argReturnJson:
                return {
                    "json": json.loads(r.text),
                    "status_code": r.status_code,
                    "success": True
                }
            else:
                return {
                    "text": r.text,
                    "status_code": r.status_code,
                    "success": True
                }
        else:
            return {
                "status_code": r.status_code,
                "success": False,
                "failure_reason": "Return code " + str(r.status_code) + " does not equal expected code of " + str(argExpectedReturnCode),
                "text": r.text
            } 
    else:
        return {"msg": "api_not_configured"}

def buildGraylogSearchJson(argQuery: str, timerange: int, streams: list, aggType: str, aggFiled: str, groupBy: str):
    oPayload = {}
    oQuery = {}
    oQuery["query"] = {}
    oQuery["query"]['type'] = 'elasticsearch'
    oQuery["query"]['query_string'] = ''

    oQuery["timerange"] = {"from": timerange, "type": "relative"}


    # ================================================================
    # Search Type Start
    oSearchType = {}
    oSearchType['timerange'] = oQuery["timerange"]
    oSearchType["query"] = {}
    oSearchType["query"]['type'] = 'elasticsearch'
    oSearchType["query"]['query_string'] = argQuery
    oSearchType["streams"] = streams
    oSearchType["name"] = "chart"

    oSearchTypeSeries = {}
    oSearchTypeSeries['type']   = aggType
    oSearchTypeSeries['id']     = ""
    oSearchTypeSeries['field']  = aggFiled
    oSearchType["series"] = [oSearchTypeSeries]

    oSearchType['rollup'] = True
    oSearchType['type'] = "pivot"

    oSearchTypeRowGroups = {}
    oSearchTypeRowGroups['type'] = "values"
    oSearchTypeRowGroups['fields'] = [groupBy]
    oSearchTypeRowGroups['limit'] = 15
    oSearchType["row_groups"] = [oSearchTypeRowGroups]

    oQuery['search_types'] = [oSearchType]
    # Search Type End
    # ================================================================


    oPayload["queries"] = [oQuery]
    return oPayload

def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False

def formatGraylogQueryOutput(argResult: dict, searchType: str, addValues: dict):
    if not "results" in argResult:
        return {"error": "key 'results' not found"}
    
    rs = []
    # kv = {}

    # print(json.dumps(argResult['results'], indent = 4))
    for result in argResult['results']:
        # print(json.dumps(argResult['results'][result]['search_types'], indent = 4))
        for search_type in argResult['results'][result]['search_types']:
            for row in argResult['results'][result]['search_types'][search_type]['rows']:
                if row['source'] == "leaf":
                    kv = {}
                    use_key = row['key'][0]
                    use_value = row['values'][0]['value']
                    # kv[use_key] = use_value

                    if isinstance(use_value, float):
                        valuename = "value_float"
                    elif isinstance(use_value, int):
                        valuename = "value_int"
                    else:
                        valuename = "value"
                    
                    kv = {
                        "key": use_key,
                        valuename: use_value
                    }
                    final_dict = mergeDict(kv, addValues, True)

                    rs.append(final_dict)
    
    return rs

def sendMessageToGraylogGelfHttp(HOST: str, PORT: int, payload: list):

    sUrl = "http://" + str(HOST) + ":" + str(PORT) + "/gelf"

    sHeaders = {
        "Content-Type": "application/json",
        "User-Agent": "python"
    }

    # print(json.dumps(payload, indent=4))
    r = requests.post(sUrl, data = payload, headers=sHeaders)
    print("Graylog Input:" + str(r.status_code))

def logBackToGraylog(HOST: str, PORT: int, messages: list):

    pyaload_concat = ""
    for message in messages:
        pyaload_concat = pyaload_concat + json.dumps(message) + "\n"

    sendMessageToGraylogGelfHttp(HOST, PORT, pyaload_concat)

def queryGraylog(argQuery: dict):
    r = doGraylogApi("POST", "/api/views/search", {}, argQuery, False, 201, True)
    if not 'success' in r:
        return {'error': 'search creation req result does not contain a success value'}

    if not r['success'] == True:
        return {'error': 'search creation req success is NOT true'}

    if not 'json' in r:
        return {'error': 'rsearch creation req esult does not contain a json value'}

    if not 'id' in r['json']:
        return {'error': 'search creation req result json does not contain an id value'}

    search_id = r['json']['id']
    rr = doGraylogApi("POST", "/api/views/search/" + str(search_id) + "/execute", {}, {"parameter_bindings":{}}, False, 201, True)
    if not 'success' in rr:
        return {'error': 'search result does not contain a success value'}

    if not rr['success'] == True:
        return {'error': 'search result success is NOT true'}

    if not 'json' in rr:
        return {'error': 'search result does not contain a json value'}

    return rr['json']

graylog_host = "ubu4310.drew.local"
graylog_port = 12202

queries_list = [
    {
        "query"             : "_exists_:ha_event_new_state_double AND ha_sensor_type:current_consumption",
        "timerange"         : 300,
        "streams"           : ["6317aaae5c2b2b19d63ad77a"],
        "aggregation_field" : "ha_event_new_state_double",
        "aggregation_type"  : "latest",
        "group_gy"          : "ha_entity"
    }
]

for query in queries_list:
    j = buildGraylogSearchJson(
        query['query'],
        query['timerange'],
        query['streams'],
        query['aggregation_type'],
        query['aggregation_field'],
        query['group_gy'],
        )

    r = queryGraylog(j)
    f = formatGraylogQueryOutput(r, "aggregation", {"source": "query-and-log-agg", "message": "-", "measurement": "W", "item": "energy_usage"})
    logBackToGraylog(graylog_host, graylog_port, f)

# t = json.dumps(f, indent=4)
# print(t)
