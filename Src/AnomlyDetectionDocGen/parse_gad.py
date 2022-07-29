import argparse
import json
import re

parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--debug", "-d", help="For debugging", action=argparse.BooleanOptionalAction)
parser.add_argument("--file", help="Graylog Anomaly Detection rules json file", required=True)

args = parser.parse_args()
configFromArg = vars(args)

# print("Arguments: ")
# print(configFromArg)
# print("")


f = open (configFromArg['file'], "r")
oJson = json.loads(f.read())
oJsEnt = oJson['entities']

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
    print("## " + anomRuleTitle)
    print("")

    # Requirements
    sConstraints = dictAnomDetRules[anomRuleTitle]['constraints']
    print("### Requirements: ")
    for sConstraint in sConstraints:
        print(sConstraint['type'] + ": " + sConstraint['version'])
    print("")
    
    # Description
    sDesc = dictAnomDetRules[anomRuleTitle]['data']['description']['@value']
    # result = re.search(r"^(.*?)(?:\n|<br>)", sDesc)
    # print("Description: " + result.group(1))
    print(sDesc)
    print("")

    print("Config | Value")
    print("---- | ----")

    # Indices
    sIndices = dictAnomDetRules[anomRuleTitle]['data']['indices']
    # print("#### Index Prefix(es): ")
    sConcat = ""
    for sIndexPrefix in sIndices:
        # print(sIndexPrefix['@value'])
        sConcat = sConcat + "- " + sIndexPrefix['@value'] + "<br>"
    print("Index Prefix(es) | " + sConcat)

    # Feature Fields
    # print("#### Feature Fields: ")
    # print("")
    sFeatures = dictAnomDetRules[anomRuleTitle]['data']['feature_fields']
    sConcat = ""
    for sFeature in sFeatures:
        sConcat = sConcat + "feature_name: " + sFeature['feature_name']['@value'] + "<br>"
        sConcat = sConcat + "    - field_name: " + sFeature['field_name']['@value'] + "<br>"
        sConcat = sConcat + "    - operation: " + sFeature['operation']['@value'] + "<br>"
    print("Feature Fields | " + sConcat)
    
    # categorical_fields
    # print("### Categorical Fields: ")
    # print("")
    sCatFields = dictAnomDetRules[anomRuleTitle]['data']['categorical_fields']
    sConcat = ""
    for sCatField in sCatFields:
        sConcat = sConcat + "- " + sCatField['@value'] + "<br>"
    print("Categorical Fields | " + sConcat)

    
    print("shingle_size | " + str(dictAnomDetRules[anomRuleTitle]['data']['shingle_size']['@value']))
    print("detector_interval_minutes | " + str(dictAnomDetRules[anomRuleTitle]['data']['detector_interval_minutes']['@value']))
    print("window_delay_minutes| " + str(dictAnomDetRules[anomRuleTitle]['data']['window_delay_minutes']['@value']))
