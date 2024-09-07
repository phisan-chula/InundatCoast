#!/home/phisan/miniconda3/envs/gee/bin/python3
#
#
#
import sys,os
import argparse
import pandas as pd
import geopandas as gpd
import rioxarray
import numpy as np
from shapely.geometry import Point

from RiskAnalysis import *
from GlobBldg import *

##################################################################
if __name__=="__main__":
    parser = argparse.ArgumentParser( prog=sys.argv[0],
                    description='What the program does' )
    parser.add_argument( 'PROV', help='specified province name' )
    args = parser.parse_args()

    risk = RiskAnalysis( args.PROV )
    print( risk.TOML )
    VFILE = risk.getVFILE() ; AB=risk.getAbbrev()
    print( f'====================Processing {sys.argv[0]}===================' )

    ##################################################################
    if 0:
        GG_BLDG =  'DATA/305_buildings.csv'
        gg = GoogleGlobBldg( GG_BLDG, VFILE[0], NROWS=0 )
        #import pdb ;pdb.set_trace()
        gg_bldg = gg.gdf_[gg.gdf_.confidence>0.7]
        gg_bldg.to_file( VFILE[3], layer=f'{AB}:Building', driver='GPKG' )
    ##################################################################

    [MSL_minmax, Popu_minmax] = risk.getDEFAULT('MINMAX')
    gdfRegion = gpd.read_file( VFILE[0] )

    print(f'Writing Analysis (Points) file "{VFILE[3]}" ...')
    try:
        gdfDEM = GeoTIFF2df( VFILE[2], IN_RANGE=MSL_minmax , NAME="MSL")
    except:
        import pdb ; pdb.set_trace()
    print( gdfDEM.MSL.describe() )
    gdfDEM.to_file( VFILE[-1], layer=f'{AB}:DEM', driver='GPKG' )

    gdfPopu = GeoTIFF2df( VFILE[1],IN_RANGE=Popu_minmax , NAME="Popu" )
    gdfPopu.Popu = gdfPopu.Popu.round(1)
    print( gdfPopu.Popu.describe() )
    gdfPopu.to_file( VFILE[-1] , layer=f'{AB}:Popu', driver='GPKG' )

    CMD = f'''find CACHE/{args.PROV} -maxdepth 1  -exec ls -ld {{}} \\; ''' 
    print(CMD); os.system( CMD )

