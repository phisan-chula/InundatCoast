#
#
import pandas as pd
import geopandas as gpd
import pyogrio
from shapely.geometry import Point
from geopy.geocoders import Nominatim
#######################################################
xml_file = 'Anat_Tsunami_Aug20.xml'
df = pd.read_xml( xml_file, xpath="//observation-area" )
print( df )

import pdb ; pdb.set_trace()

geolocator = Nominatim(user_agent="geoapiExercises")
def Geocoding(row, geoloc ):
    place = f"{row['area-name-th']:}, {row['province-name-th']:} ,  Thailand"
    print( place )
    location = geolocator.geocode(place)
    #import pdb ; pdb.set_trace()
    if location is None:
        return None
    else:
        return location.point
df['geometry'] = df.apply( Geocoding, axis=1, 
                   result_type='expand', args=( geolocator, ) )
gdf = gpd.GeoDataFrame( df, crs='OGC:CRS84', geometry=df.geometry)

#df.to_file( "BulletinTsunami.kml", driver='KML', engine='pyogrio')

