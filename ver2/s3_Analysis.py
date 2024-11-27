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
from scipy.spatial.distance import cdist

from RiskAnalysis import *
from GlobBldg import *

def match_nearest_points(group1, group2):
    """
    Matches points from group1 to their nearest points in group2.
    """
    dist_matrix = cdist(group1, group2, metric='cityblock')
    nearest_indices = np.argmin(dist_matrix, axis=1)
    matches = [(i, nearest_indices[i]) for i in range(len(group1))]
    return matches

##################################################################
if __name__=="__main__":
    parser = argparse.ArgumentParser( prog=sys.argv[0],
                    description='Filter DEM from nearest MaxMw93 inundation heighs, Population from TOML min/max' )
    parser.add_argument( 'PROV', help='specified province name' )
    args = parser.parse_args()

    risk = RiskAnalysis( args.PROV )
    print( risk.TOML )
    VFILE = risk.getVFILE() ; AB=risk.getAbbrev()
    print( f'====================Processing {sys.argv[0]}===================' )

    ##################################################################
    if 0:
        GG_BLDG =  'DATA/305_buildings.csv'
        gg = GoogleGlobBldg( GG_BLDG, VFILE[0], NROWS=0 )
        #import pdb ;pdb.set_trace()
        gg_bldg = gg.gdf_[gg.gdf_.confidence>0.7]
        gg_bldg.to_file( VFILE[3], layer=f'{AB}:Building', driver='GPKG' )
    ##################################################################

    [MSL_minmax, Popu_minmax] = risk.getDEFAULT('MINMAX')
    gdfRegion = gpd.read_file( VFILE[0] )

    print(f'Writing Risk Analysis (Points) file "{VFILE[-1]}" ...')

    BUF_SIZ = 5_000 # meter
    gdfBuf = gpd.GeoDataFrame( gdfRegion.buffer( BUF_SIZ/111_000 ), columns=['geometry'] )

    gdfMw93= gpd.read_file( 'CACHE/TsunamiMax.gpkg', layer='MaxMw93' )
    gdfMw93 = gpd.sjoin( gdfMw93, gdfBuf,  how='inner', predicate='intersects' )
    gdfMw93.reset_index( drop=True, inplace=True )

    gdfDEM = GeoTIFF2df( VFILE[2], IN_RANGE=None, NAME="MSL")
    gdfDEM = gdfDEM[gdfDEM.MSL!=-32768]
    gdfDEM = gdfDEM[gdfDEM.MSL<=gdfMw93.H_Mw93.max()]
    gdfDEM.reset_index( drop=True, inplace=True )

    pnt1 = np.array([(point.x, point.y) for point in gdfDEM.geometry])
    pnt2 = np.array([(point.x, point.y) for point in gdfMw93.geometry])
    match_list = match_nearest_points( pnt1, pnt2)
    gdfDEM[['idx1','idx2']] = match_list
    def GetH_Mw93(row, gdfMw93):
        return gdfMw93.H_Mw93[ row.idx2 ]
    gdfDEM['H_Mw93'] = gdfDEM.apply( GetH_Mw93,axis=1, result_type='expand', args=( gdfMw93,) )
    gdfDEM['INUNDT'] = gdfDEM.H_Mw93 - gdfDEM.MSL
    gdfDEM = gdfDEM[ gdfDEM.INUNDT>0 ]
    #import pdb ; pdb.set_trace()

    gdfDEM.to_file( VFILE[-1], layer=f'{AB}:DEM', driver='GPKG' )

    gdfPopu = GeoTIFF2df( VFILE[1],IN_RANGE=Popu_minmax , NAME="Popu" )
    gdfPopu.Popu = gdfPopu.Popu.round(1)
    print( gdfPopu.Popu.describe() )
    gdfPopu.to_file( VFILE[-1] , layer=f'{AB}:Popu', driver='GPKG' )

    CMD = f'''find CACHE/{args.PROV} -maxdepth 1  -exec ls -ld {{}} \\; ''' 
    print(CMD); os.system( CMD )

