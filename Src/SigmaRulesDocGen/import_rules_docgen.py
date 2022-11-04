import argparse
import json
import re
import glob
import requests
from requests.auth import HTTPBasicAuth
import configparser
from os.path import exists

parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--debug", "-d", help="For debugging", action=argparse.BooleanOptionalAction)
parser.add_argument("--dir", help="Directory of sigma rules", default="rules")
parser.add_argument("--config", help="Config Filename", default="config.ini")
parser.add_argument("--verbose", help="Verbose output.", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--batch-size", help="Max number of rules to import with each API request.", default=100)
parser.add_argument("--method", help="[api|file] Import Sigma via local files or via github API", default="file")

args = parser.parse_args()
configFromArg = vars(args)

iBatchSize = int(configFromArg['batch_size'])

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

# print("Graylog Server: " + sArgHost)
print(alertText + "Target Graylog Server: " + successText + sArgHost + defText)
print(alertText + "Rules Import Method: " + successText + configFromArg['method'] + defText + "\n")

# build server:host and concat with URI
sArgBuildUri=sArgBuildUri+sArgHost+":"+sArgPort

listSigmaRulesToImport = []

gIntSuccess = 0
gIntFailure = 0
gIntTotalWebReqs = 0

def doBuildSigmaImportList(argFile):
    listSigmaRulesToImport.append(argFile)

def doImportSigmaRulesUsingList(argList):
    global gIntSuccess
    global gIntFailure

    intListItemCount = len(argList)
    print(strIndentOne + "Importing " + successText + str(intListItemCount) + defText + " sigma rules...")
    # print(argList)

    if configFromArg['debug']:
        print(alertText + "debug enabled, skipping upload web req" + defText + "\n")
    else:
        if configFromArg['method'] == "api":
            # =====================================================================
            # using import via Github API
            # specify URL
            sUrl = sArgBuildUri + "/api/plugins/org.graylog.plugins.securityapp.sigma/sigma/rules/import"
            # headers
            sHeaders = {"Accept":"application/json", "X-Requested-By":"python"}
            # send req, upload json content pack file
            oJson = {"keys": argList}
            r = requests.post(sUrl, json = oJson, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
            
            if r.status_code == 200:
                if configFromArg['verbose']:
                    print(strIndentOne + successText + "Web Request Successful." + defText)

                # print(r.text)
                oJsonResp = json.loads(r.text)
                print(strIndentOne + "Success Count: " + successText + str(oJsonResp["success_count"]) + defText + " " + "Failure Count: " + errorText + str(oJsonResp["failure_count"]) + defText)
                
                gIntSuccess = gIntSuccess + oJsonResp["success_count"]
                gIntFailure = gIntFailure + oJsonResp["failure_count"]
                
                for strError in oJsonResp["errors"]:
                    print("\n" + strIndentOne + errorText + strError + defText)
            else:
                print(strIndentOne + errorText + "Error: " + str(r.status_code) + " (" + r.text + ")" + defText)
        
        if configFromArg['method'] == "file":
            # =====================================================================
            # upload file
            # specify URL
            sUrl = sArgBuildUri + "/api/plugins/org.graylog.plugins.securityapp.sigma/sigma/rules"
            # headers
            sHeaders = {"Accept":"application/json", "X-Requested-By":"python"}

            for fileName in argList:
                print("Uploading file: " + fileName + defText)
                raw = open(fileName).read()

                # send req, upload json content pack file
                oJson = {
                    "search_within_ms": 900000,
                    "execute_every_ms": 900000,
                    "streams": [],
                    "source": raw
                }
                # print(oJson)
                r = requests.post(sUrl, json = oJson, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
                # print("Status Code: " + str(r.status_code))
                # print(r.text)
                if r.status_code == 200:
                    # if configFromArg['verbose']:
                    print(strIndentOne + successText + "Success" + defText)
                    gIntSuccess = gIntSuccess + 1
                else:
                    if r.status_code == 400:
                        oJsonResp = json.loads(r.text)
                        if "message" in oJsonResp:
                        print("" + strIndentOne + "ERROR: " + errorText + oJsonResp["message"] + defText)
                    else:
                            print("" + strIndentOne + "ERROR: " + errorText + str(oJsonResp) + defText)
                    else:
                        print(strIndentOne + errorText + "Error: " + str(r.status_code) + " (" + r.text + ")" + defText)
                    gIntFailure = gIntFailure + 1

        # print(r.headers)

def doSplitListByMaxAllowed(argList):
    global gIntTotalWebReqs

    iBatchCount = 1
    iItemCount = 0
    intToUseForBatchSizeInIf = iBatchSize - 1
    
    dictLists = {}
    
    # init temp list and temp count
    listList = []
    iBuildNewListCount = 1

    iListCount = len(argList)

    intTotalRulesAddedToDict = 0

    doReset = False

    print("Batch Size: " + str(iBatchSize) + "")

    if iListCount > iBatchSize:
        # split into multiple lists
        for i in argList:
            iItemCount = iItemCount + 1
            # print("Item " + str(iItemCount) + " of " + str(iListCount) + " (iBuildNewListCount: " + str(iBuildNewListCount) + ")")

            listList.append(i)

            if iBuildNewListCount > intToUseForBatchSizeInIf:
                doReset = True
            if iItemCount == iListCount:
                doReset = True
            
            if doReset == True:
                doReset = False
                # store list at max batch size in dictionary of lists
                dictLists[iBatchCount] = listList

                # increment batch size
                iBatchCount = iBatchCount + 1

                # reset list and temp counter
                listList = []
                iBuildNewListCount = 0
                intTotalRulesAddedToDict = intTotalRulesAddedToDict + iBatchSize
            
            
            iBuildNewListCount = iBuildNewListCount + 1

        # iterate through dictionary of lists
        intTotalWebReqsNeededForImport = len(dictLists)
        gIntTotalWebReqs = intTotalWebReqsNeededForImport
        for intListCount in dictLists:
            # print("=============================================================================")
            # print(intListCount)
            # print(dictLists[intListCount])
            if configFromArg['method'] == "api":
            print("\n"+ alertText + "Web Request " + str(intListCount) + " of " + str(intTotalWebReqsNeededForImport) + defText)
            doImportSigmaRulesUsingList(dictLists[intListCount])
    else:
        doImportSigmaRulesUsingList(argList)


# =============================================================================
# =============================================================================
# =============================================================================

print("Loading from directory \"" + successText + configFromArg["dir"] + defText + "\"" + "\n")

oFiles = glob.glob(configFromArg["dir"] + "/**/*.yml", recursive=True)
for file in oFiles:
    if configFromArg['verbose']:
        print(file)
    doBuildSigmaImportList(file)
if configFromArg['verbose']:
    print("")

print("Found " + successText + str(len(listSigmaRulesToImport)) + defText + " sigma rules.")

doSplitListByMaxAllowed(listSigmaRulesToImport)

print("")
print("Total Success Count: " + successText + str(gIntSuccess) + defText + "\n" + "Total Failure Count: " + errorText + str(gIntFailure))