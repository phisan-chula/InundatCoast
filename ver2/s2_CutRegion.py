#!/home/phisan/miniconda3/envs/gee/bin/python3
#
#
#
import sys,os
import argparse
from shapely import Point, MultiPoint
from RiskAnalysis import *


DEM =  r'/mnt/d/GeoData/FABDEM_TH/FABDEM_Thailand.vrt'  # nodata -9999
POPU = r'/mnt/d/GeoData/WorldPop/2020/THA/tha_ppp_2020.tif'
 
# NSO Populatoin Registration 2565
OfficialThaiPopu =  {       #popu , area_sqkm
      'Phuket': (  417_891 , 547 ), 
      'Ranong': (  194_226 ,3_230), 
      'Phangnga' : ( 267_442 , 4_170 ), 
      'Krabi' :   (  480_057,5_323 ), 
      'Trang' :  ( 663_820 ,4_726 ),
      'Satun' :   ( 325_303 ,3_019 )
    }

def TABLE( HDR, LINEs ):
    print( len(HDR)*'-' ) ; print( HDR ) ; print( len(HDR)*'-' )
    for line in LINEs:
        print(line)
    print( len(HDR)*'-' ) ; print( '\n')

def DoCompare():
    risk = RiskAnalysis( None )
    AREAs=list() ; DEMs = list() ; POPUs = list()
    PROVs = risk.TOML['REGION_PROV'].split('|')
    #for PROV in PROVs[-2:-1]:
    for PROV in PROVs:
        print( f'Processing {PROV}...')
        risk = RiskAnalysis( PROV )
        VFILE = risk.getVFILE() 
        popu, area = OfficialThaiPopu[ PROV ]
        area_ = int(risk.dfProv[risk.dfProv.NAME_1==PROV].iloc[0].geometry.area*(111*111))
        gdfPopu = GeoTIFF2df( VFILE[1],  NAME="Popu", IN_RANGE=[0,99999] )
        gdfDEM = GeoTIFF2df( VFILE[2],  NAME="DEM", IN_RANGE=[0,99999] ) 
        popu_ = int( gdfPopu.Popu.sum())

        area_perc = '{:4.1f}%'.format((area_-area)/area*100 )
        AREAs.append( f'|{PROV:<10s} | {area:15,d} | {area_:15,d} | {area-area_:10,d} | {area_perc:10} |' ) 
        #import pdb; pdb.set_trace()
        POPUs.append( f'|{PROV:<10s} | {popu:10,d} | {popu_:10,d} | {popu-popu_:10,d} | {gdfPopu.Popu.min():12.1f} | {gdfPopu.Popu.max():12.1f} |' ) 
        DEMs.append( f'|{PROV:<10s} | {gdfDEM.DEM.min():10.1f} | {gdfDEM.DEM.max():10.1f} | {gdfDEM.DEM.std():10.1f} |' ) 
    TABLE( f'|{"Province":^10s} | {"Official Area":^15s} | {"Model Area":^15s} | {"Diff sq.km":^10s} | {"Diff":^10s} |', AREAs )
    TABLE( f'|{"Province":^10s} | {"Offic.Popu":^10s} | {"Model.Popu":^10s} | {"Popu.Diff":^10s} | {"Min.Dens":^12s} | {"Max.Dens":^12s} |', POPUs )
    TABLE( f'|{"Province":^10s} | {"DEM-min":^10s} | {"DEM-max":^10s} | {"DEM-std":^10s} |' , DEMs )

##################################################################
if __name__=="__main__":
    print( f'*** DEM : {DEM} ***')
    parser = argparse.ArgumentParser( prog=sys.argv[0],
                    description='read DEM and cut by region of Thai province' )
    parser.add_argument( '-p', '--province', type=str, help='specified the province name to cut operation' )
    parser.add_argument( '-c', '--compare', action='store_true', 
            help='Compare population and area, after cut regions!!!' )
    #import pdb ; pdb.set_trace()
    args = parser.parse_args()
    print( args )

    if args.compare:
        DoCompare()  # and exit ...
        sys.exit()
    elif args.province:
        risk = RiskAnalysis( args.province )
        VFILE = risk.getVFILE() 
        print( f'**************** Processing {args.province} ****************')
        print( risk.TOML)
        gdf = risk.dfProv[ risk.dfProv.NAME_1==args.province ]
        gdf.to_file( VFILE[0] , layer='Region', driver='GPKG')

        CMD1 = f'gdalwarp -overwrite -cutline {VFILE[0]} -cl Region -multi -crop_to_cutline'\
                f' -co COMPRESS=DEFLATE -ot Float32 -srcnodata -99999 -dstnodata -32768 '\
                f' {POPU} {VFILE[1]}'
        print( CMD1 ) ; os.system( CMD1 )

        CMD2  = f'gdalwarp -overwrite -cutline {VFILE[0]} -cl Region -multi -crop_to_cutline '\
                f' -co COMPRESS=DEFLATE -ot Int16 -srcnodata -9999 -dstnodata -32768 '\
                f' {DEM} {VFILE[2]}'
        print( CMD2 ) ; os.system( CMD2 )

        CMD3 = f'''find CACHE/{args.province} -maxdepth 1 -exec ls -ld {{}} \\; '''
        print( CMD3 ) ; os.system( CMD3 )
    else:
        parser.print_help()

    print( f'************* end of {sys.argv[0]} ******************')
