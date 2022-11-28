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
import urllib.parse

parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--debug", "-d", help="For debugging", action=argparse.BooleanOptionalAction)
parser.add_argument("--config", help="Config Filename", default="config.ini")
parser.add_argument("--verbose", help="Verbose output.", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--perpage", help="Items Per Page. How many rules are returned from the graylog api at one time.", default=100)
parser.add_argument("--startpage", help="Start Page. Graylog Sigma Rules page to start from.", default=1)
parser.add_argument("--endpage", help="End Page. Graylog Sigma Rules page to end with. Useful to limit how many rules are exported at a given time.", default=10000)
parser.add_argument("--function", help="[markdown|ids] Type of operation/function to do. Markdown exports markdown files. IDs outputs a list of graylog IDs for each sigma rule, one per line. IDs are helpful for doing bulk deletes.", default="markdown")
parser.add_argument("--delete", help="Deletes existing markdown files (if present) before exporting rules to markdown.", action=argparse.BooleanOptionalAction, default=True)

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

def safeGetKeyFromDict(strKey, objDict, strDefault):
    if str(strKey) in objDict:
        ret = objDict[strKey]
        return ret
    else:
        return strDefault

def urlBuildHelper(strArgPath, strArgFile, strArgFileType):
    strFile = strArgFile

    bPrependUnderscore = False
    if strFile.lower() == "no category":
        bPrependUnderscore = True
    elif strFile.lower() == "no product":
        bPrependUnderscore = True
    elif strFile.lower() == "no service":
        bPrependUnderscore = True

    if bPrependUnderscore == True:
        strFile = "_" + strFile

    ret = urllib.parse.quote("../" + strArgPath + "/" + strFile + "." + strArgFileType)
    return ret

def generateMarkDown(sArgRules):
    global dictCounts
    
    import os

    dictRules = {}
    
    dictRulesByCategory = {}
    dictRulesByProduct = {}
    dictRulesByService = {}

    # logsource:
    #   category: application
    #   product: python

    # strFileToWriteMarkdownTo = "out.md"

    # if exists(strFileToWriteMarkdownTo):
    #     import os
    #     os.remove(strFileToWriteMarkdownTo)

    # open file for editing
    # f = open(strFileToWriteMarkdownTo, "a")

    sConcat = ""
    for rule in sArgRules:
        sFinalWriteRuleAsMarkDown = ""

        if "source" in sArgRules[rule]:
            dct = yaml.safe_load(sArgRules[rule]["source"])
            oLogSource = dct["logsource"]
            strCategory =   safeGetKeyFromDict("category", oLogSource, "No Category")
            strProduct =    safeGetKeyFromDict("product", oLogSource, "No Product")
            strService =    safeGetKeyFromDict("service", oLogSource, "No Service")

        dictCounts["category"][strCategory] = rule
        dictCounts["product"][strProduct] = rule
        dictCounts["service"][strService] = rule

        # print("")
        # print("### " + sArgRules[rule]["title"])
        # print("")
        strRuleTitle = sArgRules[rule]["title"]
        sFinalWriteRuleAsMarkDown = sFinalWriteRuleAsMarkDown + "" + "\n"
        sFinalWriteRuleAsMarkDown = sFinalWriteRuleAsMarkDown + "### " + strRuleTitle + "\n"
        sFinalWriteRuleAsMarkDown = sFinalWriteRuleAsMarkDown + "" + "\n"

        # print("Config | Value")
        # print("---- | ----")
        sFinalWriteRuleAsMarkDown = sFinalWriteRuleAsMarkDown + "Config | Value" + "\n"
        sFinalWriteRuleAsMarkDown = sFinalWriteRuleAsMarkDown + "---- | ----" + "\n"

        # Category
        # print("Category | " + str(strCategory) + "")
        sFinalWriteRuleAsMarkDown = sFinalWriteRuleAsMarkDown + "Category | [" + str(strCategory) + "]("+ urlBuildHelper("categories", str(strCategory), "md") + ")" + "\n"

        # Product
        # print("Product | " + str(strProduct) + "")
        sFinalWriteRuleAsMarkDown = sFinalWriteRuleAsMarkDown + "Product | [" + str(strProduct) + "]("+ urlBuildHelper("products", str(strProduct), "md") + ")" + "\n"

        # Service
        # print("Service | " + str(strService) + "")
        sFinalWriteRuleAsMarkDown = sFinalWriteRuleAsMarkDown + "Service | [" + str(strService) + "]("+ urlBuildHelper("services", str(strService), "md") + ")" + "\n"

        # Level
        # print("Level | `" + str(sArgRules[rule]["level"]) + "`")
        sFinalWriteRuleAsMarkDown = sFinalWriteRuleAsMarkDown + "Level | `" + str(sArgRules[rule]["level"]) + "`" + "\n"

        # Query
        # print("Search Query | `" + str(sArgRules[rule]["query"]) + "`")
        sFinalWriteRuleAsMarkDown = sFinalWriteRuleAsMarkDown + "Search Query | `" + str(sArgRules[rule]["query"]) + "`" + "\n"
        
        sConcat = "- Description: " + dct["description"]
        sConcat = sConcat + "<br>" + "- Author: " + dct["author"]
        sConcat = sConcat + "<br>" + "- Log Source: " + str(dct["logsource"])
        # print("Source Yaml | " + str(sConcat) + "")
        sFinalWriteRuleAsMarkDown = sFinalWriteRuleAsMarkDown + "Source Yaml | " + str(sConcat) + "" + "\n"
    
        dictRules[strRuleTitle] = sFinalWriteRuleAsMarkDown

        # =====================================================================
        # Categories
        bExists = False
        if strCategory in dictRulesByCategory:
            bExists = True
        
        if bExists == False:
            dictRulesByCategory[strCategory] = {}
        
        dictRulesByCategory[strCategory][strRuleTitle] = strRuleTitle
        # =====================================================================

        # =====================================================================
        # Products
        bExists = False
        if strProduct in dictRulesByProduct:
            bExists = True
        
        if bExists == False:
            dictRulesByProduct[strProduct] = {}
        
        dictRulesByProduct[strProduct][strRuleTitle] = strRuleTitle
        # =====================================================================

        # =====================================================================
        # Services
        bExists = False
        if strService in dictRulesByService:
            bExists = True
        
        if bExists == False:
            dictRulesByService[strService] = {}
        
        dictRulesByService[strService][strRuleTitle] = strRuleTitle
        # =====================================================================
    
    createDirIfNotExists("export/")

    # ===================================================================================
    # Categories
    iCount = 1
    createDirIfNotExists("export/categories/")
    # write per category
    for ruleCategory in sorted(dictRulesByCategory):
        strThingForFileName = ruleCategory
        if strThingForFileName == "No Category":
            strThingForFileName = "_" + strThingForFileName
        strFileName = strThingForFileName
        f = open("categories/" + strFileName + ".md", "a")

        writeToFile(f, "## " + ruleCategory)
        for rule in sorted(dictRulesByCategory[ruleCategory]):
            writeToFile(f, dictRules[rule])
        
        iCount = iCount + 1
        f.close()
    # ===================================================================================
    
    # ===================================================================================
    # Products
    iCount = 1
    createDirIfNotExists("export/products/")
    # write per category
    for ruleProduct in sorted(dictRulesByProduct):
        strThingForFileName = ruleProduct
        if strThingForFileName == "No Product":
            strThingForFileName = "_" + strThingForFileName
        strFileName = strThingForFileName
        f = open("products/" + strFileName + ".md", "a")

        writeToFile(f, "## " + ruleProduct)
        for rule in sorted(dictRulesByProduct[ruleProduct]):
            writeToFile(f, dictRules[rule])
        
        iCount = iCount + 1
        f.close()
    # ===================================================================================

    # ===================================================================================
    # Services
    iCount = 1
    createDirIfNotExists("export/services/")
    # write per category
    for ruleService in sorted(dictRulesByService):
        strThingForFileName = ruleService
        if strThingForFileName == "No Service":
            strThingForFileName = "_" + strThingForFileName
        strFileName = strThingForFileName
        f = open("services/" + strFileName + ".md", "a")

        writeToFile(f, "## " + ruleService)
        for rule in sorted(dictRulesByService[ruleService]):
            writeToFile(f, dictRules[rule])
        
        iCount = iCount + 1
        f.close()
    # ===================================================================================

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

def devCategorizeRules():
    print()
    # 1. Generate a lookup of Rule name translated to
    #   - directory path
    #   - original filename
    # 2. Use this to cross reference for categorization
    # 
    # Alternatively
    # use...
    # logsource:
    #   category: application
    #   product: django
    # 

def writeToFile(handle, text):
    handle.write(text + "\n")

def deleteExistingMarkDownFiles():
    if configFromArg['delete']:
        print(alertText + "DELETING existing .md markdown files." + defText)
        # oFiles = glob.glob("*.md")
        oFiles = glob.glob("." + "/**/*.md", recursive=True)

        lFilesToIgnoreDeleteion = ["./readme.md"]

        import os

        for file in oFiles:
            sFileLower = file.lower()
            if sFileLower in lFilesToIgnoreDeleteion:
                print("Skipping deletion: " + successText + file + defText)
            else:
                print(alertText + "Deleting: " + errorText + file + defText)
                os.remove(file)

def createDirIfNotExists(strArgDir):
    import os

    if exists(strArgDir):
        print(successText + "dir " +defText + strArgDir + successText + " exists" + defText)
    else:
        print(alertText + "Creating missing directory: " + defText + strArgDir)
        os.mkdir(strArgDir)

dictCounts = {}
dictCounts["category"]  = {}
dictCounts["product"]   = {}
dictCounts["service"]   = {}

if configFromArg['function'] == "markdown":
    deleteExistingMarkDownFiles()

    rules = doExportRuleQueries()
    # json_object = json.dumps(rules, indent = 4)
    # print(json_object)
    generateMarkDown(rules)

    print("")
    print("Categories: " + str(len(dictCounts["category"])))
    print("Products: " + str(len(dictCounts["product"])))
    print("Services: " + str(len(dictCounts["service"])))
    
    for type in dictCounts:
        print

elif configFromArg['function'] == "ids":
    rules = doExportRuleQueries()
    generateRuleIds(rules)
elif configFromArg['function'] == "dev_dir_list":
    devCategorizeRules()
    # f = open("demofile2.txt", "a")
    # writeToFile(f, "testing 123")
    # f.close()
    # exit()
elif configFromArg['function'] == "dev_delete":
    deleteExistingMarkDownFiles()
else:
    print(errorText + "ERROR! Invalid function." + defText)
