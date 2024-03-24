#!/home/phisan/miniconda3/envs/gee/bin/python3
#
#
#
import sys,os
import argparse
from RiskAnalysis import *

##################################################################
if __name__=="__main__":
    parser = argparse.ArgumentParser( prog=sys.argv[0],
                    description='What the program does' )
    parser.add_argument( 'PROV', help='specified province name' )
    args = parser.parse_args()

    risk = RiskAnalysis( args.PROV )
    print( risk.TOML)
    VFILE = risk.getVFILE() 

    print( f'**************** Processing {args.PROV} ****************')
    gdf = risk.dfProv[ risk.dfProv.NAME_1==args.PROV ]
    gdf.to_file( VFILE[0] , layer='Region', driver='GPKG')

    CMD = f'gdalwarp -overwrite -cutline {VFILE[0]} -cl Region '\
            f' -co COMPRESS=DEFLATE -ot Float32 -srcnodata -99999 -dstnodata -32768 '\
            f' DATA/tha_ppp_2020.tif {VFILE[1]}'
    print( CMD ) ; os.system( CMD )

    CMD = f'gdalwarp -overwrite -cutline {VFILE[0]} -cl Region '\
            f' -co COMPRESS=DEFLATE -ot Int16 -srcnodata -32768 -dstnodata -32768 '\
            f' DEM/AllDEM.vrt {VFILE[2]}'
    print( CMD ) ; os.system( CMD )

    CMD = f'''find CACHE/{args.PROV} -maxdepth 1  -exec ls -ld {{}} \\; '''
    print( CMD ) ; os.system( CMD )

    print( f'************* end of {sys.argv[0]} ******************')

    #import pdb ; pdb.set_trace()
