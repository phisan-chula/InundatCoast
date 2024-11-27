#
#  s7_FinalRiskMap
#
#
import os
import argparse
import geohash
import rasterio as rio
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point,MultiPoint,MultiPolygon
from shapely.ops import unary_union
from sklearn.cluster import DBSCAN
from pathlib import Path
from pyproj import Transformer
import matplotlib.pyplot as plt
from RiskAnalysis import *

GADM = r'/mnt/d/GeoData/GADM/gadm41_THA.gpkg' 
NOSTRA = r'/mnt/d/FieldData/NOSTRA_Tsunami_2024/DATA_GDB_20241001/DATA.gdb'

COAST_LINE = r'/mnt/d/FieldData/2024_TsunamiData/Coast_line_andaman.kml'
DEM = '/mnt/d/GeoData/FABDEM_TH/FABDEM_Thailand.vrt'  # nodata -9999
ROAD = '/mnt/d/FieldData/NOSTRA_Tsunami_2024/DATA_GDB_20241001/DATA.gdb','L_TRANS'

class MakeRiskArea:
    ''' Make Risk Area by PROVINCE '''
    def __init__(self, ARGS, PROVINCE):
        self.ARGS = ARGS
        self.RISK_OBJ = RiskAnalysis( PROVINCE )
        self.AB        = self.RISK_OBJ.getAbbrev()
        self.RISK_GPKG = self.RISK_OBJ.getVFILE()[-1]

        self.FINAL_RISK_GPKG = f'CACHE/{PROVINCE}/FinalRiskMap.gpkg'
        try:
            df = gpd.read_file( './CACHE/InitalRiskArea.gpkg', layer=self.AB ) # from S6
        except:
            import pdb; pdb.set_trace()
        df.crs='EPSG:4326'

        #REGION = 'Phuket' ,'Patong', Point(98.29659,7.89276)
        Path(f'./CACHE').mkdir(parents=True, exist_ok=True)
        Path(f'./CACHE/{PROVINCE}').mkdir(parents=True, exist_ok=True)

        final_risk = list()
        for i in range( len(df) ):
            mapsheet = df.iloc[i:i+1]
            ra = self.IntersectRiskArea( mapsheet[['PROV_CODE', 'Geohash','geometry']] )
            if len(ra)>0:
                final_risk.append( ra )
        self.dfFinalArea = pd.concat( final_risk )   # pop>=50  dist_max<1000
        if 0:
            self.IntersectRoad()
            self.MakeRoadPoint()
            self.GetRoadElev()
            self.WriteGPKG()

    def FilterFinalArea(self, POPU_MIN=50, DIST_MAX=1000 ):
        self.dfFinalArea  = self.dfFinalArea[ self.dfFinalArea.Popu>=POPU_MIN ]
        dfCOAST = gpd.read_file( COAST_LINE ).iloc[0].geometry
        is_near = self.dfFinalArea.distance( dfCOAST )*111_000 <= DIST_MAX
        self.dfFinalArea = self.dfFinalArea[ is_near ]
        #import pdb; pdb.set_trace()

    def IntersectRiskArea(self, MAPSHEET ):
        '''intersect inundation with low lying DEM '''
        gdfClustInun = gpd.read_file( self.RISK_GPKG, layer=f'{self.AB}:ClustDEM' )
        gdfClustPopu = gpd.read_file( self.RISK_GPKG, layer=f'{self.AB}:ClustPopu' )
        gdfPopu = gpd.read_file( self.RISK_GPKG, layer=f'{self.AB}:Popu', engine='pyogrio' )

        thePopu =  gpd.sjoin( gdfClustPopu, MAPSHEET, how='inner', predicate='within')

        gdfRiskArea = gpd.overlay( thePopu, gdfClustInun, how='intersection')
        gdfRiskArea = gdfRiskArea.drop( columns=[ 
            'Cluster_1', 'SumPopu', 'SumPopu_', 'index_right', 'Cluster_2' ])
        gdfRiskArea = gdfRiskArea.explode( ignore_index=True, index_parts=False)
        popu_ =  gpd.sjoin( gdfPopu, gdfRiskArea, how='inner' , predicate='intersects' )
        sum_popu_ = popu_.groupby('index_right').sum('Popu')
        #if self.AB=='SA': import pdb; pdb.set_trace()
        gdfRiskArea = gdfRiskArea.merge( sum_popu_, left_index=True, right_index=True, how='outer' )
        gdfRiskArea = gdfRiskArea.dropna()[ ['PROV_CODE', 'Geohash', 'Popu',  'geometry' ] ]
        if len( gdfRiskArea)>0:
            #import pdb ; pdb.set_trace()
            def MakeGH(row):
                ct = row.geometry.centroid
                return  geohash.encode( ct.y, ct.x, precision=8 )
            try:
                gdfRiskArea['geohash_part'] = gdfRiskArea.apply( MakeGH, axis=1, result_type='expand' )
            except:
                import pdb ; pdb.set_trace()
            gdfRiskArea['Popu'] = gdfRiskArea['Popu'].astype('int32')
        return gdfRiskArea

    def IntersectRoad(self, ROAD_SHORT=50 ):
        print( f'GetRiskArea        ROAD_SHORT = {ROAD_SHORT} meter...' )
        gdfRoad = gpd.read_file( ROAD[0], layer=ROAD[1] )[['RDLNCLASS','RDLNWIDTH','geometry']]
        assert gdfRoad.crs.to_epsg()==32647
        gdfRoad['Length']=gdfRoad.length
        gdfRoad = gdfRoad[gdfRoad.Length>=ROAD_SHORT]

        gdfRoad_ = gpd.overlay( gdfRoad, self.gdfRiskArea_z47, how='intersection')
        self.gdfRoad_wgs84 = gdfRoad_.to_crs( crs='epsg:4326' )

    def MakeRoadPoint(self, EPSm=50, MIN_PNT=2 ):
        # 7    	≤ 153m	×	153m    
        # 8     ≤ 38.2m ×       19.1m
        # 9     ≤ 4.77m ×       4.77m
        PREC=9 
        print( f'MakeRoadPoint() gh={PREC}digits  EPS={EPSm}m  MinPoint={MIN_PNT} ...')
        nodes = list()
        for i,row in self.gdfRoad_wgs84.iterrows():
            fr,to = row.geometry.boundary.geoms 
            nodes.extend( [ [fr.x,fr.y],[to.x,to.y]] )
        df = pd.DataFrame( nodes, columns=['x','y']) 
        clust = DBSCAN( EPSm/111_000, min_samples=MIN_PNT ).fit( df[['x','y']].to_numpy())
        df['label_'] = clust.labels_
        #print( df.value_counts() )
        junct = list()
        for i,row in df[df.label_==-1].iterrows():
            pnt = Point( row.x, row.y )
            gh = geohash.encode( pnt.y,pnt.x, precision=PREC )
            junct.append( [ -1, 1, gh, pnt ] )
        for grp,row in df[df.label_>-1].groupby('label_'):
            #pnt = Point( row.x.mean(), row.y.mean() )
            pnt = Point( row.iloc[0].x,  row.iloc[0].y ) # randomly choost the first one!
            gh = geohash.encode( pnt.y,pnt.x,precision=PREC )
            junct.append( [ grp, len(row), gh, pnt ] )
        dfRoadPnt = pd.DataFrame( junct, columns=[ 'label_', 'njunc', 'gh', 'geometry' ] )
        self.gdfRoadPnt = gpd.GeoDataFrame( dfRoadPnt, crs='epsg:4326', geometry=dfRoadPnt.geometry )

    def GetRoadElev(self):
        DEM_REGION = f'./CACHE/{self.PROV[0]}/{self.REGION[0]}.tif'
        minx, miny, maxx, maxy = self.gdfRiskArea.total_bounds
        CMD  = f'gdalwarp -overwrite  -multi -te {minx} {miny} {maxx} {maxy} '\
                f' -co COMPRESS=DEFLATE -ot Float32 -srcnodata -9999 -dstnodata -32768 '\
                f' {self.ARGS.dem} {DEM_REGION}'
        print( CMD ) ; os.system( CMD )
        df = self.gdfRoadPnt;  df['x'] = df.geometry.x; df['y'] = df.geometry.y
        with rio.open( DEM_REGION ) as ds:
            print( ds.meta)
            elevs = list()
            for elev in ds.sample( df[['x','y']].to_numpy().tolist() ):
                elevs.append( elev[0] )
            df['Elev'] = elevs  
        df['Elev'] = df['Elev'] + ( -1.025 )

        print( '*********** Applied -1.025 m for EGM2008->TGM2017**********' )
        df['Elev_'] = df['Elev'].map('{:.1f}'.format)
        #import pdb; pdb.set_trace()

    def WriteGPKG(self):
        #self.PROV = 'Phuket','PU'
        #self.gdfRoad_.to_file(   self.ELEV, layer=f'{self.PROV[1]}:Road_', driver='GPKG' )
        #self.gdfRoadPnt.to_file( self.ELEV, layer=f'{self.PROV[1]}:Elev', driver='GPKG' )
        #import pdb; pdb.set_trace()
        print( f'Writing {self.FINAL_RISK_GPKG} ...' )
        self.dfFinalArea.to_file(self.FINAL_RISK_GPKG, layer=f'FinalRisk', driver='GPKG' )

def ClusterRiskArea( gdfRiskArea ):
    print( f'Total RiskArea parts  = {len(gdfRiskArea)} ...' )
    print( f'Total RiskArea aggregrated ...')
    print( gdfRiskArea.Geohash.value_counts())
    RiskClust = list()
    for [prov,gh],row in gdfRiskArea.groupby( ['PROV_CODE', 'Geohash' ] ):
        #print( '{60*"-"}')
        #print( row )
        ctr = MultiPoint(row.geometry.centroid.to_list() ).centroid
        sqkm = row.geometry.area.sum()*111*111
        gh_list = row.geohash_part.to_list()
        RiskClust.append( [prov, gh, row.Popu.sum(), sqkm, gh_list, ctr] )
    dfRiskClust = pd.DataFrame( RiskClust, columns=['PROV', 'Geohash', 'Popu', 'SqKM', 'gh_list', 'geometry'] )
    gdfRiskClust = gpd.GeoDataFrame( dfRiskClust, crs='EPSG:4326', geometry=dfRiskClust.geometry ) 
    gdfRiskClust.reset_index( inplace=True )
    gdfRiskClust['SqKM'] = gdfRiskClust['SqKM'].round(2)
    
    #dfTambol = gpd.read_file(GADM, layer='ADM_ADM_3' )[['NAME_1', 'NAME_2', 'NAME_3', 'geometry']] 
    NAME_ADMIN = ['NAME1', 'NAME2', 'NAME3','NAME_ENG1', 'NAME_ENG2', 'NAME_ENG3', 'geometry' ]
    dfTambol = gpd.read_file(NOSTRA, layer='ADMIN_POLY' )[ NAME_ADMIN ] 
    dfTambol = dfTambol.to_crs( 'EPSG:4326' )
    #import pdb ;pdb.set_trace()
    gdfRiskClust = gpd.sjoin( gdfRiskClust, dfTambol, how='inner', predicate='within' )
    PlotReport(gdfRiskArea,gdfRiskClust)

def PlotReport(gdfRiskArea,gdfRiskClust):
    FINAL_CLUS = Path( 'CACHE/FinalRiskCluster' )
    gdfRiskClust.to_file( FINAL_CLUS.with_suffix('.gpkg'), layer=f'FinalCluster', driver='GPKG' )
    gdfRiskArea.to_file(  FINAL_CLUS.with_suffix('.gpkg'), layer=f'FinalArea', driver='GPKG' )
    gdfRiskArea.crs = 'OGC:CRS84'
    gdfRiskArea.to_file( 'CACHE/FinalRiskArea.kml',layer=f'RiskArea', driver='KML', engine='pyogrio' )
    #gdfRiskClust.crs = 'OGC:CRS84'
    #gdfRiskClust.to_file( FINAL_CLUS.with_suffix('.kml'), layer=f'FinalRiskCluster', driver='KML', engine='pyogrio' )
    df = gdfRiskClust[ ['PROV','Geohash','Popu','SqKM', 'gh_list'] ].copy()
    dftab = list()
    for i in range(len(df)):
        for j in range( len(df.iloc[i].gh_list) ):
            this_row = df.iloc[i:i+1].copy()
            #import pdb; pdb.set_trace()
            this_row['gh_list'] = df.iloc[i:i+1].iloc[0].gh_list[j]
            if j>0:
                this_row[['PROV', 'Geohash', 'Popu', 'SqKM']] = 4*['-']
            dftab.append( this_row )
    dftab = pd.concat( dftab )
    print( dftab.to_markdown( ) )
    #import pdb; pdb.set_trace()
    print( gdfRiskClust[ ['PROV','Geohash','Popu','SqKM', 'NAME1', 'NAME2', 'NAME3'] ].to_markdown() )
    print( gdfRiskClust[ ['PROV','Geohash','Popu','SqKM', 'NAME_ENG1', 'NAME_ENG2', 'NAME_ENG3'] ].to_markdown() )

#####################################################################
#####################################################################
#####################################################################
#PROV = 'Phuket|Ranong|Phangnga|Krabi|Trang|Satun'
parser = argparse.ArgumentParser(prog='s7_FinalRisk', description='read road and extrace elevations',
                    epilog='Text at the bottom of help')
parser.add_argument( 'PROV', help='specified province name' )
parser.add_argument('-d','--dem', default=DEM, help='DEM for extract spot heights' )
parser.add_argument('-p','--plot', action='store_true',help='Plot risk area,road,spot-heigts'  )

args = parser.parse_args()
print(args)

ra = list()
for prov in [args.PROV, ]:
#for prov in PROV.split('|'):
    risk_area = MakeRiskArea(args, prov )
    risk_area.FilterFinalArea(POPU_MIN=20, DIST_MAX=1000)
    risk_area.WriteGPKG()
    ra.append( risk_area.dfFinalArea ) 
gdf_RiskArea = pd.concat( ra, ignore_index=True )

ClusterRiskArea( gdf_RiskArea )

if args.plot:
    fig, ax = plt.subplots(figsize = (10,10))
    ev.gdfRoad_.plot( color='red', ax=ax)
    ev.gdfRiskArea.plot( edgecolor='black', facecolor='none', ax=ax )
    ev.gdfRoadPnt.plot( color='blue', ax=ax )
    for idx,row in ev.gdfRoadPnt.iterrows():
            ax.annotate( row['Elev_'], (row['x'],row['y']) )
    plt.xticks( rotation=90 )
    plt.title( TITLE )
    plt.show()

