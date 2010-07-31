#!/usr/bin/env python
###############################################################################
# $Id$
#
# Project:  Google Summer of Code 2007
# Purpose:  Convert a raster into TMS tiles, create KML SuperOverlay EPSG:4326,
#           generate a simple HTML viewers based on Google Maps and OpenLayers
# Author:   Klokan Petr Pridal, klokan at klokan dot cz
# Web:      http://www.klokan.cz/projects/gdal2tiles/
#
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
#
# Uploaded as ticket #1763 of http://trac.osgeo.org/gdal/ 
# Patch #1815: Python 2.2 back-compatibility (needed for FWTools under Linux)
# Patch #1870: Google Earth KML Children Visibility + Square Pixel Condition
# OpenLayers 2.4 patch, note on #1763
#

from osgeo import gdal 
import sys, os, tempfile
from osgeo.gdalconst import GA_ReadOnly
from osgeo.osr import SpatialReference
from math import ceil, log10
import operator

import generate

verbose = False

tilesize = 256
tileformat = 'png'

tempdriver = gdal.GetDriverByName( 'MEM' )
tiledriver = gdal.GetDriverByName( tileformat )

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
        #from Numeric import zeros
        alphaarray = (zeros((dysize, dxsize)) + 255).astype('b')
        alpha.WriteArray( alphaarray, 0, tilesize-dysize )
    else:
        tmp = tempdriver.Create('', tilesize, tilesize, bands=bands)

    # (write data from the bottom left corner)
    tmp.WriteRaster( 0, tilesize-dysize, dxsize, dysize, data, band_list=range(1, bands+1))
 
    # ... and then copy it into the final tile with given filename
    tiledriver.CreateCopy(filename, tmp, strict=0)

    return 0





# =============================================================================
def Usage():
    print 'Usage: gdal2tiles.py [-title "Title"] [-publishurl http://yourserver/dir/]'
    print '                     [-nogooglemaps] [-noopenlayers] [-nokml]'
    print '                     [-googlemapskey KEY] [-forcekml] [-v]'
    print '                     input_file [output_dir]'
    print

# =============================================================================
#
# Program mainline.
#
# =============================================================================

if __name__ == '__main__':

    profile = 'local' # later there should be support for TMS global profiles
    title = ''
    publishurl = ''
    googlemapskey = 'INSERT_YOUR_KEY_HERE' # when not supplied as parameter
    nogooglemaps = False
    noopenlayers = False
    nokml = False
    forcekml = False

    input_file = ''
    output_dir = ''

    isepsg4326 = False
    generatekml = False

    gdal.AllRegister()
    argv = gdal.GeneralCmdLineProcessor( sys.argv )
    if argv is None:
        sys.exit( 0 )

    # Parse command line arguments.
    i = 1
    while i < len(argv):
        arg = argv[i]

        if arg == '-v':
            verbose = True

        elif arg == '-nogooglemaps':
            nogooglemaps = True

        elif arg == '-noopenlayers':
            noopenlayers = True

        elif arg == '-nokml':
            nokml = True

        elif arg == '-forcekml':
            forcekml = True

        elif arg == '-title':
            i += 1
            title = argv[i]

        elif arg == '-publishurl':
            i += 1
            publishurl = argv[i]

        elif arg == '-googlemapskey':
            i += 1
            googlemapskey = argv[i]

        elif arg[:1] == '-':
            print >>sys.stderr, 'Unrecognised command option: ', arg
            Usage()
            sys.exit( 1 )

        elif not input_file:
            input_file = argv[i]

        elif not output_dir:
            output_dir = argv[i]

        else:
            print >>sys.stderr, 'Too many parameters already: ', arg
            Usage()
            sys.exit( 1 )
            
        i = i + 1

    if not input_file:
        print >>sys.stderr, 'No input_file was given.'
        Usage()
        sys.exit( 1 )

    # Set correct default values.
    if not title:
        title = os.path.basename( input_file )
    if not output_dir:
        output_dir = os.path.splitext(os.path.basename( input_file ))[0]
    if publishurl and not publishurl.endswith('/'):
        publishurl += '/'
    if publishurl:
        publishurl += os.path.basename(output_dir) + '/'

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
    south = geotransform[3]+geotransform[5]*ysize
    east = geotransform[0]+geotransform[1]*xsize
    west = geotransform[0]

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

    if (isepsg4326 or forcekml) and (north, south, east, west) != (0, xsize, ysize, 0):
        generatekml = True
    if verbose:
        if generatekml:
            print "Generating of KML is possible"
        else:
            print "It is not possible to generate KML (projection is not EPSG:4326 or there are no coordinates)!"

    if forcekml and (north, south, east, west) == (0, xsize, ysize, 0):
        print >> sys.stderr, "Geographic coordinates not available for given file '%s'" % input_file
        print >> sys.stderr, "so KML file can not be generated."
        sys.exit( 1 )


    # Python 2.2 compatibility.
    log2 = lambda x: log10(x) / log10(2) # log2 (base 2 logarithm)
    sum = lambda seq, start=0: reduce( operator.add, seq, start)

    # Zoom levels of the pyramid.
    maxzoom = int(max( ceil(log2(xsize/float(tilesize))), ceil(log2(ysize/float(tilesize)))))
    zoompixels = [geotransform[1] * 2.0**(maxzoom-zoom) for zoom in range(0, maxzoom+1)]
    tilecount = sum( [
        int( ceil( xsize / (2.0**(maxzoom-zoom)*tilesize))) * \
        int( ceil( ysize / (2.0**(maxzoom-zoom)*tilesize))) \
        for zoom in range(maxzoom+1)
    ] )

    # Create output directory, if it doesn't exist
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    if verbose:
        print "Output (%s):" % output_dir
        print "="*80
        print "  Format of tiles:", tiledriver.ShortName, '/', tiledriver.LongName
        print "  Size of a tile:", tilesize, 'x', tilesize, 'pixels'
        print "  Count of tiles:", tilecount
        print "  Zoom levels of the pyramid:", maxzoom
        print "  Pixel resolution by zoomlevels:", zoompixels

    # Generate tilemapresource.xml.
    f = open(os.path.join(output_dir, 'tilemapresource.xml'), 'w')
    f.write( generate.generate_tilemapresource( 
        title = title,
        north = north,
        south = south,
        east = east,
        west = west,
        isepsg4326 = isepsg4326,
        projection = projection,
        publishurl = publishurl,
        zoompixels = zoompixels,
        tilesize = tilesize,
        tileformat = tileformat,
        profile = profile
    ))
    f.close()

    # Generate googlemaps.html
    if not nogooglemaps:
        f = open(os.path.join(output_dir, 'googlemaps.html'), 'w')
        f.write( generate.generate_googlemaps(
          title = title,
          googlemapskey = googlemapskey,
          xsize = xsize,
          ysize = ysize,
          maxzoom = maxzoom,
          tilesize = tilesize
        ))
        f.close()

    # Generate openlayers.html
    if not noopenlayers:
        f = open(os.path.join(output_dir, 'openlayers.html'), 'w')
        f.write( generate.generate_openlayers(
          title = title,
          xsize = xsize,
          ysize = ysize,
          maxzoom = maxzoom,
          tileformat = tileformat
        ))
        f.close()
        
    # Generate Root KML
    if generatekml:
        f = open(os.path.join(output_dir, 'doc.kml'), 'w')
        f.write( generate.generate_rootkml(
            title = title,
            north = north,
            south = south,
            east = east,
            west = west,
            tilesize = tilesize,
            tileformat = tileformat,
            publishurl = ""
        ))
        f.close()
        
    # Generate Root KML with publishurl
    if generatekml and publishurl:
        f = open(os.path.join(output_dir, os.path.basename(output_dir)+'.kml'), 'w')
        f.write( generate.generate_rootkml(
            title = title,
            north = north,
            south = south,
            east = east,
            west = west,
            tilesize = tilesize,
            tileformat = tileformat,
            publishurl = publishurl
        ))
        f.close()

    #
    # Main cycle for TILE and KML generating.
    #
    tileno = 0
    progress = 0
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

            for iy in range(0, int( ceil( ysize / rmaxsize))):

                # Read window ysize in pixels.
                if iy+1 == int( ceil( ysize / rmaxsize)) and ysize % rmaxsize != 0:
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
                # Write that raster to the tile.
                writetile( filename, data, dxsize, dysize, bands)
               
                # Create a KML file for this tile.
                if generatekml:
                    f = open( os.path.join(output_dir, '%d/%d/%d.kml' % (zoom, ix, iy)), 'w')
                    f.write( generate.generate_kml(
                        zoom = zoom,
                        ix = ix,
                        iy = iy,
                        rpixel = zoompixels[zoom],
                        tilesize = tilesize,
                        tileformat = tileformat,
                        south = south,
                        west = west,
                        xsize = xsize,
                        ysize = ysize,
                        maxzoom = maxzoom
                    ))
                    f.close()

                tileno += 1

    # Last \n for the progress bar
    print "\nDone"
