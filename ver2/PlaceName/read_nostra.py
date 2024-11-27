#
#
#
from pathlib import Path
import numpy as np
import pandas as pd 
import geopandas as gpd 

LOC_CODE = { 'CellTower' : 75200, }

class POI:
    def __init__(self):
        self.CACHE = Path( './CACHE_POI' )
        self.CACHE.mkdir(parents=True, exist_ok=True) 

        GDB = '/mnt/d/FieldData/NOSTRA_Tsunami_2024/DATA_GDB_20241001/DATA.gdb',\
              'LANDMARK'
        APPENDIX = '/mnt/d/FieldData/NOSTRA_Tsunami_2024/APPENDIX_20241001.xlsx'
        dfLM = pd.read_excel( APPENDIX )  

        dfLM = dfLM[ dfLM.LOCAL_X.isin(['X','x']) ]
        dfLM.LOCAL_CODE = dfLM.LOCAL_CODE.astype(np.int64)
        print( f'======= number of landmark codes {len(dfLM)} ========' )
        print( dfLM[[ 'LOCAL_CODE',  'LOCAL_CODE_DESCRIPTION', 'LOCAL_X' ]] )
        ############################################################################
        df = gpd.read_file( GDB[0], layer=GDB[1])
        df.LOCAL_CODE = df.LOCAL_CODE.astype(np.int64)
        poi   = df.POI_CODE.value_counts() 
        local = df.LOCAL_CODE.value_counts()
        print( poi )
        print( local )

        #############################################################################
        dfPOI = df[df.LOCAL_CODE.isin( dfLM.LOCAL_CODE.values ) ]  # manual selected from 
        cols = [ 'POI_CODE', 'LOCAL_CODE', 'NAME', 'NAME_ENG', 'VERSION', 'geometry' ]
        dfPOI = dfPOI[cols].copy()
        print( f'Number of selected POIs : {len(dfPOI)} ...' )
        dfPOI_cnt = dfPOI.LOCAL_CODE.value_counts()
        dfPOI_cnt = dfPOI_cnt[ dfPOI_cnt >= 10]

        dfPOI_10 = dfLM[ dfLM.LOCAL_CODE.isin( dfPOI_cnt.keys() ) ].copy()
        dfPOI_10['COUNT'] = dfPOI_cnt.sort_index().values

        assert df.crs.to_epsg() == 32647
        dfInfra = df[ df.LOCAL_CODE.isin( dfPOI_10.LOCAL_CODE ) ].copy()
        dfInfra['Note1'] = ''
        dfInfra['Note2'] = ''
        dfInfra['Note3'] = ''
        dfInfra = dfInfra.to_crs('EPSG:4326')
        POI_CACHE = self.CACHE / 'POI_Andaman_NOSTRA.gpkg'
        print( f'Writing {POI_CACHE} ...' ) 
        for grp, row in dfInfra.groupby( 'LOCAL_CODE' ) :
            LC = dfPOI_10[ dfPOI_10.LOCAL_CODE==grp].LOCAL_CODE_DESCRIPTION.iloc[0]
            LC = LC.split('/')[0]
            row.to_file( POI_CACHE, driver='GPKG', layer=f'{grp:05d}:{LC}({len(row)})') 
        #import pdb; pdb.set_trace()

###############################################################################
###############################################################################
###############################################################################
poi = POI()

