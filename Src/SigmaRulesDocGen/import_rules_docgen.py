import argparse
import json
import re
import glob
import yaml

# pip install pyyaml

parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--debug", "-d", help="For debugging", action=argparse.BooleanOptionalAction)
parser.add_argument("--import-dir", help="Directory of sigma rules", default="rules")
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
#   Blue        44
#   Purple      45
#   Cyan        46
#   White       47

def doParseYaml(argFile):
    with open(argFile, 'r') as file:
        objYamlAsJson = yaml.safe_load(file)
        # print(objYamlAsJson)
        print(objYamlAsJson["title"])

print("Loading from directory \"" + successText + configFromArg["import_dir"] + defText + "\"" + "\n")

oFiles = glob.glob(configFromArg["import_dir"] + "/**/*.yml", recursive=True)
for file in oFiles:
    print(file)
    doParseYaml(file)