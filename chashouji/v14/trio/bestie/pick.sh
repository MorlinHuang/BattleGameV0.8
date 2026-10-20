#!/bin/sh
# 用法：sh pick.sh G4 /tmp/kf_generated_images/xxx.png  → ref/G4.png
cp "$2" "$(dirname "$0")/ref/$1.png" && echo "ref/$1.png <- $2"
