#!/home/phisan/miniconda3/envs/gee/bin/python3
#
#
#
import sys,os
import numpy as np
import argparse
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point,MultiPoint
import matplotlib.pyplot as plt
from pathlib import Path
from RiskAnalysis import *



def PlotPDF():
    fig, ax = plt.subplots(figsize=(8, 6))
    gdfPopu.plot(ax=ax, color='red', alpha=0.5, lw=0.7)
    gdfRegion.plot(ax=ax, fc='none', ec='black', alpha=0.7, linewidth=1)
    for i,row in gdfPopu.iterrows():
        x,y = row.geometry.centroid.x, row.geometry.centroid.y 
        ax.text( x,y, f'{i}|',         color='blue', ha='right', va='center', fontsize=8 )  
        ax.text( x,y, f'{row.SumPopu_}',color='red',  ha='left',  va='center', fontsize=8 )  
    #import pdb; pdb.set_trace()
    plt.title( f'Province: {args.PROV}')
    #COLS = list(gdfPopu.columns)[:-1] ;TAB = gdfPopu[ COLS ]
    #Krabiax.table(cellText=TAB.values, colLabels=TAB.columns, loc='center')
    #plt.show()
    PDF = Path( VFILE[-1] ).parent.joinpath( Path( VFILE[-1] ).stem + '.pdf' )
    print( f'Plotting {PDF} ...' )
    plt.savefig( PDF )


##################################################################
if __name__=="__main__":
    parser = argparse.ArgumentParser( prog=sys.argv[0],
                    description='What the program does' )
    parser.add_argument( 'PROV', help='specified province name' )
    args = parser.parse_args()

    risk = RiskAnalysis( args.PROV )
    #print( risk.TOML )
    VFILE = risk.getVFILE() ; AB=risk.getAbbrev()
    print( f'*********** {args.PROV} ************' )
    gdfRegion = gpd.read_file( VFILE[0] )
    gdfPopu = gpd.read_file( VFILE[-1], layer=f'{AB}:ClustPopu' )
    gdfDEM = gpd.read_file( VFILE[-1], layer=f'{AB}:ClustDEM' )
    [[ DEM_EPS_m, DEM_MIN_pnt],[POPU_EPS_m, POPU_MIN_pnt]] = risk.getDEFAULT('DBSCAN')
    ##############################################################

    #gdfPopu = gdfPopu[ gdfPopu.SumPopu>500 ].copy() 

    gdfPopu.sort_values( by=['SumPopu'], axis=0, ascending=False, inplace=True, ignore_index=True )
    #print( gdfPopu )
    HDR = f'| {"No.":^4s} | {"Population":^10s} | {"Area.SqKM":^10s} | {"Dens.@sqkm":,^10s} |'
    print(len(HDR)*'-') ; print( HDR ) ; print(len(HDR)*'-')
    for i,row in gdfPopu.iterrows():
        #import pdb; pdb.set_trace()
        sqkm = row.geometry.area*111*111
        dens = row.SumPopu/sqkm
        print( f'| {i:>4d} | {row.SumPopu:>10,d} | {sqkm:10.2f} | {dens:10,.0f} |' )
    PlotPDF()

