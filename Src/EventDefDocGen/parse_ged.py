import argparse
import json
import re
import glob

parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--debug", "-d", help="For debugging", action=argparse.BooleanOptionalAction)
# parser.add_argument("--file", help="Graylog Anomaly Detection rules json file", required=True)

args = parser.parse_args()
configFromArg = vars(args)

# print("Arguments: ")
# print(configFromArg)
# print("")

def outputMarkdownForJson(argJson, sContentPackName, sContentPackRev):
    oJsEnt = argJson
    listAnomDetRules = []
    dictAnomDetRules = {}

    for oEnt in oJsEnt:
        sName = oEnt['data']['title']['@value']
        dictAnomDetRules[sName] = oEnt
        listAnomDetRules.append(sName)

    listAnomDetRules.sort()

    for anomRuleTitle in listAnomDetRules:
        # sConcat = anomRuleTitle
        print("")
        print("### " + anomRuleTitle)
        print("")

        jsonRule = dictAnomDetRules[anomRuleTitle]

        # Description
        sDesc = jsonRule['data']['description']['@value']
        print(sDesc)
        print("")

        print("Config | Value")
        print("---- | ----")

        # Requirements
        sConstraints = jsonRule['constraints']
        # print("### Requirements: ")
        sConcat = ""
        for sConstraint in sConstraints:
            sConcat = sConcat + "- " + sConstraint['type'] + ": " + sConstraint['version'] + "<br>"
        print("Requirements | " + sConcat)

        # Priority
        sPri = jsonRule['data']['priority']['@value']
        print("Priority | " + str(sPri))

        # Type (filter/aggregation)
        sType = jsonRule['data']['config']['type']
        print("Type | " + str(sType))

        # Search Query
        sSrchQry = jsonRule['data']['config']['query']['@value']
        print("Search Query | `" + str(sSrchQry) + "`")

        # streams
        lStreams = jsonRule['data']['config']['streams']
        iStreamCount = 0
        sConcat = ""
        for sStream in lStreams:
            iStreamCount +=1
            sConcat = sConcat + "- " + sStream + "<br>"
        
        if ( iStreamCount > 0 ):
            sTextForSteams = sConcat
        else:
            sTextForSteams = "No Streams selected, searches in all Streams"
        
        print("Stream(s) | " + sTextForSteams)

        # search within (search_within_ms)
        iSearchWithinMs = jsonRule['data']['config']['search_within_ms']
        print("Search within | " + convertMsToText(iSearchWithinMs))

        # execute search ever (execute_every_ms)
        iExecuteEveryMs = jsonRule['data']['config']['execute_every_ms']
        print("Search within | " + convertMsToText(iExecuteEveryMs))

        # is_scheduled
        bIsScheduled = jsonRule['data']['is_scheduled']['@value']
        print("Enable scheduling | " + convertBoolToYesNo(bIsScheduled))

        # group by

        # fields
        print("")
        print("#### Fields")
        print("")

        print("Field | Data Type | Value Source | Template")
        print("---- | ---- | ---- | ----")

        jsonFields = jsonRule['data']['field_spec']
        for jsonField in jsonFields:
            sField = jsonField
            sDataType = jsonFields[jsonField]['data_type']
            sValueSource = convertValueSource(jsonFields[jsonField]['providers'][0]['type'])
            sTemplate = jsonFields[jsonField]['providers'][0]['template']
            print(sField + " | " + sDataType + " | " + sValueSource + " | `" + sTemplate + "`")

        # break

def convertMsToText(argInt):
    sRet = "0"
    sUnit = " milliseconds"
    sWorkingInt = argInt

    # to seconds
    if ( sWorkingInt > 0 ):
        # convert ms to s
        if ( sWorkingInt > 999 ):
            sUnit = " seconds"
            sWorkingInt = round(sWorkingInt / 1000)
            sRet = str(sWorkingInt) + sUnit
        
        # convert s to m
        if ( sWorkingInt > 59 ):
            sUnit = " minutes"
            sWorkingInt = round(sWorkingInt / 60)
            sRet = str(sWorkingInt) + sUnit
        
        # convert m to h
        if ( sWorkingInt > 59 ):
            sUnit = " hours"
            sWorkingInt = round(sWorkingInt / 60)
            sRet = str(sWorkingInt) + sUnit
        
    return sRet

def convertBoolToYesNo(argBool):
    if ( argBool ):
        return "Yes"
    else:
        return "No"

def convertValueSource(argStr):
    return argStr

oFiles = glob.glob("*.json")
for file in oFiles:
    f = open (file, "r")
    oJson = json.loads(f.read())
    oJsEnt = oJson['entities']
    print("## " + oJson['name'] + " (Content Pack, Rev: " + str(oJson['rev']) + ")")
    outputMarkdownForJson(oJsEnt, oJson['name'], oJson['rev'])