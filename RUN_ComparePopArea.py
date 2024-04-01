#!/home/phisan/miniconda3/envs/gee/bin/python

import os

PROVS = 'Phuket|Ranong|Phangnga|Krabi|Trang|Satun'

for prov in PROVS.split("|"):
    CMD = f'python3 s2_CutRegion.py -c {prov}'
    #print( CMD )
    os.system( CMD )

