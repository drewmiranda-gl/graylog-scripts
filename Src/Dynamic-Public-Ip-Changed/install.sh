#! /bin/bash

sudo mkdir -p /opt/track_public_ip_changes

# */1 * * * * /usr/bin/sh /opt/track_public_ip_changes/track_public_ip_changes.sh >> /opt/track_public_ip_changes/debug.log