#!/bin/bash
# Rebuilds the client, so JavaScript changes become visible.
# Version: 2016nov03

cd `dirname $0` # Make sure we're in this folder
cd ../client
bower install
gulp sass