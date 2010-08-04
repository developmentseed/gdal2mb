### Requirements

* [GDAL Complete](http://www.kyngchaos.com/software/frameworks) from kyngchaos
* [Python](http://www.python.org/) from anywhere

### Usage

Run `python gdal2tiles.py -h` for usage instructions.

### Description

This is a variation of the [gdal2tiles](http://www.klokan.cz/projects/gdal2tiles/) script that supports MapBox `mbtiles` SQLite tilesets as an output option. It has the same requirements as the original script - notably an installation of [GDAL](http://www.gdal.org/).

Note that MapBox supports the `EPSG:900913`, or Google Mercator, projection, alone. Therefore, raster data in other projections must be reprojected with gdalwarp.

    gdalwarp -t_srs raster.tiff raster_merc.tiff

Usage of this command is

    python gdal2tiles.py raster_merc.tiff raster_merc.mbtiles

The resultant `.mbtiles` file can be used in Maps on a Stick and elsewhere.
