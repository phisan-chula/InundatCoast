#!/home/phisan/miniconda3/envs/gee/bin/python
import os
PROVS = 'Phuket|Ranong|Phangnga|Krabi|Trang|Satun'
for prov in PROVS.split("|"):
    for prog in ['s5_Summary.py',]:
        if prog=='s2_CutRegion.py':
            CMD = f'python3 {prog} -p {prov}'
        else:
            CMD = f'python3 {prog} {prov}'
        print( 100*'=')
        print( CMD )
        print( 100*'=')
        os.system( CMD )

