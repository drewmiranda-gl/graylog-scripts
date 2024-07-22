import argparse, yaml, requests,urllib3, json, re, shutil, os
from os.path import exists
from requests.auth import HTTPBasicAuth
from tqdm import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

parser = argparse.ArgumentParser()
parser.add_argument("--overwrite", help="Overwrite file if already downloaded.", action=argparse.BooleanOptionalAction, default=False)

args = parser.parse_args()

# font
#                       Style
#                       v Color
#                       v v  Background
#                       v v  v
defText         = "\033[0;30;50m"       # Black
boldText        = "\033[1;30;50m"       # Black
alertText       = "\033[1;33;50m"       # yellow
errorText       = "\033[1;31;50m"       # red
successText     = "\033[1;32;50m"       # green
blueText        = "\033[0;34;50m"       # blue

# =============================================================================
# START DEFINE FUNCTIONS ======================================================

def get_download_url_from_downloads_graylog_org(build_artifact: str):
    url = "https://downloads.graylog.org/nightly-builds?limit=1&artifacts=" + build_artifact
    response = requests.get(url)

    if not response:
        print("ERROR, no 'response'")
        exit(1)
    
    if not int(response.status_code) == 200:
        print("ERROR, HTTP Status: " + str(response.status_code))
        exit(1)
    
    json_obj = json.loads(response.text)

    if not "artifacts" in json_obj:
        print("ERROR, artifacts not found in json response")
        exit(1)
    
    if not len(json_obj['artifacts']):
        print("ERROR, 0 not found in json_obj['artifacts']")
        exit(1)

    return json_obj['artifacts'][0]

def do_download_build_from_downloads_graylog_org(build_artifact: str, overwrite: bool):
    json_artifact = get_download_url_from_downloads_graylog_org(build_artifact)
    url_to_download = json_artifact['url']
    local_filename = json_artifact['filename']
    print("Attempting to download build " + blueText + url_to_download + defText)
    
    if overwrite == False:
        if exists(local_filename):
            print(alertText + "NOTE: Use --overwrite to force skipped file to be downloaded." + defText)
            print(successText + "Skipping file because already downloaded: " + blueText + local_filename + defText)
            return local_filename

    url = url_to_download
    # Streaming, so we can iterate over the response.
    response = requests.get(url, stream=True)
    total_size_in_bytes= int(response.headers.get('content-length', 0))
    block_size = 1024 #1 Kibibyte
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
    with open(local_filename, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("ERROR, something went wrong")
    
    print(successText + "Downloaded file successfully: " + blueText + local_filename + defText)
    return local_filename

def delete_file_if_exists(filename):
    if exists(filename):
        os.remove(filename)

def writeToFile(filename, text):
    handle = open(filename, "a")
    handle.write(text + "\n")
    handle.close()

# END DEFINE FUNCTIONS ========================================================
# =============================================================================

# Downloading Build
delete_file_if_exists("filename.txt")
download_file_name = do_download_build_from_downloads_graylog_org("graylog-enterprise-linux-x64", args.overwrite)
writeToFile("filename.txt", download_file_name)
