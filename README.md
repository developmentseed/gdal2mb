### Requirements

* GDAL
 * OSX: [GDAL Complete](http://www.kyngchaos.com/software/frameworks) from kyngchaos
 * Other systems: [GDAL binaries](http://trac.osgeo.org/gdal/wiki/DownloadingGdalBinaries)
* [Python](http://www.python.org/) (included on OSX and Linux)

### Usage

If GeoTIFFs are in projections other than `EPSG:900913` (as many are), run gdalwarp first:

    gdalwarp -t_srs EPSG:900913 raster.tiff raster_merc.tiff

Run `python gdal2tiles.py -h` for usage instructions.

### Description

This is a variation of the [gdal2tiles](http://www.klokan.cz/projects/gdal2tiles/) script that supports MapBox `mbtiles` SQLite tilesets as an output option. It has the same requirements as the original script - notably an installation of [GDAL](http://www.gdal.org/).

Usage of this command is

    python gdal2tiles.py raster_merc.tiff raster_merc.mbtiles

The resultant `.mbtiles` file can be used in Maps on a Stick and elsewhere.
