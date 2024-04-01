#
#
#
from pathlib import Path
import pandas as pd
import geopandas as gpd
# #   Column          Dtype
#---  ------          -----
# 0   latitude        float64
# 1   longitude       float64
# 2   area_in_meters  float64
# 3   confidence      float64
# 4   geometry        object
# 5   full_plus_code  object

class GoogleGlobBldg:
    def __init__(self, FILE_BLDG , FILE_POLY, NROWS=None ):
        ''' NROWS = -n : skip every n-th row
            NOOWS == 0 : read all rows
            NROWS = +n : read only first n rows'''
        self.FILE_BLDG = FILE_BLDG
        self.FILE_POLY = FILE_POLY
        CACHE_FILE = self.replace_extension( self.FILE_BLDG, '.bz2' )
        if CACHE_FILE.is_file():
            print(f'Reading cached {CACHE_FILE} ...')
            gdf = pd.read_pickle( CACHE_FILE ,  compression='infer' )
        else:
            print(f'Reading new {FILE_BLDG} and writing {CACHE_FILE} ...')
            gdf = self.ReadGlobBldg( NROWS=NROWS )
            gdf.to_pickle( CACHE_FILE, compression='infer' )
        self.gdf = gdf
        #import pdb; pdb.set_trace()
        ##########################################################
        poly = gpd.read_file( self.FILE_POLY ).simplify( 500/111_000 )
        gdf_ = gdf.overlay(  gpd.GeoDataFrame(geometry=poly),  
                    how='intersection', keep_geom_type='Point' )
        self.gdf_ = gdf_

    def ReadGlobBldg( self, NROWS=10_000 ):
        USECOLS=[ 0,1,2,3 ] # point format
        if NROWS > 0:
            df = pd.read_csv( self.FILE_BLDG, usecols=USECOLS, nrows=NROWS )
        elif NROWS==0:
            df = pd.read_csv( self.FILE_BLDG, usecols=USECOLS )
        else:   # minus '-' means  read ever n-th
            SKIPS = lambda x: x % -NROWS != 0
            df = pd.read_csv( self.FILE_BLDG, usecols=USECOLS, skiprows=SKIPS )
        gdf = gpd.GeoDataFrame( df, crs='EPSG:4326', 
                        geometry=gpd.points_from_xy( df.longitude, df.latitude ) )
        return gdf

    def replace_extension(self, path, new_ext):
        parent = Path( path ).parent
        stem = Path( path ).stem
        return parent.joinpath(stem + new_ext)


###########################################################################
if __name__ == '__main__':
    GG_BLDG =  'DATA/305_buildings.csv'
    Region = 'CACHE/Trang/VulnerRegion.gpkg'
    gb = GoogleGlobBldg( GG_BLDG, Region, NROWS=0 )
    print( f'gdf  : {len(gb.gdf):,d}' )
    print( f'gdf_ : {len(gb.gdf_):,d}' )
    #import pdb; pdb.set_trace()

