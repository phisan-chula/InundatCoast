#
# s6_MakeMap : 
#
import pandas as pd
import geopandas as gpd
import fiona
import Geohash
import pyogrio
import shapely
from simplekml import Kml, Style
from pathlib import Path
from shapely.geometry import Point,box
from RiskAnalysis import *
gpd.options.io_engine = "pyogrio"

#####################################################
#####################################################
FORCE_REMOVE = [ 'w1muy6' ]
#####################################################
#####################################################

def ReadRiskAnaly( f, coast_line ):
    gdf_coast = gpd.read_file( coast_line, layer='Andaman_line_merge', engine='pyogrio' )
    layers = fiona.listlayers( f )
    thelayer = [item for item in layers if 'ClustPopu' in item][0]
    PROV = thelayer[0:2]
    df = gpd.read_file( f, layer=thelayer )
    df['PROV_CODE'] = PROV
    def MakeGeohash(row,GDF_COAST):
        centr = row.geometry.centroid
        gh = Geohash.encode( centr.y ,centr.x, 6)
        xmin, ymin, xmax, ymax = row.geometry.bounds
        map_ext = box( xmin, ymin, xmax, ymax, ccw=True )
        width = 111*(xmax-xmin)
        height = 111*(ymax-ymin)
        wxh = f'{width:.1f} km x {height:.1f} km'
        dist_coast = shapely.distance( row.geometry, GDF_COAST.iloc[0].geometry )*111_000
        return gh, wxh, dist_coast, map_ext 
    df[[ 'Geohash','WxH', 'dist_coast', 'geometry']] = df.apply( MakeGeohash, axis=1, 
                    args=(gdf_coast,), result_type='expand' )
    #import pdb ;pdb.set_trace()
    return df 

def WriteKML( df ):
    sharedstyle = Style()
    sharedstyle.labelstyle.color = 'ff0000ff'  # Red
    sharedstyle.polystyle.color = '990000ff'  # Transparent red
    sharedstyle.polystyle.outline = 0
    kml = Kml() 
    for prov,prov_row in df.groupby('PROV_CODE'):
        fol = kml.newfolder( name=f'{prov}' )
        for i,row in prov_row.iterrows():
            #import pdb ;pdb.set_trace()
            ctrd = row.geometry.centroid
            pnt = fol.newpoint( name=f'{row.Geohash}:{row.SumPopu_}', coords=[(ctrd.x,ctrd.y)] )
            pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/water.png'
            pol = fol.newpolygon( name=f'{row.PROV_CODE}:{row.Geohash}' )
            pol.description = f"""
            <html>
            <body>
              <p>Resident: {row.SumPopu:,d}</p>
              <p>Geohash: {row.Geohash}</p>
              <p>WxH (km x km): {row.WxH}</p>
              <p>Andaman Inundation Map for Tsunami Waring (2024,Aug)</p>
            </body>
            </html>
            """
            pol.outerboundaryis = list(row.geometry.exterior.coords)
            pol.style = sharedstyle
    kml.save( './CACHE/MapSheet.kml' )

###########################################################################################
###########################################################################################
###########################################################################################
EXCLUDE = [ 'w1muy6',   # PHUKET
            'w1mux0' ]
EXCLUDE = '|'.join( EXCLUDE ) 

RESULT_DIR = r'./CACHE'
RISK_ANALY = r'/RiskAnalysis.gpkg'
COAST_LINE = r'./DATA/Coast_line_andaman.kml'
PARAM = pd.Series( { 'POPU_MIN'    : 200, 
                     'POPU_MIN_PU' : 500, 
                     'DIST_COAST'  : 1000    # meter
                   } )
print( f'{40*"="}\n{PARAM:}\n{40*"="}\n' )

dfs = list()
files = list( Path( RESULT_DIR ).glob( f'*/{RISK_ANALY}' ) )
if len(files)==0:
    raise Exception( '***ERROR*** no ..RiskAnalysis.gpck' )
else:
    for f in files:
        df = ReadRiskAnaly( f, COAST_LINE )
        dfs.append(df)
dfSheet = pd.concat( dfs, ignore_index=True )
dfSheet = gpd.GeoDataFrame( dfSheet, crs='EPSG:4326' , geometry=dfSheet.geometry )

bDUP = dfSheet.Geohash.duplicated().any()
print( f'No duplicates GH : {not bDUP:} ... ') 
#import pdb ; pdb.set_trace()
dfSheet =  dfSheet[~dfSheet['Geohash'].str.contains( EXCLUDE )]
print( f'exclude {EXCLUDE} .... no.sheet={len(dfSheet)} ' )
print( f'====== All risk areas : {len(dfSheet)} =======')
print( dfSheet.PROV_CODE.value_counts() )


dfSheet = dfSheet[dfSheet.SumPopu> PARAM['POPU_MIN'] ].copy()                 # *** SumPopu *** #
_bExcl = (dfSheet.PROV_CODE=='PU') & (dfSheet.SumPopu< PARAM['POPU_MIN_PU'] ) # *** SumPopu *** Phuket #
dfSheet = dfSheet[ ~_bExcl ].copy()
print( f'Number of Risk-area MapSheet {len(dfSheet)}... ')
############################################################################
dfSheet = dfSheet[dfSheet.dist_coast< PARAM['DIST_COAST'] ]                 # *** dist_cost *** #
print( f'Number of coastal risk-area MapSheet {len(dfSheet)}... ')
print( dfSheet.PROV_CODE.value_counts() )
print( 'Writing ./CACHE/MapSheet.gpkg ...')

dfSheet.crs = 'OGC:CRS84'
dfs = list()
for grp,row in dfSheet.groupby('PROV_CODE'):
    print( f'================== {grp} ====================')
    df = row[['Geohash', 'SumPopu_', 'dist_coast' , 'WxH' ]].copy()
    df['dist_coast'] = ( df['dist_coast']/1000 ).map( '{:.1f} km'.format )
    df['PROV'] = grp
    df.sort_values(by='Geohash', inplace=True)
    #print( df )
    dfs.append( df )
    row.to_file( './CACHE/MapSheet.gpkg', layer=f'{grp}' , driver='GPKG', engine='pyogrio' )
dfs = pd.concat( dfs )
dfs.reset_index( inplace=True )
print( dfs.to_markdown() )
WriteKML( dfSheet )

print( '************** end s6_MakeMap.py *************')
#import pdb ; pdb.set_trace()
