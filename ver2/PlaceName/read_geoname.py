#
#
#
import pandas as pd
import geopandas as gpd
import pyogrio
from shapely.geometry import Point

###########################################################################
PROV = 'Phuket|Ranong|Phangnga|Krabi|Trang|Satun'
dfGADM = gpd.read_file( '../DATA/gadm41_THA.gpkg', layer='ADM_ADM_1')
dfPROV = dfGADM[ dfGADM.NAME_1.isin( PROV.split('|') ) ]

GEONAMES = r'../DATA/TH/TH.txt'
column_names = ['geonameid', 'name', 'asciiname', 'alternatenames', 'latitude', 'longitude', 
        'country_code', 'feature_class', 'feature_code', 'cc2', 'admin1_code', 'admin2_code', 
        'admin3_code', 'admin4_code', 'population', 'elevation', 'dem', 'timezone', 'modification_date']
dfPlace = pd.read_csv( GEONAMES, sep='\t', header=None,names=column_names )
gdfPlace = gpd.GeoDataFrame( dfPlace, crs='OGC:CRS84', geometry=gpd.points_from_xy( 
                        dfPlace.longitude,dfPlace.latitude ) )

df = gpd.sjoin( gdfPlace, dfPROV, how='inner', op='within' )
df.to_file('Places6Prov.gpkg', driver='GPKG', layer='Places' )
import pdb ; pdb.set_trace()
