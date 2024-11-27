#
# s6_InititialRisk : 
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
        dist_coast = int(shapely.distance( row.geometry, GDF_COAST.iloc[0].geometry )*111_000)
        return gh, wxh, dist_coast, map_ext 
    df[[ 'Geohash','WxH', 'dist_coast', 'geometry']] = df.apply( MakeGeohash, axis=1, 
                    args=(gdf_coast,), result_type='expand' )
    #import pdb ;pdb.set_trace()
    return df 

def WriteKML( df , MAPSHEET_KML ):
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
            pnt = fol.newpoint( name=f'{row.Geohash}({row.SumPopu_})', coords=[(ctrd.x,ctrd.y)] )
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
    kml.save( MAPSHEET_KML )

###########################################################################################
###########################################################################################
###########################################################################################
if 1:
    EXCLUDE = [  
                 #'w1muy6',   # Phuket (541,700)
                 'w1qq52',   # Krabi (36,700)
                 'w1qmhm',   # Krabi (228)
                 'w1qmhy',   # Krabi (826)
                 'w1qc35',   #  Krabi (600)
                ]
    EXCLUDE = '|'.join( EXCLUDE ) 
else:
    EXCLUDE = None

RESULT_DIR = r'./CACHE'
RISK_ANALY = r'RiskAnalysis.gpkg'
INIT_RISK_AREA = r'CACHE/InitalRiskArea'  #  .gpck ; .kml
COAST_LINE = r'/mnt/d/FieldData/2024_TsunamiData/Coast_line_andaman.kml'
PARAM = pd.Series( { 'POPU_MIN'    : 300, 
                     'POPU_MIN_PU' : 500, 
                     'DIST_COAST'  : 1000    # meter
                   } )
print( f'{40*"="}\n{PARAM:}\n{40*"="}\n' )

dfs = list()
files = list( Path( RESULT_DIR ).glob( f'*/{RISK_ANALY}' ) )
if len(files)==0:
    raise Exception( '***ERROR*** no ..RiskAnalysis.gpkg' )
else:
    for f in files:
        df = ReadRiskAnaly( f, COAST_LINE )
        dfs.append(df)
dfSheet = pd.concat( dfs, ignore_index=True )
dfSheet = gpd.GeoDataFrame( dfSheet, crs='EPSG:4326' , geometry=dfSheet.geometry )
bDUP = dfSheet.Geohash.duplicated().any()
print( f'No duplicates GH : {not bDUP:} ... ') 

###########################################################################
WriteKML( dfSheet, f'{INIT_RISK_AREA}_ALL_{len(dfSheet)}.kml'  )
##########################################################################
if EXCLUDE is not None:
    #import pdb ; pdb.set_trace()
    EXCLUDE = dfSheet['Geohash'].str.contains( EXCLUDE )
    dfSheet_excl =  dfSheet[ EXCLUDE ]
    print( f'EXCLUDEing.... --> {len(dfSheet_excl)} areas of {len(EXCLUDE)}  ...' )
    print( dfSheet_excl )
    dfSheet      =  dfSheet[~EXCLUDE]
    #import pdb ; pdb.set_trace()
    print( f'after exclude {EXCLUDE} .... no.sheet={len(dfSheet)} ' )
    print( f'====== All risk areas : {len(dfSheet)} =======')
    print( dfSheet.PROV_CODE.value_counts() )

    dfSheet = dfSheet[dfSheet.SumPopu>PARAM['POPU_MIN'] ].copy()                 # *** SumPopu *** #
    _bExcl = (dfSheet.PROV_CODE=='PU') & (dfSheet.SumPopu< PARAM['POPU_MIN_PU'] )
    dfSheet = dfSheet[ ~_bExcl ].copy()

############################################################################
print( f'Number of Risk-area MapSheet {len(dfSheet)}... ')
############################################################################

dfSheet = dfSheet[dfSheet.dist_coast< PARAM['DIST_COAST'] ]                 # *** dist_cost *** #
print( f'Number of coastal risk-area MapSheet {len(dfSheet)}... ')
print( dfSheet.PROV_CODE.value_counts() )

print( f'Writing {INIT_RISK_AREA} .kml|.gpkg ...')

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
    #import pdb ; pdb.set_trace()

    row.to_file( f'{INIT_RISK_AREA}.gpkg', layer=f'{grp}' , driver='GPKG', engine='pyogrio' )
dfs = pd.concat( dfs )
dfs.reset_index( inplace=True )
print( dfs.to_markdown() )

WriteKML( dfSheet, f'{INIT_RISK_AREA}.kml'  )
print( '************** end s6_InitialRiskMap.py *************')
#import pdb ; pdb.set_trace()
