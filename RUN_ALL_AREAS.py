#!/home/phisan/miniconda3/envs/gee/bin/python

import os

PROVS = 'Phuket|Ranong|Phangnga|Krabi|Trang|Satun'

for prov in PROVS.split("|"):
    for prog in ['s2_CutRegion.py','s3_Analysis.py','s4_MakeCluster.py']:

        CMD = f'python3 {prog} {prov}'
        print( 100*'=')
        print( CMD )
        print( 100*'=')
        os.system( CMD )

