#!/usr/bin/env python3
# import json
# import sys
# import argparse

# parser = argparse.ArgumentParser(description="Just an example",
#                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter)
# parser.add_argument("--debug", "-d", help="For debugging", action=argparse.BooleanOptionalAction)
# parser.add_argument("--title", required=True)
# parser.add_argument("--timestamp")
# parser.add_argument("--message", required=True)

# args = parser.parse_args()

# import http.client, urllib
# conn = http.client.HTTPSConnection("api.pushover.net:443")
# conn.request("POST", "/1/messages.json",
#   urllib.parse.urlencode({
#     "token": "ajhcwhgmrcackbw34qvxpotrgg4pzj",
#     "user": "u111ruz6wc6f3av7e8qvyvybciagtp",
#     "message": str(args.message),
#     "title": str(args.title)
#   }), { "Content-type": "application/x-www-form-urlencoded" })
# conn.getresponse()

import json
import sys

# Function that prints text to standard error
def print_stderr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# Main function
if __name__ == "__main__":

    # Print out all input arguments.
    # sys.stdout.write("All Arguments Passed In: " + ' '.join(sys.argv[1:]) + "\n")

    # Turn stdin.readlines() array into a string
    std_in_string = ''.join(sys.stdin.readlines())

    # Load JSON
    event_data = json.loads(std_in_string)

    # Extract some values from the JSON.
    # sys.stdout.write("Values from JSON: \n")
    # sys.stdout.write("Event Definition ID: " + event_data["event_definition_id"] + "\n")
    # sys.stdout.write("Event Definition Title: " + event_data["event_definition_title"] + "\n")
    # sys.stdout.write("Event Timestamp: " + event_data["event"]["timestamp"] + "\n")

    # Extract Message Backlog field from JSON.
    msg_backlog = ""
    sys.stdout.write("\nBacklog:\n")
    for message in event_data["backlog"]:
        msg_backlog = msg_backlog + "\n"
        for field in message.keys():
            # sys.stdout.write("Field: " + field + "\t")
            # sys.stdout.write("Value: " + str(message[field]) + "\n")
            msg_backlog = msg_backlog + str(field) + ": " + str(message[field]) + "\n"

    # Write to stderr if desired
    # print_stderr("Test return through standard error")

    import http.client, urllib
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
    urllib.parse.urlencode({
        "token": "",
        "user": "",
        "message": event_data["backlog"],
        "title": str(event_data["event_definition_title"])
    }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()

    # Return an exit value. Zero is success, non-zero indicates failure.
    exit(0)
