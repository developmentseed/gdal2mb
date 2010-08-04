#!/usr/bin/env python
#
# MapBox tile generator written by 
# Tom MacWright <macwright [-at-] gmail.com>, based on 
# gdal2tiles.py, whose license and author are noted below
#
###############################################################################
# Project:  Google Summer of Code 2007
# Purpose:  Convert a raster into TMS tiles, create KML SuperOverlay EPSG:4326,
#           generate a simple HTML viewers based on Google Maps and OpenLayers
# Author:   Klokan Petr Pridal, klokan at klokan dot cz
# Web:      http://www.klokan.cz/projects/gdal2tiles/
###############################################################################
# Copyright (c) 2007, Klokan Petr Pridal
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
# 
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
###############################################################################

from osgeo import gdal 
import sys, os
from osgeo.gdalconst import GA_ReadOnly
from osgeo.osr import SpatialReference
from math import ceil, log10
from optparse import OptionParser
import operator
import sqlite3

verbose = False

tilesize = 256
tileformat = 'jpeg'

tempdriver = gdal.GetDriverByName('MEM')
tiledriver = gdal.GetDriverByName(tileformat)

# =============================================================================
def writetile( filename, data, dxsize, dysize, bands):
    """
    Write raster 'data' (of the size 'dataxsize' x 'dataysize') read from
    'dataset' into the tile 'filename' with size 'tilesize' pixels.
    Later this should be replaced by new <TMS Tile Raster Driver> from GDAL.
    """

    # Create needed directories for output
    dirs, file = os.path.split(filename)
    if not os.path.isdir(dirs):
        os.makedirs(dirs)

    # GRR, PNG DRIVER DOESN'T HAVE CREATE() !!!
    # so we have to create temporary file in memmory...

    #TODO: Add transparency to files with one band only too (grayscale).
    if bands == 3 and tileformat == 'png':
        tmp = tempdriver.Create('', tilesize, tilesize, bands=4)
        alpha = tmp.GetRasterBand(4)
        alphaarray = (zeros((dysize, dxsize)) + 255).astype('b')
        alpha.WriteArray(alphaarray, 0, tilesize-dysize )
    else:
        tmp = tempdriver.Create('', tilesize, tilesize, bands=bands)

    # (write data from the bottom left corner)
    tmp.WriteRaster(0, tilesize-dysize, dxsize, dysize, data, band_list=range(1, bands+1))
 
    # ... and then copy it into the final tile with given filename
    tiledriver.CreateCopy(filename, tmp, strict=0)

    return 0

# =============================================================================
def writemb(index, data, dxsize, dysize, bands, mb_db):
    """
    Write raster 'data' (of the size 'dataxsize' x 'dataysize') read from
    'dataset' into the mbtiles document 'mb_db' with size 'tilesize' pixels.
    Later this should be replaced by new <TMS Tile Raster Driver> from GDAL.
    """

    # GRR, PNG DRIVER DOESN'T HAVE CREATE() !!!
    # so we have to create temporary file in memmory...

    #TODO: Add transparency to files with one band only too (grayscale).
    if bands == 3 and tileformat == 'png':
        tmp = tempdriver.Create('', tilesize, tilesize, bands=4)
        alpha = tmp.GetRasterBand(4)
        #from Numeric import zeros
        alphaarray = (zeros((dysize, dxsize)) + 255).astype('b')
        alpha.WriteArray( alphaarray, 0, tilesize-dysize )
    else:
        tmp = tempdriver.Create('', tilesize, tilesize, bands=bands)

    # (write data from the bottom left corner)
    tmp.WriteRaster( 0, tilesize-dysize, dxsize, dysize, data, band_list=range(1, bands+1))
 
    # ... and then copy it into the final tile with given filename
    tiledriver.CreateCopy('tmp.png', tmp, strict=0)

    # print raw_data
    query = """insert into tiles (zoom_level, tile_column, tile_row, tile_data) values (%d, %d, %d, ?)""" % (index[0], index[1], index[2])
    cur = mb_db.cursor()
    d = open('tmp.png', 'rb').read()
    cur.execute(query, (sqlite3.Binary(d),))
    mb_db.commit()
    cur.close()
    return 0

if __name__ == '__main__':


    parser = OptionParser("%prog usage: %prog [input_file] [output_file]")
    parser.add_option('-t', '--title', dest='title', help='Tileset title')
    parser.add_option('-o', '--overlay', 
        dest='overlay', default=False, help='Overlay')

    (options, args) = parser.parse_args()

    try:
        input_file = args[0]
        output_file = args[1]
    except IndexError, e:
        raise Exception('Input and Output file arguments are required')

    profile = 'local' # later there should be support for TMS global profiles
    title = ''

    input_file = ''
    output_dir = ''

    isepsg4326 = False

    gdal.AllRegister()

    # Set correct default values.
    if not title:
        title = os.path.basename( input_file )
    if not output_dir:
        output_dir = os.path.splitext(os.path.basename( input_file ))[0]
    mb_output = os.path.splitext(output_dir)[1] == '.mbtiles'

    # Open input_file and get all necessary information.
    dataset = gdal.Open( input_file, GA_ReadOnly )
    if dataset is None:
        Usage()
        sys.exit( 1 )
        
    bands = dataset.RasterCount
    if bands == 3 and tileformat == 'png':
        from Numeric import zeros
    xsize = dataset.RasterXSize
    ysize = dataset.RasterYSize

    geotransform = dataset.GetGeoTransform()

    projection = dataset.GetProjection()

    north = geotransform[3]
    south = geotransform[3] + geotransform[5] * ysize
    east  = geotransform[0] + geotransform[1] * xsize
    west  = geotransform[0]

    if verbose:
        print "Input (%s):" % input_file
        print "="*80
        print "  Driver:", dataset.GetDriver().ShortName,'/', dataset.GetDriver().LongName
        print "  Size:", xsize, 'x', ysize, 'x', bands
        print "  Projection:", projection
        print "  NSEW: ", (north, south, east, west) 

    if projection:
        # CHECK: Is there better way how to test that given file is in EPSG:4326?
        #spatialreference = SpatialReference(wkt=projection)
        #if spatialreference.???() == 4326:
        if projection.endswith('AUTHORITY["EPSG","4326"]]'):
            isepsg4326 = True
            if verbose:
                print "Projection detected as EPSG:4326"

    # Python 2.2 compatibility.
    log2 = lambda x: log10(x) / log10(2) # log2 (base 2 logarithm)
    sum = lambda seq, start=0: reduce(operator.add, seq, start)

    # Zoom levels of the pyramid.
    maxzoom = int(max(ceil(log2(xsize/float(tilesize))), ceil(log2(ysize/float(tilesize)))))
    zoompixels = [geotransform[1] * 2.0**(maxzoom-zoom) for zoom in range(0, maxzoom+1)]
    tilecount = sum([
        int(ceil(xsize / (2.0**(maxzoom-zoom)*tilesize))) * \
        int(ceil(ysize / (2.0**(maxzoom-zoom)*tilesize))) \
        for zoom in range(maxzoom+1)
    ])

    if verbose:
        print "Output (%s):" % output_dir
        print "="*80
        print "  Format of tiles:", tiledriver.ShortName, '/', tiledriver.LongName
        print "  Size of a tile:", tilesize, 'x', tilesize, 'pixels'
        print "  Count of tiles:", tilecount
        print "  Zoom levels of the pyramid:", maxzoom
        print "  Pixel resolution by zoomlevels:", zoompixels

    tileno = 0
    progress = 0

    if mb_output:
        mb_db_filename = output_dir
        print "Connecting to database %s" % mb_db_filename

        mb_db = sqlite3.connect(mb_db_filename)
        mb_db.execute("""
        CREATE TABLE tiles (
          zoom_level integer, 
          tile_column integer, 
          tile_row integer, 
          tile_data blob);
        """)       
        mb_db.commit()

    for zoom in range(maxzoom, -1, -1):

        # Maximal size of read window in pixels.
        rmaxsize = 2.0**(maxzoom-zoom)*tilesize

        if verbose:
            print "-"*80
            print "Zoom %s - pixel %.20f" % (zoom, zoompixels[zoom]), int(2.0**zoom*tilesize)
            print "-"*80

        for ix in range(0, int( ceil( xsize / rmaxsize))):

            # Read window xsize in pixels.
            if ix+1 == int( ceil( xsize / rmaxsize)) and xsize % rmaxsize != 0:
                rxsize = int(xsize % rmaxsize)
            else:
                rxsize = int(rmaxsize)
            
            # Read window left coordinate in pixels.
            rx = int(ix * rmaxsize)

            for iy in range(0, int(ceil( ysize / rmaxsize))):

                # Read window ysize in pixels.
                if iy+1 == int(ceil( ysize / rmaxsize)) and ysize % rmaxsize != 0:
                    rysize = int(ysize % rmaxsize)
                else:
                    rysize = int(rmaxsize)

                # Read window top coordinate in pixels.
                ry = int(ysize - (iy * rmaxsize)) - rysize

                dxsize = int(rxsize/rmaxsize * tilesize)
                dysize = int(rysize/rmaxsize * tilesize)
                filename = os.path.join(output_dir, '%d/%d/%d.png' % (zoom, ix, iy))

                if verbose:
                    # Print info about tile and read area.
                    print "%d/%d" % (tileno+1,tilecount), filename, [ix, iy], [rx, ry], [rxsize, rysize], [dxsize, dysize]
                else:
                    # Show the progress bar.
                    percent = int(ceil((tileno) / float(tilecount-1) * 100))
                    while progress <= percent:
                        if progress % 10 == 0:
                            sys.stdout.write( "%d" % progress )
                            sys.stdout.flush()
                        else:
                            sys.stdout.write( '.' )
                            sys.stdout.flush()
                        progress += 2.5
               
                # Load raster from read window.
                data = dataset.ReadRaster(rx, ry, rxsize, rysize, dxsize, dysize)
                writemb((zoom, ix, iy), data, dxsize, dysize, bands, mb_db)
                tileno += 1

    mb_db.close()
    # Last \n for the progress bar
    print "\nDone"
