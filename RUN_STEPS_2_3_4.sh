#!/bin/sh
# Check if there are arguments using $# (number of arguments)
if [ $# -eq 0 ]; then
  echo "No arguments provided."
  echo "RUN_STEPS_2_3_4 {Phuket|Ranong|Phangnga|Krabi|Trang|Satun}"
else
  python3 s2_CutRegion.py $1
  python3 s3_Analysis.py $1
  python3 s4_MakeCluster.py $1
fi

