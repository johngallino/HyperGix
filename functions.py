import json
import zipfile
import os
from urllib.request import urlopen
from config import HYPERION_SCANS_PATH as DOWNLOAD_PATH
from osgeo import gdal
from qmanager import LAN_PATH

def tifCruncher(img, name, bands=[0]):
    ''' Takes a hyperspectral GeoTiff and returns a len(TARGET_BANDS) band compressed version '''
    ''' Defaults to converting all bands of GeoTiff, unless passed a list of select bands'''

    if type(bands) == list:
        if bands != [0]:
            print('bands is not [0]')
            bandCount = img.RasterCount
        else:
            bandCount = len(bands)
    else:
        raise TypeError(f'Bands passed to tiffCruncher function must be a list, not {type(bands)}')

    width = img.RasterXSize
    height = img.RasterYSize
    raster = img.ReadRaster(0,0, width, height)
    
    drv = gdal.GetDriverByName('GTiff')
    options = ['PHOTOMETRIC=MINISBLACK', 'PROFILE=GeoTIFF']
    # tiffed = drv.Create(os.path.join(LAN_PATH,'%s.tif' % name), width, height, bandCount, gdal.GDT_Int16, options=options)
    lan_file = os.path.join(DOWNLOAD_PATH,'%s.lan' % name[:-4])
    tiffed = gdal.Translate(lan_file, img, format='LAN', outputType=gdal.GDT_Int16)

    tiffed.SetGeoTransform( [0.0, 1.0, 0.0, 0.0, 0.0, 1.0] )
    for i in range(1, bandCount+1):
        tiffed.GetRasterBand(i).WriteArray(img.GetRasterBand(bandCount[i-1]).ReadAsArray().reshape(height, width))
        if i == 1:
            tiffed.GetRasterBand(i).SetColorInterpretation(gdal.GCI_BlueBand)
        elif i== 4:
            tiffed.GetRasterBand(i).SetColorInterpretation(gdal.GCI_GreenBand)
        elif i==5:
            tiffed.GetRasterBand(i).SetColorInterpretation(gdal.GCI_RedBand)

    tiffed.FlushCache()
    return tiffed


def unzipIt(zip_file):
    dirname = os.getcwd()
    zippath = os.path.join(dirname, 'downloads')
    print(f'Unzipping to {zippath}')
    try:
        with zipfile.ZipFile(zip_file) as z:
            z.extractall(zippath)
            z.close()
            print("Extracted all contents of downloaded file")
        os.remove(zip_file)
    except Exception as e:
        print(e)

    


