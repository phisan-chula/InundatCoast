#!/home/phisan/miniconda3/envs/gee/bin/python3
#
#
#
import sys,os
import argparse
import pyogrio
import pandas as pd
import geopandas as gpd

gpd.options.io_engine = "pyogrio"
from shapely import Point, MultiPoint
from shapely import wkt
from pathlib import Path
from RiskAnalysis import *

DEM = '/mnt/d/GeoData/FABDEM_TH/FABDEM_Thailand.vrt'  # nodata -9999
COAST_LINE = r'./DATA/Coast_line_andaman.kml'
 
def MakeContour( BUFF=4_0000, CI=10 ):
    gdf_coast = gpd.read_file( COAST_LINE , layer='Andaman_line_merge', engine='pyogrio' )
    gdf_coast = gdf_coast.buffer( BUFF/111_000 )
    BUF_GPKG =  './CACHE/BUFFER_coast.gpkg'
    print( f'Writing {BUF_GPKG} ...' )
    gdf_coast.to_file( BUF_GPKG, driver='GPKG' )
    coast_dem = f'./CACHE/DEM_coast.tiff'
    contour  = Path(DEM).parent / f'{Path(DEM).stem}_contour.gpkg'
    CMD1  = f'''gdalwarp -overwrite -cutline {BUF_GPKG} -cl BUFFER_coast '''\
            f'''-multi -crop_to_cutline -co COMPRESS=DEFLATE -ot Float32  '''\
            f''' -srcnodata -9999 -dstnodata -32768 {DEM} {coast_dem}'''
    print( CMD1 )
    os.system( CMD1 )

    CONTR = './CACHE/CONTR_coast.gpkg' 
    CMD2 = f'gdal_contour  -a MSL  -b 1  -f GPKG   -fl 0.1 5 10   {coast_dem}  {CONTR}'
    print( CMD2 )
    #import pdb ; pdb.set_trace()
    os.system( CMD2 )
    pass

##################################################################
if __name__=="__main__":
    print( f'*** DEM : {DEM} ***')
    parser = argparse.ArgumentParser( prog=sys.argv[0],
                    description='read DEM and generate coastal contour' )
    args = parser.parse_args()
    print( args )
    MakeContour( )

    print( f'************* end of {sys.argv[0]} ******************')
