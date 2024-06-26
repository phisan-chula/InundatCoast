#!/home/phisan/miniconda3/envs/gee/bin/python3
#
#
#
import sys,os
import numpy as np
import argparse
import pandas as pd
import geopandas as gpd
import rioxarray
import numpy as np
from shapely.geometry import Point,MultiPoint
from alpha_shapes import Alpha_Shaper, plot_alpha_shape
from sklearn.cluster import DBSCAN
from RiskAnalysis import *

##############################################################
def DoClusterPolygon( gdf, EPS_m,MIN_pnt, POPU_COL=None ):
    pnts = gdf[['x','y']].to_numpy() 
    clustering = DBSCAN( eps=EPS_m/111_000, min_samples=MIN_pnt, n_jobs=-1).fit(pnts)
    gdf['Cluster']=clustering.labels_
    print( gdf['Cluster'].value_counts() )
    gdf = gdf[~(gdf.Cluster==-1)].copy()
    if len( gdf )==0: raise Exception("***DoCluster() failed!***")

    ClustPoly = list()
    for clust,grp in gdf.groupby( 'Cluster' ): 
        if POPU_COL:                                # round-off to hundred
            shaper = Alpha_Shaper( grp[['x','y']].to_numpy() )  # use concave polygon
            poly = shaper.get_shape( alpha=10.0)
            sum_pop  = int(grp[POPU_COL].sum())
            sum_pop_ = '{:,d}'.format( round( sum_pop ,-2) )
            ClustPoly.append( [clust, sum_pop, sum_pop_, poly] )
        else:
            #import pdb; pdb.set_trace()
            shaper = Alpha_Shaper( grp[['x','y']].to_numpy() )  # use concave polygon
            poly = shaper.get_shape( alpha=10.0)
            #poly = MultiPoint( grp.geometry.to_list() ).convex_hull
            ClustPoly.append( [clust, poly] )
    if POPU_COL: COLS = ['Cluster', 'SumPopu', 'SumPopu_', 'geometry']
    else: COLS = ['Cluster','geometry']

    df = pd.DataFrame( ClustPoly, columns=COLS )
    gdf = gpd.GeoDataFrame( df, crs='EPSG:4326', geometry=df.geometry )
    gdf = gdf[~gdf.geometry.is_empty].copy()   # clean-up GEOMETRYCOLLECTION EMPTY
    return gdf

##################################################################
if __name__=="__main__":
    parser = argparse.ArgumentParser( prog=sys.argv[0],
                    description='What the program does' )
    parser.add_argument( 'PROV', help='specified province name' )
    args = parser.parse_args()

    risk = RiskAnalysis( args.PROV )
    print( risk.TOML )
    VFILE = risk.getVFILE() ; AB=risk.getAbbrev()
    print( f'****************** Processing {args.PROV} *******************' )
    ### gdfBldg = gpd.read_file( VFILE[3], layer=f'{AB}:Building' )
    #import pdb; pdb.set_trace()
    gdfPopu = gpd.read_file( VFILE[-1], layer=f'{AB}:Popu' )
    gdfDEM = gpd.read_file( VFILE[-1], layer=f'{AB}:DEM' )

    [[ DEM_EPS_m, DEM_MIN_pnt],[POPU_EPS_m, POPU_MIN_pnt]] = risk.getDEFAULT('DBSCAN')
    ##############################################################
    print( f'****************** Convex Clustering Inundated DEM { DEM_EPS_m, DEM_MIN_pnt} *******************' )
    gdfClustDEM = DoClusterPolygon( gdfDEM, DEM_EPS_m, DEM_MIN_pnt )
    gdfClustDEM.to_file( VFILE[-1], layer=f'{AB}:ClustDEM', driver='GPKG' )

    ##############################################################
    print( f'****************** Concave Clustering Population {POPU_EPS_m, POPU_MIN_pnt}  *******************' )
    gdfClustPopu = DoClusterPolygon( gdfPopu,POPU_EPS_m, POPU_MIN_pnt, POPU_COL='Popu' )
    gdfClustPopu.to_file( VFILE[-1], layer=f'{AB}:ClustPopu', driver='GPKG' )

    print(f'Writing polygon around cluster to "{VFILE[-1]}" ...')

