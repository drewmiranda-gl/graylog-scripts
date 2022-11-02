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

parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--debug", "-d", help="For debugging", action=argparse.BooleanOptionalAction)
parser.add_argument("--config", help="Config Filename", default="config.ini")
parser.add_argument("--verbose", help="Verbose output.", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--perpage", help="Items Per Page.", default=15)
parser.add_argument("--startpage", help="Items Per Page.", default=1)
parser.add_argument("--endpage", help="Items Per Page.", default=10000)
parser.add_argument("--function", help="[markdown|ids] Type of operation/function to do", default="markdown")

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

iPerPage = int(configFromArg['perpage'])
iStartPage = int(configFromArg['startpage'])
iEndPage = int(configFromArg['endpage'])

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

def buildUrl(iArgPage, iArgPerPage):
    sUrl = sArgBuildUri + "/api/plugins/org.graylog.plugins.securityapp.sigma/sigma/rules?page=" + str(iArgPage) +"&per_page=" + str(iArgPerPage) +"&sort=parsed_rule.title&direction=asc"
    return sUrl

def doProcessRules(oArgJsonSigmaRules):
    dictForResp = {}

    for rule in oArgJsonSigmaRules:
        dictTemp = {}
        # print("================================================================")
        # print(rule)
        
        # dictTemp["title"] = rule["title"]
        # dictTemp["query"] = rule["query"]
        dictForResp[rule["id"]] = rule
    return dictForResp

def getRulesPageFromApi(iArgPage, iArgPerPage, iArgMax):
    # specify URL
    sUrl = buildUrl(iArgPage, iArgPerPage)
    # headers
    sHeaders = {"Accept":"application/json", "X-Requested-By":"python"}
    # send req, upload json content pack file
    # if configFromArg['verbose']:
    print("Web Req: " + str(iArgPage) + " of " + str(iArgMax))
    r = requests.get(sUrl, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
    return r

def generateMarkDown(sArgRules):
    sConcat = ""
    for rule in sArgRules:
        print("")
        print("### " + sArgRules[rule]["title"])
        print("")

        print("Config | Value")
        print("---- | ----")

        # Level
        print("Level | `" + str(sArgRules[rule]["level"]) + "`")

        # Query
        print("Search Query | `" + str(sArgRules[rule]["query"]) + "`")

        # Source
        # print("Source Yaml | `" + str(sArgRules[rule]["source"]) + "`")
        dct = yaml.safe_load(sArgRules[rule]["source"])
        sConcat = "- Description: " + dct["description"]
        sConcat = sConcat + "<br>" + "- Author: " + dct["author"]
        print("Source Yaml | " + str(sConcat) + "")

def doExportRuleQueries():
    list = []
    dictSigmaRules = {}

    iPage = iStartPage

    iTotalRules = 0
    iCurrentPage = 0
    iCountOnThisPage = 0

    iInternalCounter = 0

    r = getRulesPageFromApi(iPage, iPerPage, "?")

    bProcessNext = True

    if r.status_code == 200:
        oJsonResp = json.loads(r.text)
        iTotalRules = oJsonResp["total"]
        iCurrentPage = oJsonResp["page"]
        iCountOnThisPage = oJsonResp["count"]

        iMaxPages = math.ceil(iTotalRules / iCountOnThisPage)
        # 1 less page for loop since we already did first page
        iMaxPagesForLoop = (iMaxPages - 1)

        rs = doProcessRules(oJsonResp["sigma_rules"])
        list.append(rs)
        
        # do we need to loop?
        if iTotalRules > iCountOnThisPage:
            while iInternalCounter < iMaxPagesForLoop:
                iInternalCounter = iInternalCounter + 1
                iPage = iPage + 1
                # print("Page: " + str(iPage))

                if iPage > iEndPage:
                    print(alertText + "ALERT: stopping because page " + str(iPage) + " is greater than end page (" + str(iEndPage) + ")" + defText)
                    bProcessNext = False
                    break
                if iPage > iMaxPages:
                    bProcessNext = False
                    break
                
                if bProcessNext:
                    r = getRulesPageFromApi(iPage, iPerPage, iMaxPages)
                    if r.status_code == 200:
                        oJsonResp = json.loads(r.text)
                        rs = doProcessRules(oJsonResp["sigma_rules"])
                        list.append(rs)

        # json_object = json.dumps(rs, indent = 4)
        # print(json_object)

        for item in list:
            for rule in item:
                dictSigmaRules[rule] = item[rule]

        return dictSigmaRules
    else:
        print(errorText + "Error: " + str(r.status_code) + " (" + r.text + ")" + defText)
        exit()

def generateRuleIds(sArgRules):
    for rule in sArgRules:
        print(rule)

if configFromArg['function'] == "markdown":
    rules = doExportRuleQueries()
    # json_object = json.dumps(rules, indent = 4)
    # print(json_object)
    generateMarkDown(rules)
elif configFromArg['function'] == "ids":
    rules = doExportRuleQueries()
    generateRuleIds(rules)
else:
    print(errorText + "ERROR! Invalid function." + defText)
