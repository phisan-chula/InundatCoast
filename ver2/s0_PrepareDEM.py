#
#
#
import os,sys
import argparse
from RiskAnalysis import *

###################################################################
if __name__=="__main__":
    parser = argparse.ArgumentParser(
                    prog=sys.argv[0], description='What the program does',
                    epilog='To WIN: cp -r CACHE/  /mnt/c/Users/User/Downloads/')
    parser.add_argument('-f', '--force', action='store_true', help='force download NASADEM and unzip' )
    parser.add_argument('-v', '--vrt', action='store_true', help='build gdal/vrt file "AllDEM.vrt"' )
    args = parser.parse_args()
    print(args)

    risk = RiskAnalysis()

    for i,row in risk.dfGrid.iterrows():
        print('Preparing downloading ...')
        CMD = f'wget --load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies '\
                f' --keep-session-cookies -P "./DEM" {row.URL}'
        print( CMD )
        if args.force: os.system( CMD )
        #import pdb; pdb.set_trace()

    if args.force: 
        CMD = '''cd "./DEM" ; for z in *.zip; do unzip "$z"; done '''
        print( CMD ); os.system( CMD  )

    if args.force or args.vrt:
        with open( './DEM/dem_list.txt','w') as fd:
            fd.write("\n".join(  risk.dfGrid.DEM_HGT.to_list() ) )
        CMD = r'''/usr/bin/gdalbuildvrt -input_file_list ./DEM/dem_list.txt ./DEM/AllDEM.vrt'''
        print( CMD )
        os.system( CMD )
 
    os.system( 'echo "\n----dem_list.txt-----\n"; cat ./DEM/dem_list.txt' )
    os.system( 'echo "\n\n------in directory------\n"; find ./DEM/' )
    print( f'************* end of {sys.argv[0]} ******************')


