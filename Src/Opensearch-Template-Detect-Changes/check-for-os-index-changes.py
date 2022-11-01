# pip install requests
# pip install configparser

import requests
from requests.auth import HTTPBasicAuth
import configparser
import json
import glob
import argparse
import re

# defaults
parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--debug", "-d", help="For debugging", action=argparse.BooleanOptionalAction)
parser.add_argument("--config", help="Config Filename", default="config.ini")

args = parser.parse_args()
configFromArg = vars(args)

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

# build server:host and concat with URI
sArgBuildUri=sArgBuildUri+sArgHost+":"+sArgPort

def uploadContentPack(oJsonFile):
    # specify URL
    sUrl = sArgBuildUri + "/api/system/content_packs"

    # headers
    sHeaders = {"Accept":"application/json", "X-Requested-By":"python-ctpk-upl"}

    # send req, upload json content pack file
    r = requests.post(sUrl, json = oJsonFile, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
    return r

def installContentPack(sContentPackUniqueId, sContentPackRevVer):
    # specify URL
    sUrl = sArgBuildUri + "/api/system/content_packs/" + sContentPackUniqueId + "/" + str(sContentPackRevVer) + "/installations"
    
    # headers
    sHeaders = {"Accept":"application/json", "X-Requested-By":"python-ctpk-upl"}

    # {"parameters":{},"comment":""}


    # send req, upload json content pack file
    oJson = {"parameters":{},"comment":""}
    r = requests.post(sUrl, json = oJson, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))

    # print(r.status_code)
    # print(r.headers)
    # print(r.text)
    return r



def fullUploadInstallContentPack(sArgUploadFile):
    # load json file
    f = open (sArgUploadFile, "r")
    oJsonFile = json.loads(f.read())
    # get ID
    sContentPackUniqueId = oJsonFile['id']
    sContentPackRevVer = oJsonFile['rev']

    print("Installing Content Pack:")
    print("    " + oJsonFile['name'])
    # print("    " + sContentPackUniqueId)

    if configFromArg['debug']:
        print("        debug enabled, skipping upload web req")

    if not configFromArg['debug']:
        r = uploadContentPack(oJsonFile)

        iStatusCode = r.status_code
        if iStatusCode == 201:
            print("    Content Pack Successfully Uploaded")
            print("    Will Install...")
            rInst = installContentPack(sContentPackUniqueId, sContentPackRevVer)
            if rInst.status_code == 200:
                print("        Installed Successfully!")
            else:
                print("        Error: " + str(rInst.status_code) + " (" + rInst.text + ")")
        elif iStatusCode == 401:
            print("")
            print("ERROR! Authentication error. Please verify config file is configured correctly.")
            print("")
            exit()
        elif iStatusCode == 400:
            print("        Already Installed!")
        else:
            print("    Error: " + str(iStatusCode) + " (" + r.text + ")")
    
    print("")

    # print(r.status_code)
    # print(r.headers)
    # print(r.text)

def getLatestIlluminateContentPacks():
    # lIllCtPkIds = []
    dictIlluminateContentPacks = {}

    print("    Getting list of content packs...")

    # specify URL
    sUrl = sArgBuildUri + "/api/system/content_packs/latest"

    # headers
    sHeaders = {"Accept":"application/json", "X-Requested-By":"python-ctpk-upl"}

    r = requests.get(sUrl, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
    if r.status_code == 200:
        intIllCtPk = 0

        # print(r.text)
        oJsonContentPacks = json.loads(r.text)
        # print("        Found " + str(oJsonContentPacks['total']) + " content packs.")

        regex = r"Graylog Illuminate"

        for ctpk in oJsonContentPacks['content_packs']:
            if re.match(regex, ctpk['name']):
                intIllCtPk += 1

        print("        Found " + str(intIllCtPk) + " Illuminate content packs.")

        for ctpk in oJsonContentPacks['content_packs']:
            if re.match(regex, ctpk['name']):
                # print("Illumate Content Pack: " + ctpk['name'])
                # lMetaKeys.append(ctpk['id'])
                dictIlluminateContentPacks[ctpk['id']] = {'rev': ctpk['rev'], 'name': ctpk['name']}

        return dictIlluminateContentPacks


    else:
        print("    ERROR! HTTP Status: " + str(r.status_code))

def doUninstallContentPackRevById(argContentPackId, argContentPackRevId):
    print("            Uninstalling Content Pack: " + argContentPackId + ", rev: " + argContentPackRevId)

    # specify URL
    sUrl = sArgBuildUri + "/api/system/content_packs/" + argContentPackId + "/installations/" + argContentPackRevId

    # headers
    sHeaders = {"Accept":"application/json", "X-Requested-By":"python-ctpk-upl"}

    r = requests.delete(sUrl, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
    print("            HTTP Status:" + str(r.status_code))

def doCompareFindIfOldRevsCanBeUninstalled(argJsonContentPackAllRevs):
    listRevs = []
    listUniques = []
    dictIlluminateContentPackInstallRevs = {}

    # get revs
    for ctPkRev in argJsonContentPackAllRevs:
        realRev = ctPkRev['content_pack_revision']
        listRevs.append(realRev)
        dictIlluminateContentPackInstallRevs[realRev] = ctPkRev
    
    listRevs.sort(reverse=True)

    isRevUnique = True
    
    for revNumber in listRevs:
        # entities
        jsEnt = dictIlluminateContentPackInstallRevs[revNumber]['entities']
        for entity in jsEnt:
            strType = entity['type']['name']
            strTitle = entity['title']
            # print("Type: " + strType + ", Title: " + strTitle)
            strConcatUnique = strType + "___" + strTitle

            # is this unique?
            if strConcatUnique in listUniques:
                # print("            NOT UNIQUE: " + strConcatUnique)
                isRevUnique = False
                break

            listUniques.append(strConcatUnique)
        
        if not isRevUnique:
            print("        Version: " + str(revNumber) + " is not unique")
            strContentPackId = dictIlluminateContentPackInstallRevs[revNumber]['content_pack_id']
            strInstallId = dictIlluminateContentPackInstallRevs[revNumber]['_id']
            # print("strContentPackId: " + strContentPackId)
            # print("strInstallId: " + strInstallId)
            if not configFromArg['debug']:
                doUninstallContentPackRevById(strContentPackId, strInstallId)
            else:
                print("            debug enabled, skipping uninstall content pack version!")
    
    if isRevUnique:
        print("        No duplicate content found.")



def getContentPack(argContentPackId, argContentPackName):
    iFoundRevs = 0

    # print("")
    # print(argContentPackId)

    # specify URL
    sUrl = sArgBuildUri + "/api/system/content_packs/" + argContentPackId + "/installations"

    # headers
    sHeaders = {"Accept":"application/json", "X-Requested-By":"python-ctpk-upl"}

    r = requests.get(sUrl, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
    if r.status_code == 200:
        oJsonContentPack = json.loads(r.text)
        for ctPkRev in oJsonContentPack['installations']:
            iFoundRevs += 1
            # rev = oJsonContentPack['installations'][ctPkRev]['rev']
            rev = ctPkRev['content_pack_revision']
        
        # print("    Found " + str(iFoundRevs) + " revs")
        if iFoundRevs > 1 :
            # more than one, we may have duplicates
            # check if old rev has anything new rev does not
            print("")
            print("    Content pack '" + argContentPackName + "' has " + str(iFoundRevs) + " version")
            print("        Checking for duplicate content...")
            doCompareFindIfOldRevsCanBeUninstalled(oJsonContentPack['installations'])

    else:
        print("    ERROR! HTTP Status: " + str(r.status_code))

def doCheckForDuplicateContentPacks():
    dictContentPacksLatest = getLatestIlluminateContentPacks()
    for key in dictContentPacksLatest:
        jsonContentPack = getContentPack(key, dictContentPacksLatest[key]['name'])

def doCheckForOpensearchTemplateChanges():
    # specify URL
    sUrl = sArgBuildUri + "/_cat/templates?v"

    # headers
    sHeaders = {"Accept":"application/json"}

    r = requests.get(sUrl, headers=sHeaders, verify=False)
    if r.status_code == 200:
        jsonOsTemplates = json.loads(r.text)
        for osTemplate in jsonOsTemplates:
            print("")
            print("====")
            print(osTemplate)
















# getContentPack("78f8f6ed-ce4c-4033-8be8-23bb6e92f058")
# exit()

doCheckForOpensearchTemplateChanges()

exit()