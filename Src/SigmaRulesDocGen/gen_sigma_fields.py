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

def doCountFields(argList):
    iRuleCount = len(argList)

    lIgnore = ["condition", "keyword", "selection_keywords", "export_command", "export_params", "keywords"]
    dictFields = {}
    dictFieldsPerRule = {}
    listRulesWithoutFields = []
    listRulesWithFields = []

    listGimCompatbileFields = []
    listMissingGimFields = []

    listGimFileds = getGlIllmSigmaMappedFields()

    listRulesWithIncompatibleFields = []
    listCompatibleRules = []

    for i in argList:
        fileName = i
        if configFromArg['verbose']:
            print(successText + i + defText)
        raw = open(fileName).read()
        dct = yaml.safe_load(raw)
        detections = dct["detection"]
        bHasSelection = False
        bRuleisCompatible = True

        for selection in detections:
            if not selection in lIgnore:
                bHasSelection = True
                for field in detections[selection]:
                    if type(field) is str:
                        dTrmFld = fieldOnlyRemovePipeAndWhatFollows(field)
                        sTrimmedField = dTrmFld['field']
                        if sTrimmedField.lower() in listGimFileds:
                            if sTrimmedField not in listGimCompatbileFields:
                                listGimCompatbileFields.append(sTrimmedField)
                        else:
                            if sTrimmedField not in listMissingGimFields:
                                listMissingGimFields.append(sTrimmedField)
                                bRuleisCompatible = False
                        
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
                            # sTrimmedField = fieldOnlyRemovePipeAndWhatFollows(subfield)
                            dTrmFld = fieldOnlyRemovePipeAndWhatFollows(subfield)
                            sTrimmedField = dTrmFld['field']
                            if sTrimmedField.lower() in listGimFileds:
                                if sTrimmedField not in listGimCompatbileFields:
                                    listGimCompatbileFields.append(sTrimmedField)
                            else:
                                if sTrimmedField not in listMissingGimFields:
                                    listMissingGimFields.append(sTrimmedField)
                                    bRuleisCompatible = False
                            
                            if not sTrimmedField in dictFields:
                                dictFields[sTrimmedField] = 0
                            
                            dictFields[sTrimmedField] = dictFields[sTrimmedField] + 1

                            if not sTrimmedField in dictFieldsPerRule:
                                dictFieldsPerRule[sTrimmedField] = {}
                            if not fileName in dictFieldsPerRule[sTrimmedField]:
                                dictFieldsPerRule[sTrimmedField][fileName] = ""

                            dictFieldsPerRule[sTrimmedField][fileName] = ""
        
        if bHasSelection == False:
            listRulesWithoutFields.append(fileName)
        else:
            listRulesWithFields.append(fileName)
        
        if bRuleisCompatible == True:
            listCompatibleRules.append(fileName)
        else:
            listRulesWithIncompatibleFields.append(fileName)

    
    # print(json.dumps(dictFields))
    # print(listRulesWithoutFields)
    
    for field in dictFieldsPerRule:
        print(str(field) + "\t" + str(len(dictFieldsPerRule[field])))
    
    iRulesWithoutFieldsInQuery = len(listRulesWithoutFields)
    if iRulesWithoutFieldsInQuery > 0:
        print("")
        print(alertText + "Rules without fields in query: " + errorText + str(iRulesWithoutFieldsInQuery) + defText + " of " + str(iRuleCount) + " (" + str(len(listRulesWithFields)) + " rules do have fields in query.)")
        print(json.dumps(listRulesWithoutFields))
    
    # listGimCompatbileFields = []
    # listMissingGimFields = []
    iCompatibleFields = len(listGimCompatbileFields)
    iIncompatibleFields = len(listMissingGimFields)

    print("")
    print(successText + "GIM Compatible Fields (" + str(iCompatibleFields) + " fields):" + defText)
    print(json.dumps(listGimCompatbileFields))
    
    print("")
    print(errorText + "GIM Incompatible Fields (Missing from illuminate csv lookup mapping) (" + str(iIncompatibleFields) + " fields):" + defText)
    print(json.dumps(listMissingGimFields))

    iIncompatibleRules = len(listRulesWithIncompatibleFields)
    iCompatibleRules = len(listCompatibleRules)
    if iIncompatibleFields > 0:
        print("")
        print(errorText + str(iIncompatibleRules) + " (of " + str(iRuleCount) + ") sigma rules have fields that are not mapped by Graylog Illuminate via core_sigma_field_map.csv" + defText)
        print(alertText + "This means these rules cannot be effectively used with Graylog's Sigma Rules feature." + defText)
        print(successText + str(iCompatibleRules) + " (of " + str(iRuleCount) + ") sigma rules have fields that are mapped." + defText)

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