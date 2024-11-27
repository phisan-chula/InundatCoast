#
#
#
import pandas as pd 
import geopandas as gpd 
from shapely.geometry import Point
import pyogrio
import re

####################################################################
def ReadRadioTower():
    RADIO  = '/mnt/d/FieldData/NOSTRA_RadioTower/LANDMARK.gdb'
    gdf = gpd.read_file( RADIO, layer='LANDMARK_75200' )
    gdf = gdf.to_crs('EPSG:4326')
    return gdf 

def ReadWarningTower():
    df = pd.read_csv( 'DDPM_WarningTower.txt', header=None)
    def Parse(row):
        cols = row[0].split()
        code = cols[1]
        place = " ".join( cols[2:-5] ) 
        tb = cols[-5]
        ap = cols[-4]
        cw = cols[-3]
        N = float(cols[-2][1:])
        E = float(cols[-1][1:])
        return  code, place, tb, ap, cw, Point( E,N)
    df[[ 'code','place','tambol','amphoe','changwat','geometry']] = df.apply( Parse, axis=1, result_type='expand')
    df.drop( columns=0, inplace=True )
    print( df.code.value_counts() )
    print( df.changwat.value_counts() )
    gdf = gpd.GeoDataFrame( df , crs='EPSG:4326' , geometry=df.geometry )
    return gdf

###############################################################
###############################################################
###############################################################
gdfWarn =  ReadWarningTower()
if 0:
    ANDA = [ 'ระนอง', 'พังงา', 'ภูเก็ต', 'กระบี่','ตรัง' , 'สตูล' ]
    gdfWarn = gdfWarn[ gdfWarn.changwat.isin( ANDA ) ]
###############################################################
TOWER = '../CACHE/WarnRadio_Tower.gpkg'

print( len(gdfWarn) )
print( gdfWarn.changwat.value_counts() )

print( f'Writing {TOWER} ...' )
gdfWarn.to_file( TOWER, driver='GPKG', layer='WarnDDPM', engine='pyogrio' )

gdfRadio = ReadRadioTower()
gdfRadio.to_file( TOWER, driver='GPKG', layer='RadioTower', engine='pyogrio' )
import pdb; pdb.set_trace()


