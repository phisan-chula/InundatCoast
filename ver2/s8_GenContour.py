#!/home/phisan/miniconda3/envs/gee/bin/python3
#
#
#
import sys,os
import argparse
import pyogrio
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely import Point, LineString, MultiPoint, MultiPolygon, Polygon
from shapely import wkt,unary_union,ops
from pathlib import Path
from RiskAnalysis import *

gpd.options.io_engine = "pyogrio"

DEM = '/mnt/d/GeoData/FABDEM_TH/FABDEM_Thailand.vrt'  # nodata -9999
COAST_LINE = r'/mnt/d/FieldData/2024_TsunamiData/Coast_Tsunami6Prov.kml'
D2M = 111_000  # degree to meter
CIs = [ 0.01, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15 ]

class InundateCoast:
    def __init__(self):
        Path("./CACHE").mkdir(parents=True, exist_ok=True)
        self.BUF_GPKG  = './CACHE/BUFFER_coast.gpkg'
        self.DEM_COAST = './CACHE/DEM_coast.tiff'
        self.CONTR     = './CACHE/CONTR_coast.gpkg' 
        self.CONTR_CLN = Path('./CACHE/CONTR_coast_clean.gpkg') 
        self.gdfCOAST_ = gpd.read_file( COAST_LINE , layer='Coast_Tsunami6Prov', engine='pyogrio' )
        #import pdb ; pdb.set_trace()
        #####################################################
        print( f'__init__()\n : {self.gdfCOAST_} ...\n')
        bufs = list()
        for i,row in self.gdfCOAST_.iterrows():
            parts = row['Name'].split('_')
            PROV = parts[0]
            PART = '-'
            if len(parts)==2:
                PART = parts[1]
            dist = np.array(  row.Description.split('|') ).astype(int)
            ls = LineString([(x, y) for x, y, z in row.geometry.coords])
            if dist[0]!=0:
                buf_L = ls.buffer( +dist[0]/111000, cap_style=2, join_style=3, single_sided=True )
            if dist[1]!=0:
                buf_R = ls.buffer( -dist[1]/111000, cap_style=2, join_style=3, single_sided=True )
            if dist[0]!=0 and dist[1]!=0:
                bufLR = unary_union( [buf_L,buf_R] )
            elif dist[0]!=0:
                bufLR = buf_L
            else:
                bufLR = buf_R
            bufLR = self.CleanMultiPolygon( bufLR )
            bufs.append( [PROV, PART, row['Name'], bufLR] )
        all_poly = unary_union( np.array(bufs)[:,-1] )
        all_poly = self.CleanMultiPolygon( all_poly )
        bufs.append( ['6_PROV','All', 'All_Coast', all_poly ] )
        dfCOAST = pd.DataFrame( bufs, columns=[ 'PROV', 'PART', 'Name', 'geometry' ] )
        self.gdfCOAST = gpd.GeoDataFrame( dfCOAST, crs='EPSG:4326', geometry=dfCOAST.geometry )
        print( f'Writing n={len(self.gdfCOAST)} GPKG {self.BUF_GPKG} ...' )
        for i in range(len( self.gdfCOAST)):
            row = self.gdfCOAST.iloc[i:i+1]
            NAME = row.iloc[0]['Name']
            row.to_file( self.BUF_GPKG, driver='GPKG', layer=f'{NAME:}' )
        self.gdfCOAST_.to_file( self.BUF_GPKG, driver='GPKG', layer='coast_defined' ) 
        #import pdb ; pdb.set_trace()

    def CleanMultiPolygon( self,polys ):
        '''extract only "exterior" of polygon '''
        #import pdb ; pdb.set_trace()
        print( f'CleanMultiPolygon() ==> {polys.geom_type} extract ".exterior" ... ')
        if polys.geom_type=='Polygon':
            return Polygon(polys.exterior)    
        else:
            ext_poly = list()
            for poly in polys.geoms:
                ext_poly.append( Polygon( poly.exterior )  )
            return MultiPolygon( ext_poly)

    def MakeContour( self ):
        OPT_CI = '-fl ' + ' '.join( map( str, CIs ))
        print( f'MakeContour() : CI:{CIs} meter')
        contour  = Path(DEM).parent / f'{Path(DEM).stem}_contour.gpkg'
        #PIXEL = ' -tr {} {}'.format( * [0.000277777777778/2]*2 )
        PIXEL = ''
        CMD1  = f'''gdalwarp -overwrite -cutline {self.BUF_GPKG} -cl All_Coast '''\
                f''' -multi -crop_to_cutline -co COMPRESS=DEFLATE -ot Float32 {PIXEL} '''\
                f''' -r cubic -srcnodata -9999 -dstnodata -32768 {DEM} {self.DEM_COAST}'''
        print( CMD1 ) ; os.system( CMD1 )
        CMD2 = f'gdal_contour -a MSL  -b 1 -f GPKG {OPT_CI} {self.DEM_COAST} {self.CONTR}'
        print( CMD2 ) ; os.system( CMD2 )

    def CleanContour( self ):
        gdf = gpd.read_file( self.CONTR,  engine='pyogrio' )
        gdf['MSL'] = gdf['MSL'].astype(int)
        #import pdb ; pdb.set_trace()
        gdf_filtered = gdf[gdf.geometry.apply(lambda geom: geom.length > 100/111_000)]  # Short= 100m 
        gdf_filtered = gdf_filtered[gdf_filtered.geometry.apply(lambda geom: len(geom.coords) > 7)] # optimal!
        print( f'STEP3 : filter len>100m and nPoints>7 and writing "{self.CONTR_CLN}"...' ) 
        #gdf_filtered.to_file(self.CONTR_CLN, driver='GPKG' ) 
        for ci,grp in gdf_filtered.groupby('MSL'):
            grp.to_file( self.CONTR_CLN, layer=f'CI_{ci:02d}m', driver='GPKG' )
        CMD =  f'''ogr2ogr  -mapFieldType Integer64=Real -f KML '''\
               f''' {self.CONTR_CLN.with_suffix('.kml')} {self.CONTR_CLN}'''
        print( CMD ) ; os.system( CMD )

    def AverageTsunamiMax(self):
        Q = 95  #   0-100  
        TIDE = 1.11  # meter
        print( f'\n{56*"*"}\nAverage Tsunami Wave Height :   quant={Q}%   tide={TIDE} m.\n{56*"*"}\n',)
        df = gpd.read_file( f'CACHE/TsunamiMax.gpkg', layer='MaxMw93' )
        self.TsunamiHeight = gpd.sjoin( df, self.gdfCOAST[:-1], how='inner', predicate='intersects' )
        DivMSL = list()
        for pp,row in self.TsunamiHeight.groupby( 'Name' ):
            min_ = row.H_Mw93.min()
            mean = row.H_Mw93.mean()
            quan = row.H_Mw93.quantile(Q/100.)
            max_ = row.H_Mw93.max()
            print( f'{40*"*"}\n{40*"*"}\n{pp:^40s}')
            print( f'min/mean/max     :{min_:4.1f}/{mean:4.1f}/{max_:4.1f} meter' )
            print( f'quan{Q:.0f}%          : {quan:.1f} meter')
            print( f'Tide+quan{Q:.0f}%     : {quan+TIDE:.1f} meter')
            print( f'count            : {len(row)}\n{40*"*"}')
            LS = self.gdfCOAST_[self.gdfCOAST_.Name==pp].iloc[0].geometry
            grpMSL = self.AverageTsunami_Dist( pp,row,LS )
            print( grpMSL[['cnt','mean','max']] )
            DivMSL.append( grpMSL ) 
        dfGrpMSL = pd.concat( DivMSL )
        self.gdfGrpMSL = gpd.GeoDataFrame( dfGrpMSL, crs='epsg:4326', geometry=dfGrpMSL.geometry )
        self.gdfGrpMSL.to_file( self.BUF_GPKG, driver='GPKG', layer='Avg.MSL' ) 
        #import pdb ;pdb.set_trace()

    def AverageTsunami_Dist(self, PROV_PART, dfPNT, LS, DIV=5_000 ):
        LS_dist = LS.length*111_000
        BINS = np.arange( 0, LS_dist, DIV )
        if (LS_dist-BINS[-1]) > 1_000 :  # last division > 1 km !
            BINS = np.append( BINS, [ LS_dist ] )

        pnt_mid = list()
        for i in range(len(BINS)-1): 
            sub = ops.substring( LS, BINS[i]/D2M, BINS[i+1]/D2M, normalized=False )
            pnt_mid.append( sub.interpolate( 0.5, normalized=True ) )

        data = list() 
        for i,row in dfPNT.iterrows():
            dist = LS.project( row.geometry,normalized=False )*111_000  # to meter
            data.append( [PROV_PART, dist, row.H_Mw93 ] )
        df = pd.DataFrame( data, columns=[ 'PROV', 'dist_m', 'MSL'  ] )
        df['bins'] = pd.cut( df.dist_m, bins = BINS, ordered=True, precision=0 )
        df_cnt  = df.groupby( 'bins', observed=True )['MSL'].count()
        df_mean = df.groupby( 'bins', observed=True )['MSL'].mean()
        df_max  = df.groupby( 'bins', observed=True )['MSL'].max()
        grpMSL  = pd.concat( [df_cnt,df_mean,df_max] , axis=1 )
        grpMSL.columns =['cnt','mean','max']
        grpMSL['mean'] = grpMSL['mean'].round(1)
        grpMSL['max'] = grpMSL['max'].round(1)
        grpMSL['geometry'] = pnt_mid
        grpMSL['PROV_PART'] = PROV_PART
        #import pdb;pdb.set_trace()
        return grpMSL 

##################################################################
##################################################################
##################################################################
if __name__=="__main__":
    print( f'*** DEM : {DEM} ***')
    parser = argparse.ArgumentParser( prog=sys.argv[0],
                    description='plot Tsunami height and generate coastal contour' )
    parser.add_argument("-c", "--contour", action="store_true", 
                    help=f"plot contour at CI = {CIs}")
    args = parser.parse_args()
    print( args )
    #import pdb ;pdb.set_trace()
    coast = InundateCoast()
    coast.AverageTsunamiMax()
    if args.contour:
        coast.MakeContour( )
        coast.CleanContour( )
    else:
        print('***WARNING*** no contour plotting...')
        print('***WARNING*** no contour plotting...')
        print('***WARNING*** no contour plotting...')
    print( f'************* end of {sys.argv[0]} ******************')
