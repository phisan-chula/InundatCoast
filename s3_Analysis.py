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

def GeoTIFF2df( GeoTIFF, IN_RANGE, NAME='VALUE' ):
    da = rioxarray.open_rasterio( GeoTIFF )
    ds = da.to_dataset(name=NAME)
    df = ds.to_dataframe().reset_index()
    df = df[ (df[NAME]>=IN_RANGE[0]) & (df[NAME]<=IN_RANGE[1]) ]
    gdf = gpd.GeoDataFrame( df, crs='EPSG:4326', 
          geometry=gpd.points_from_xy( df.x, df.y)) 
    return gdf

##################################################################
if __name__=="__main__":
    parser = argparse.ArgumentParser( prog=sys.argv[0],
                    description='What the program does' )
    parser.add_argument( 'PROV', help='specified province name' )
    args = parser.parse_args()

    risk = RiskAnalysis( args.PROV )
    print( risk.TOML )
    VULNER = risk.getVFILE() ; AB=risk.getAbbrev()
    print( f'Processing {VULNER}...' )
    #import pdb ;pdb.set_trace()
    [MSL_minmax, Popu_minmax] = risk.getDEFAULT('MINMAX')
    gdfRegion = gpd.read_file( VULNER[0] )

    print(f'Writing Analysis (Points) file "{VULNER[3]}" ...')

    gdfDEM = GeoTIFF2df( VULNER[2], IN_RANGE=MSL_minmax , NAME="MSL")
    print( gdfDEM.MSL.describe() )
    gdfDEM.to_file( VULNER[3], layer=f'{AB}:DEM', driver='GPKG' )

    gdfPopu = GeoTIFF2df( VULNER[1],IN_RANGE=Popu_minmax , NAME="Popu" )
    gdfPopu.Popu = gdfPopu.Popu.round(1)
    print( gdfPopu.Popu.describe() )
    gdfPopu.to_file( VULNER[3] , layer=f'{AB}:Popu', driver='GPKG' )

    CMD = f'''find CACHE/{args.PROV} -maxdepth 1  -exec ls -ld {{}} \\; ''' 
    print(CMD); os.system( CMD )

