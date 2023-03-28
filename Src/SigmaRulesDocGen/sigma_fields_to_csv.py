import argparse
import json
import re
import glob
import requests
from requests.auth import HTTPBasicAuth
import configparser
from os.path import exists
import yaml
import csv

parser = argparse.ArgumentParser(description="Script Arguments...",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--debug", "-d", help="For debugging", action=argparse.BooleanOptionalAction)
parser.add_argument("--dir", help="Directory of sigma rules", default="rules")
parser.add_argument("--csv", help="Illuminate core sigma field map csv file.", default="core_sigma_field_map.csv")
parser.add_argument("--verbose", help="Verbose output.", action=argparse.BooleanOptionalAction, default=False)

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

listSigmaRulesToImport = []

def getGlIllmSigmaMappedFields():
    sCsvFile = configFromArg["csv"]
    dictPosToFiled = {}
    dictFieldToPos = {}

    dictFieldsBySigmaField = {}
    dictFieldsByGimFIeld = {}
    listSigmaFields = []
    listSigmaFieldsLower = []

    if exists(sCsvFile):
        if configFromArg['verbose']:
            print(successText + "Illuminate CSV Mapping file: " + defText + sCsvFile + successText + " exists." + defText)
        
        with open(sCsvFile, newline='') as csvfile:
            illuminateFields = csv.reader(csvfile, delimiter=',', quotechar='"')
            i = 0
            for row in illuminateFields:
                sSigmaField = ""
                sGimField = ""

                if i == 0:
                    iFieldPos = 0
                    for col in row:
                        # print(str(iFieldPos) + ": " + col)
                        dictPosToFiled[iFieldPos] = col
                        dictFieldToPos[col] = iFieldPos
                        iFieldPos += 1

                if i > 0:
                    sSigmaField = row[dictFieldToPos['sigma_field_name']]
                    sGimField = row[dictFieldToPos['GIM_field_name']]

                    dictFieldsBySigmaField[sSigmaField] = sGimField
                    dictFieldsByGimFIeld[sGimField] = sSigmaField
                    listSigmaFields.append(sSigmaField)
                    listSigmaFieldsLower.append(sSigmaField.lower())

                i += 1
        
        return listSigmaFieldsLower
    else:
        print(errorText + "ERROR! " + "Illuminate CSV Mapping file: " + defText + sCsvFile + errorText + " does not exist!")
        return []

def doBuildSigmaImportList(argFile):
    listSigmaRulesToImport.append(argFile)

def fieldOnlyRemovePipeAndWhatFollows(field):
    dictReturn = {}

    try:
        pos = field.find("|")
    except:
        pos = 0

    if pos > 0:
        dictReturn['field'] = field[0:pos]
        dictReturn['haspipe'] = True
        return dictReturn
    else:
        dictReturn['field'] = field
        dictReturn['haspipe'] = False
        return dictReturn

def doFieldsToCsv(argList):
    iRuleCount = len(argList)

    dict_rule_2d_fields = []

    for i in argList:
        fileName = i
        if configFromArg['verbose']:
            print(successText + i + defText)
        raw = open(fileName).read()
        dct = yaml.safe_load(raw)

        strTitle = ""
        strCategory = ""
        strProduct = ""
        
        iTags = 0
        strTags = ""
        
        strStatus = ""
        strAuthor = ""
        strDate = ""
        strModified = ""

        if 'title' in dct:
            strTitle = dct['title']
        
        if 'logsource' in dct:
            if 'category' in dct['logsource']:
                strCategory = dct['logsource']['category']
            if 'product' in dct['logsource']:
                strProduct = dct['logsource']['product']
        
        if 'tags' in dct:
            for tags in dct['tags']:
                if iTags > 1:
                    strTags = strTags + "; "
                strTags = strTags + tags
                iTags = iTags + 1
        
        if 'status' in dct:
            strStatus = dct['status']
        
        if 'author' in dct:
            strAuthor = dct['author']
        
        if 'date' in dct:
            strDate = str(dct['date'])
        
        if 'modified' in dct:
            strModified = str(dct['modified'])

        dict_rule_2d_fields.append({
            "file": fileName,
            "title": strTitle,
            "category": strCategory,
            "product": strProduct,
            "tags": str(strTags),
            "status": strStatus,
            "author": strAuthor,
            "date": strDate,
            "modified": strModified
        })
        
    return dict_rule_2d_fields

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

print("Counting field names for all sigma rules... (This may take a minute)")

finalCsv = doFieldsToCsv(listSigmaRulesToImport)

field_names= ['file', 'title', 'category', 'product', 'tags', 'status', 'author', 'date', 'modified']

with open('sigma_fields.csv', 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=field_names)
    writer.writeheader()
    writer.writerows(finalCsv)

# json_object = json.dumps(finalCsv, indent = 4)
# print(json_object)
