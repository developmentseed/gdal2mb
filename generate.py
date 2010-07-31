# =============================================================================
def generate_openlayers( **args ):
    """
    Template for openlayers.html. Returns filled string. Expected variables:
        title, xsize, ysize, maxzoom, tileformat
    """

    args['maxresolution'] = 2**(args['maxzoom'])
    args['zoom'] = min( 3, args['maxzoom'])
    args['maxzoom'] += 1

    s = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml"> 
  <head>
    <title>%(title)s</title>
    <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
    <meta http-equiv='imagetoolbar' content='no'/>
    <style type="text/css"> v\:* {behavior:url(#default#VML);}
        html, body { overflow: hidden; padding: 0; height: 100%%; width: 100%%; font-family: 'Lucida Grande',Geneva,Arial,Verdana,sans-serif; }
        body { margin: 10px; background: #fff; }
        h1 { margin: 0; padding: 6px; border:0; font-size: 20pt; }
        #header { height: 43px; padding: 0; background-color: #eee; border: 1px solid #888; }
        #subheader { height: 12px; text-align: right; font-size: 10px; color: #555;}
        #map { height: 100%%; border: 1px solid #888; background-color: #fff; }
    </style>
    <script src="http://www.openlayers.org/api/2.4/OpenLayers.js" type="text/javascript"></script>
    <script type="text/javascript">
    //<![CDATA[
    var map, layer;

    function load(){
        // I realized sometimes OpenLayers has some troubles with Opera and Safari.. :-( Advices or patch are welcome...
        // Correct TMS Driver should read TileMapResource by OpenLayers.loadURL and parseXMLStringOpenLayers.parseXMLString
        // For correct projection the patch for OpenLayers TMS is needed, index to tiles (both x an y) has to be rounded into integers
        /* Then definition is like this:
        var options = {
            controls: [],
            // maxExtent: new OpenLayers.Bounds(13.7169981668, 49.608691789, 13.9325582389, 49.7489724456),
            maxExtent: new OpenLayers.Bounds(13.71699816677651995178, 49.46841113248020604942, 13.93255823887490052471, 49.60869178902321863234),
            maxResolution: 0.00150183372679037197,
            numZoomLevels: 6,
            units: 'degrees',
            projection: "EPSG:4326"
        };
        map = new OpenLayers.Map("map", options);
        */

        /* Just pixel based view now */
        var options = {
            controls: [],
            maxExtent: new OpenLayers.Bounds(0, 0, %(xsize)d, %(ysize)d),
            maxResolution: %(maxresolution)d,
            numZoomLevels: %(maxzoom)d,
            units: 'pixels',
            projection: ""
        };
        map = new OpenLayers.Map("map", options);

        // map.addControl(new OpenLayers.Control.MousePosition());
        map.addControl(new OpenLayers.Control.PanZoomBar());
        map.addControl(new OpenLayers.Control.MouseDefaults());
        map.addControl(new OpenLayers.Control.KeyboardDefaults());

        // Patch for OpenLayers TMS is needed because string "1.0.0" is hardcoded in url no,
        // there has to be optional parameter with version (default this "1.0.0")
        // Hack to support local tiles by stable OpenLayers branch without a patch
        OpenLayers.Layer.TMS.prototype.getURL = function ( bounds ) {
            bounds = this.adjustBoundsByGutter(bounds);
            var res = this.map.getResolution();
            var x = Math.round((bounds.left - this.tileOrigin.lon) / (res * this.tileSize.w));
            var y = Math.round((bounds.bottom - this.tileOrigin.lat) / (res * this.tileSize.h));
            var z = this.map.getZoom();
            var path = z + "/" + x + "/" + y + "." + this.type;
            var url = this.url;
            if (url instanceof Array) {
                url = this.selectUrl(path, url);
            }
            return url + path;
        };
        layer = new OpenLayers.Layer.TMS( "TMS", 
                "", {layername: 'map', type:'%(tileformat)s'} );
        map.addLayer(layer);
        map.zoomTo(%(zoom)d);

        resize();
    }

    function getWindowHeight() {
        if (self.innerHeight) return self.innerHeight;
        if (document.documentElement && document.documentElement.clientHeight)
            return document.documentElement.clientHeight;
        if (document.body) return document.body.clientHeight;
	        return 0;
    }

    function getWindowWidth() {
	    if (self.innerWidth) return self.innerWidth;
	    if (document.documentElement && document.documentElement.clientWidth)
	        return document.documentElement.clientWidth;
	    if (document.body) return document.body.clientWidth;
	        return 0;
    }
    
    function resize() {  
	    var map = document.getElementById("map");  
	    var header = document.getElementById("header");  
	    var subheader = document.getElementById("subheader");  
	    map.style.height = (getWindowHeight()-80) + "px";
	    map.style.width = (getWindowWidth()-20) + "px";
	    header.style.width = (getWindowWidth()-20) + "px";
	    subheader.style.width = (getWindowWidth()-20) + "px";
    } 

    onresize=function(){ resize(); };

    //]]>
    </script>
  </head>
  <body onload="load()">
      <div id="header"><h1>%(title)s</h1></div>
      <div id="subheader">Generated by <a href="http://www.klokan.cz/projects/gdal2tiles/">GDAL2Tiles</a>, Copyright (C) 2007 <a href="http://www.klokan.cz/">Klokan Petr Pridal</a>,  <a href="http://www.gdal.org/">GDAL</a> &amp; <a href="http://www.osgeo.org/">OSGeo</a> <a href="http://code.google.com/soc/">SoC 2007</a>
      </div>
       <div id="map"></div>
  </body>
</html>
""" % args

    return s

# =============================================================================
def generate_tilemapresource( **args ):
    """
    Template for tilemapresource.xml. Returns filled string. Expected variables:
      title, north, south, east, west, isepsg4326, projection, publishurl,
      zoompixels, tilesize, tileformat, profile
    """

    if args['isepsg4326']:
        args['srs'] = "EPSG:4326"
    else:
        args['srs'] = args['projection']

    zoompixels = args['zoompixels']

    s = """<?xml version="1.0" encoding="utf-8"?>
<TileMap version="1.0.0" tilemapservice="http://tms.osgeo.org/1.0.0">
  <Title>%(title)s</Title>
  <Abstract></Abstract>
  <SRS>%(srs)s</SRS>
  <BoundingBox minx="%(south).20f" miny="%(west).20f" maxx="%(north).20f" maxy="%(east).20f"/>
  <Origin x="%(south).20f" y="%(west).20f"/>
  <TileFormat width="%(tilesize)d" height="%(tilesize)d" mime-type="image/%(tileformat)s" extension="%(tileformat)s"/>
  <TileSets profile="%(profile)s">
""" % args
    for z in range(len(zoompixels)):
        s += """    <TileSet href="%s%d" units-per-pixel="%.20f" order="%d"/>\n""" % (args['publishurl'], z, zoompixels[z], z)
    s += """  </TileSets>
</TileMap>
"""
    return s



# =============================================================================
def generate_rootkml( **args ):
    """
    Template for the root doc.kml. Returns filled string. Expected variables:
      title, north, south, east, west, tilesize, tileformat, publishurl
    """
    
    args['minlodpixels'] = args['tilesize'] / 2

    s = """<?xml version="1.0" encoding="utf-8"?>
<kml xmlns="http://earth.google.com/kml/2.1">
  <Document>
    <name>%(title)s</name>
    <description></description>
    <Style> 
      <ListStyle id="hideChildren"> 
        <listItemType>checkHideChildren</listItemType> 
      </ListStyle> 
    </Style> 
    <Region>
      <LatLonAltBox>
        <north>%(north).20f</north>
        <south>%(south).20f</south>
        <east>%(east).20f</east>
        <west>%(west).20f</west>
      </LatLonAltBox>
    </Region>
    <NetworkLink>
      <open>1</open>
      <Region>
        <Lod>
          <minLodPixels>%(minlodpixels)d</minLodPixels>
          <maxLodPixels>-1</maxLodPixels>
        </Lod>
        <LatLonAltBox>
          <north>%(north).20f</north>
          <south>%(south).20f</south>
          <east>%(east).20f</east>
          <west>%(west).20f</west>
        </LatLonAltBox>
      </Region>
      <Link>
        <href>%(publishurl)s0/0/0.kml</href>
        <viewRefreshMode>onRegion</viewRefreshMode>
      </Link>
    </NetworkLink>
  </Document>
</kml>
""" % args
    return s

# =============================================================================
def generate_kml( **args ):
    """
    Template for the tile kml. Returns filled string. Expected variables:
      zoom, ix, iy, rpixel, tilesize, tileformat, south, west, xsize, ysize,
      maxzoom
    """

    zoom, ix, iy, rpixel = args['zoom'], args['ix'], args['iy'], args['rpixel']
    maxzoom, tilesize = args['maxzoom'], args['tilesize']
    south, west = args['south'], args['west']
    xsize, ysize = args['xsize'], args['ysize']

    nsew = lambda ix, iy, rpixel: (south + rpixel*((iy+1)*tilesize),
                                    south + rpixel*(iy*tilesize),
                                    west + rpixel*((ix+1)*tilesize),
                                    west + rpixel*ix*tilesize)

    args['minlodpixels'] = args['tilesize'] / 2
    args['tnorth'], args['tsouth'], args['teast'], args['twest'] = nsew(ix, iy, rpixel)

    if verbose:
        print "\tKML for area NSEW: %.20f %.20f %.20f %.20f" % nsew(ix, iy, rpixel)

    xchildern = []
    ychildern = []
    if zoom < maxzoom:
        zareasize = 2.0**(maxzoom-zoom-1)*tilesize
        xchildern.append(ix*2)
        if ix*2+1 < int( ceil( xsize / zareasize)):
            xchildern.append(ix*2+1)
        ychildern.append(iy*2)
        if iy*2+1 < int( ceil( ysize / zareasize)):
            ychildern.append(iy*2+1)

    s = """<?xml version="1.0" encoding="utf-8"?>
<kml xmlns="http://earth.google.com/kml/2.1">
  <Document>
    <name>%(zoom)d/%(ix)d/%(iy)d.kml</name>
    <Region>
      <Lod>
        <minLodPixels>%(minlodpixels)d</minLodPixels>
        <maxLodPixels>-1</maxLodPixels>
      </Lod>
      <LatLonAltBox>
        <north>%(tnorth).20f</north>
        <south>%(tsouth).20f</south>
        <east>%(teast).20f</east>
        <west>%(twest).20f</west>
      </LatLonAltBox>
    </Region>
    <GroundOverlay>
      <drawOrder>%(zoom)d</drawOrder>
      <Icon>
        <href>%(iy)d.%(tileformat)s</href>
      </Icon>
      <LatLonBox>
        <north>%(tnorth).20f</north>
        <south>%(tsouth).20f</south>
        <east>%(teast).20f</east>
        <west>%(twest).20f</west>
      </LatLonBox>
    </GroundOverlay>
""" % args

    for cx in xchildern:
        for cy in ychildern:

            if verbose:
                print "\t  ", [cx, cy], "NSEW: %.20f %.20f %.20f %.20f" % nsew(cx, cy, rpixel/2)

            cnorth, csouth, ceast, cwest = nsew(cx, cy, rpixel/2)
            s += """    <NetworkLink>
      <name>%d/%d/%d.png</name>
      <Region>
        <Lod>
          <minLodPixels>%d</minLodPixels>
          <maxLodPixels>-1</maxLodPixels>
        </Lod>
        <LatLonAltBox>
          <north>%.20f</north>
          <south>%.20f</south>
          <east>%.20f</east>
          <west>%.20f</west>
        </LatLonAltBox>
      </Region>
      <Link>
        <href>../../%d/%d/%d.kml</href>
        <viewRefreshMode>onRegion</viewRefreshMode>
        <viewFormat/>
      </Link>
    </NetworkLink>
""" % (zoom+1, cx, cy, args['minlodpixels'], cnorth, csouth, ceast, cwest, zoom+1, cx, cy)

    s += """  </Document>
</kml>
"""
    return s

# =============================================================================
def generate_googlemaps( **args ):
    """
    Template for googlemaps.html. Returns filled string. Expected variables:
      title, googlemapskey, xsize, ysize, maxzoom, tilesize, 
    """

    args['zoom'] = min( 3, args['maxzoom'])

    s = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml"> 
  <head>
    <title>%(title)s</title>
    <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
    <meta http-equiv='imagetoolbar' content='no'/>
    <style type="text/css"> v\:* {behavior:url(#default#VML);}
        html, body { overflow: hidden; padding: 0; height: 100%%; width: 100%%; font-family: 'Lucida Grande',Geneva,Arial,Verdana,sans-serif; }
        body { margin: 10px; background: #fff; }
        h1 { margin: 0; padding: 6px; border:0; font-size: 20pt; }
        #header { height: 43px; padding: 0; background-color: #eee; border: 1px solid #888; }
        #subheader { height: 12px; text-align: right; font-size: 10px; color: #555;}
        #map { height: 95%%; border: 1px solid #888; }
    </style>
    <script src='http://maps.google.com/maps?file=api&amp;v=2.x&amp;key=%(googlemapskey)s' type='text/javascript'></script>
    <script type="text/javascript">
    //<![CDATA[

    function getWindowHeight() {
	    if (self.innerHeight) return self.innerHeight;
	    if (document.documentElement && document.documentElement.clientHeight)
	        return document.documentElement.clientHeight;
	    if (document.body) return document.body.clientHeight;
	    return 0;
    }

    function getWindowWidth() {
	    if (self.innerWidth) return self.innerWidth;
    	if (document.documentElement && document.documentElement.clientWidth)
	        return document.documentElement.clientWidth;
	    if (document.body) return document.body.clientWidth;
	    return 0;
    }
    
    function resize() {  
	    var map = document.getElementById("map");  
	    var header = document.getElementById("header");  
	    var subheader = document.getElementById("subheader");  
	    map.style.height = (getWindowHeight()-80) + "px";
	    map.style.width = (getWindowWidth()-20) + "px";
	    header.style.width = (getWindowWidth()-20) + "px";
	    subheader.style.width = (getWindowWidth()-20) + "px";
	    // map.checkResize();
    } 


	// See http://www.google.com/apis/maps/documentation/reference.html#GProjection 
	// This code comes from FlatProjection.js, done by Smurf in project gwmap
	/**
	 * Creates a custom GProjection for flat maps.
	 *
	 * @classDescription	Creates a custom GProjection for flat maps.
	 * @param {Number} width The width in pixels of the map at the specified zoom level.
	 * @param {Number} height The height in pixels of the map at the specified zoom level.
	 * @param {Number} pixelsPerLon The number of pixels per degree of longitude at the specified zoom level.
	 * @param {Number} zoom The zoom level width, height, and pixelsPerLon are set for.
	 * @param {Number} maxZoom The maximum zoom level the map will go.
	 * @constructor	
	 */
	function FlatProjection(width,height,pixelsPerLon,zoom,maxZoom)
	{
		this.pixelsPerLonDegree = new Array(maxZoom);
		this.tileBounds = new Array(maxZoom);

		width /= Math.pow(2,zoom);
		height /= Math.pow(2,zoom);
		pixelsPerLon /= Math.pow(2,zoom);
		
		for(var i=maxZoom; i>=0; i--)
		{
			this.pixelsPerLonDegree[i] = pixelsPerLon*Math.pow(2,i);
			this.tileBounds[i] = new GPoint(Math.ceil(width*Math.pow(2,i)/256), Math.ceil(height*Math.pow(2,i)/256));
		}
	}

	FlatProjection.prototype = new GProjection();

	FlatProjection.prototype.fromLatLngToPixel = function(point,zoom)
	{
		var x = Math.round(point.lng() * this.pixelsPerLonDegree[zoom]);
		var y = Math.round(point.lat() * this.pixelsPerLonDegree[zoom]);
		return new GPoint(x,y);
	}

	FlatProjection.prototype.fromPixelToLatLng = function(pixel,zoom,unbounded)	
	{
		var lng = pixel.x/this.pixelsPerLonDegree[zoom];
		var lat = pixel.y/this.pixelsPerLonDegree[zoom];
		return new GLatLng(lat,lng,true);
	}

	FlatProjection.prototype.tileCheckRange = function(tile, zoom, tilesize)
	{
		if( tile.y<0 || tile.x<0 || tile.y>=this.tileBounds[zoom].y || tile.x>=this.tileBounds[zoom].x )
		{
			return false;
		}
		return true;
	}
	FlatProjection.prototype.getWrapWidth = function(zoom)
	{
		return Number.MAX_VALUE;
	}

    /*
     * Main load function:
     */

    function load() {
        var MapWidth = %(xsize)d;
        var MapHeight = %(ysize)d;
        var MapMaxZoom = %(maxzoom)d;
        var MapPxPerLon = %(tilesize)d;

        if (GBrowserIsCompatible()) {
            var map = new GMap2( document.getElementById("map") );
            var tileLayer = [ new GTileLayer( new GCopyrightCollection(null), 0, MapMaxZoom ) ];
            tileLayer[0].getTileUrl = function(a,b) {
                var y = Math.floor(MapHeight / (MapPxPerLon * Math.pow(2, (MapMaxZoom-b)))) - a.y;
                // Google Maps indexed tiles from top left, we from bottom left, it causes problems during zooming, solution?
                return b+"/"+a.x+"/"+y+".png";
            }
            var mapType = new GMapType(
                tileLayer,
                new FlatProjection( MapWidth, MapHeight, MapPxPerLon, MapMaxZoom-2, MapMaxZoom),
                'Default',
                { maxResolution: MapMaxZoom, minResolution: 0, tileSize: MapPxPerLon }
            );
            map.addMapType(mapType);

            map.removeMapType(G_NORMAL_MAP);
            map.removeMapType(G_SATELLITE_MAP);
            map.removeMapType(G_HYBRID_MAP);

            map.setCenter(new GLatLng((MapHeight/MapPxPerLon/4)/2, (MapWidth/MapPxPerLon/4)/2), %(zoom)d, mapType);

            //alert((MapHeight/MapPxPerLon/4)/2 + " x " + (MapWidth/MapPxPerLon/4)/2);
            //map.addOverlay(new GMarker( new GLatLng((MapHeight/MapPxPerLon/4)/2,(MapWidth/MapPxPerLon/4)/2) ));

            map.getContainer().style.backgroundColor='#fff';

            map.addControl(new GLargeMapControl());
            // Overview Map Control is not running correctly...
            // map.addControl(new GOverviewMapControl());
        }
        resize();
    }

    onresize=function(){ resize(); };

    //]]>
    </script>
  </head>
  <body onload="load()" onunload="GUnload()">
      <div id="header"><h1>%(title)s</h1></div>
      <div id="subheader">Generated by <a href="http://www.klokan.cz/projects/gdal2tiles/">GDAL2Tiles</a>, Copyright (c) 2007 <a href="http://www.klokan.cz/">Klokan Petr Pridal</a>,  <a href="http://www.gdal.org/">GDAL</a> &amp; <a href="http://www.osgeo.org/">OSGeo</a> <a href="http://code.google.com/soc/">SoC 2007</a>
      </div>
       <div id="map"></div>
  </body>
</html>
""" % args

    return s
