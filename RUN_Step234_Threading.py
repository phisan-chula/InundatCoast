#!/home/phisan/miniconda3/envs/gee/bin/python
import os,sys
import subprocess
import argparse
from pathlib import Path

def capture_and_log_output(command, log_file="log.txt"):
  """
  Executes a command using subprocess and redirects its output to a log file.
  Args:
      command: The command to execute as a string or list of strings.
      log_file: The path to the log file (default: "log.txt").
  """
  with open(log_file, "a") as log:
    try:
      # Capture the output using check_output
      output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)  # Combine stdout and stderr
      log.write(output.decode())  # Write decoded output to log file
    except subprocess.CalledProcessError as e:
      log.write(f"Error executing command: {e}\n")

###############################################################################
PROVS = 'Phuket|Ranong|Phangnga|Krabi|Trang|Satun'

parser = argparse.ArgumentParser( prog=sys.argv[0],
                description='What the program does' )
parser.add_argument( 'PROV', help=f'specified province {PROVS}' )
args = parser.parse_args()

Path(f'./CACHE').mkdir(parents=True, exist_ok=True)
CMD = ""
for prog in ['s2_CutRegion.py','s3_Analysis.py','s4_MakeCluster.py']:
    CMD = f'{CMD} python3 {prog} {args.PROV} ; '
#import pdb; pdb.set_trace()
print( CMD, '...threading...' )
capture_and_log_output( CMD , log_file=f"CACHE/log_s234_{sys.argv[1]}.txt")
