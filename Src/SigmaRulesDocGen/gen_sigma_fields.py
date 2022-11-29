import argparse
import json
import re
import glob
import requests
from requests.auth import HTTPBasicAuth
import configparser
from os.path import exists
import yaml

parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--debug", "-d", help="For debugging", action=argparse.BooleanOptionalAction)
parser.add_argument("--dir", help="Directory of sigma rules", default="rules")
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

def doBuildSigmaImportList(argFile):
    listSigmaRulesToImport.append(argFile)

def fieldOnlyRemovePipeAndWhatFollows(field):
    try:
        pos = field.find("|")
    except:
        pos = 0

    if pos > 0:
        return field[0:pos]
    else:
        return field

def doCountFields(argList):
    lIgnore = ["condition", "keyword", "selection_keywords", "export_command", "export_params", "keywords"]
    dictFields = {}
    dictFieldsPerRule = {}

    for i in argList:
        fileName = i
        if configFromArg['verbose']:
            print(successText + i + defText)
        raw = open(fileName).read()
        dct = yaml.safe_load(raw)
        detections = dct["detection"]
        for selection in detections:
            if not selection in lIgnore:
                for field in detections[selection]:
                    if type(field) is str:
                        sTrimmedField = fieldOnlyRemovePipeAndWhatFollows(field)
                        
                        if not sTrimmedField in dictFields:
                            dictFields[sTrimmedField] = 0
                        
                        dictFields[sTrimmedField] = dictFields[sTrimmedField] + 1
                        
                        if not sTrimmedField in dictFieldsPerRule:
                            dictFieldsPerRule[sTrimmedField] = {}
                        if not fileName in dictFieldsPerRule[sTrimmedField]:
                            dictFieldsPerRule[sTrimmedField][fileName] = ""

                        dictFieldsPerRule[sTrimmedField][fileName] = ""

                    elif type(field) is dict:
                        for subfield in field:
                            sTrimmedField = fieldOnlyRemovePipeAndWhatFollows(subfield)
                            
                            if not sTrimmedField in dictFields:
                                dictFields[sTrimmedField] = 0
                            
                            dictFields[sTrimmedField] = dictFields[sTrimmedField] + 1

                            if not sTrimmedField in dictFieldsPerRule:
                                dictFieldsPerRule[sTrimmedField] = {}
                            if not fileName in dictFieldsPerRule[sTrimmedField]:
                                dictFieldsPerRule[sTrimmedField][fileName] = ""

                            dictFieldsPerRule[sTrimmedField][fileName] = ""

    
    # print(json.dumps(dictFields))
    
    for field in dictFieldsPerRule:
        print(str(field) + "\t" + str(len(dictFieldsPerRule[field])))


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

doCountFields(listSigmaRulesToImport)