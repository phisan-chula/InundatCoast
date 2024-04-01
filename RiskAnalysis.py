#
#
#
import tomllib
import os,sys
import pandas as pd
import geopandas as gpd
import numpy as np
import rioxarray
from pathlib import Path
from shapely.geometry import LineString, box
import warnings
warnings.filterwarnings("ignore", message="Geometry is in a geographic CRS")
gpd.options.io_engine = "pyogrio"

#############################################################################
def GeoTIFF2df( GeoTIFF, IN_RANGE=None, NAME='VALUE' ):
    da = rioxarray.open_rasterio( GeoTIFF )
    ds = da.to_dataset(name=NAME)
    df = ds.to_dataframe().reset_index()
    if IN_RANGE:
        df = df[ (df[NAME]>=IN_RANGE[0]) & (df[NAME]<=IN_RANGE[1]) ]
    gdf = gpd.GeoDataFrame( df, crs='EPSG:4326',
          geometry=gpd.points_from_xy( df.x, df.y))
    return gdf

#############################################################################
class RiskAnalysis:
    VULNER_FILES = [ 'VulnerRegion.gpkg', 'VulnerPopu.tif', 'VulnerDEM.tif', 'VulnerBldg.gpkg', 
                     'RiskAnalysis.gpkg' ]   # RiskAnalysis.gpkg , the last file
    def __init__( self, PROV=None ):
        self.PROV = PROV
        with open( 'CONFIG.toml','rb') as f:
            self.TOML = tomllib.load(f)
        Path(f'./CACHE/{PROV}').mkdir(parents=True, exist_ok=True)
        Path('./DEM').mkdir(parents=True, exist_ok=True)

        self.dfProv = self.AndamanProv()
        minx, miny, maxx, maxy = self.dfProv.total_bounds
        grid = self.generate_rectangles( minx, miny, maxx, maxy, 1 )
        dfGrid = pd.DataFrame( grid, columns=['geometry'] )

        simpl_prov = self.dfProv.geometry.unary_union.simplify( tolerance=250/111_000)
        dfGrid['Coast'] = dfGrid['geometry'].apply(lambda poly: poly.intersects( simpl_prov ) )
        dfGrid = dfGrid[dfGrid.Coast].copy()
        def mkgrid( row ):
            minx, miny, maxx, maxy = row.geometry.bounds
            dem_grid = f'n{int(miny):02d}e{int(minx):03d}'
            dem_hgt = f'./DEM/{dem_grid}.hgt'
            dem_zip = f'NASADEM_HGT_{dem_grid}.zip'
            URL = f'https://e4ftl01.cr.usgs.gov/MEASURES/NASADEM_HGT.001/2000.02.11/{dem_zip}'
            return dem_hgt, dem_zip, URL
        dfGrid[ ['DEM_HGT', 'DEM_ZIP', 'URL'] ] = dfGrid.apply( mkgrid, axis=1, result_type='expand' )
        self.dfGrid = dfGrid

    def generate_rectangles( self, min_x, min_y, max_x, max_y, resolution):
      """
      Generates rectangles from a mesh grid within a bounding box.
      """
      min_x = np.floor(min_x) ; min_y = np.floor(min_y)
      max_x = np.ceil(max_x) ; max_y = np.ceil(max_y)
      X, Y = np.mgrid[min_x:max_x+resolution:resolution, min_y:max_y+resolution:resolution]
      rectangles = []
      for xmin, xmax, ymin, ymax in zip(X.flatten(), X.flatten() + resolution,\
                                        Y.flatten(), Y.flatten() + resolution):
        rectangles.append( box( xmin, ymin, xmax, ymax, ccw=True ) )
      return rectangles

    def AndamanProv(self):
        prov =  self.TOML['REGION_PROV'].split('|')
        df = gpd.read_file( 'DATA/gadm41_THA.gpkg', layer='ADM_ADM_1') 
        df = df[df['NAME_1'].isin ( prov ) ].copy()
        df['NAME_1'] = pd.Categorical(df['NAME_1'], categories=prov, ordered=True)
        df.sort_values(by='NAME_1',inplace=True)
        return df

    def getDEFAULT(self, SECTION ):
        if self.PROV in self.TOML[SECTION].keys():
            return self.TOML[SECTION][self.PROV]    
        else:
            return self.TOML[SECTION]['__DEFAULT__']
    
    def getVFILE(self):
        VFILE = list()
        for vfile in self.VULNER_FILES:
            VFILE.append( f'./CACHE/{self.PROV}/{vfile}' )
        return VFILE

    def getAbbrev(self):
        return self.dfProv[ self.dfProv.NAME_1==self.PROV].iloc[0].HASC_1[-2:]

###########################################################################################
if __name__=="__main__":
    ra = RiskAnalysis( 'Phuket' )
    import pdb ; pdb.set_trace()

