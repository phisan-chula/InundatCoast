#!/bin/sh

set -x

find CACHE/ -name "*.gpkg" -type f -print | zip -@ /mnt/c/Users/User/Downloads/Prelim_Analysis.zip
