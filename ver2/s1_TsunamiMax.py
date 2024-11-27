#
#
#
import pandas as pd
import geopandas as gpd
import re
from pathlib import Path

Path(f'./CACHE/').mkdir(parents=True, exist_ok=True)

TDATA = Path( r'/mnt/d/FieldData/2024_TsunamiData' )
dfMAX = pd.read_excel( TDATA/'zm_at_30pnts_2024.xlsx', header=None, 
        names=[ 'Location', 'TsunamiMax', 'code', 'lat', 'lng'] )
dfMw93 = pd.read_excel( TDATA/'Mw93_eta_hgt_at_shoreline_R2.xlsx', 
        engine='openpyxl' )
dfMw93.columns = [ 'lng', 'lat', 'ETA_hr', 'H_Mw93' ]
#import pdb ;pdb.set_trace()

########################################################################
HAT_TIDE = 1.11  # meter , ref  Prof.Dr. Anat , Chulalongkorn University
print(  '*******************************************************')
print( f'Adding highest astronomical tide (HAT) : {HAT_TIDE} meter...')
print(  '*******************************************************')
dfMAX['TsunamiMax'] = HAT_TIDE + dfMAX['TsunamiMax'] 
dfMw93['H_Mw93'] =  HAT_TIDE + dfMw93['H_Mw93']
#######################################################################
gdfMAX = gpd.GeoDataFrame( dfMAX, crs='EPSG:4326', 
                geometry=gpd.points_from_xy( dfMAX.lng, dfMAX.lat ) )
gdfMw93 = gpd.GeoDataFrame( dfMw93, crs='EPSG:4326', 
                geometry=gpd.points_from_xy( dfMw93.lng, dfMw93.lat ) )
PROV = 'Phuket|Ranong|Phangnga|Krabi|Trang|Satun'.split('|')

def MakeLOC(row,PROV):
    for prov in PROV:
        if prov.upper() == row.Location[ :len(prov)].upper():
            return prov, row.Location[len(prov):]
    print( row.Location )
    raise '***ERROR***'
gdfMAX[['PROV','Location']] = gdfMAX.apply( MakeLOC, axis=1, result_type='expand', args=(PROV,) )
for prov,row in gdfMAX.groupby('PROV'):
    print( prov, row.TsunamiMax.max() )
#import pdb ;pdb.set_trace()

TSU_MAX = './CACHE/TsunamiMax.gpkg'
print( f'Plotting gpkg "{TSU_MAX}"  layers={{MaxLocation|MaxMw93}} ...')
gdfMAX.to_file(  TSU_MAX, driver='GPKG', layer='MaxLocation' )
gdfMw93.to_file( TSU_MAX, driver='GPKG', layer='MaxMw93' )
#assert len(dfLOC) == len(df)
