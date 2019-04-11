viewer_template = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset='utf-8' />
    <title>example</title>
    <meta
      name='viewport'
      content='initial-scale=1,maximum-scale=1,user-scalable=no'
    />
    <script src='https://code.jquery.com/jquery-3.2.1.min.js'>
    </script>
    <script src='https://npmcdn.com/@turf/turf@3.5.1/turf.min.js'>
    </script>
    <script
      src='https://api.tiles.mapbox.com/mapbox-gl-js/v0.43.0/mapbox-gl.js'>
    </script>
    <link
      href='https://api.tiles.mapbox.com/mapbox-gl-js/v0.43.0/mapbox-gl.css'
      rel='stylesheet'
    />
    <style>
      body {{ margin:0; padding:0; }}
      #map {{ position:absolute; top:0; bottom:0; width:100%; }}
    </style>
  </head>
  <body>

    <div id='map'></div>
    <script>

      var endpoint = '{endpoint}';

      var map = new mapboxgl.Map({{
          container: 'map',
          style: {{ version: 8, sources: {{}}, layers: [] }},
          center: [-119.5591, 37.715],
          zoom: 9
      }});

      var url = '{cogurl}';

      map.on('load', () => {{

        const bounds_query = `${{endpoint}}/bounds?url=${{url}}`;
        $.getJSON(bounds_query).done()
          .then(data => {{
            console.log(data);

            map.addSource('tiles', {{
                "type": "raster",
                "tiles": [
                  `${{endpoint}}/tiles/{{z}}/{{x}}/{{y}}.png?url=${{url}}&nodata=0`
                ],
                "tileSize": 256,
                "bounds": data.bounds
            }});

            map.addLayer({{
                "id": "tiles",
                "source": "tiles",
                "type": "raster"
            }});

            const geojson = {{
              'type': 'FeatureCollection',
              'features': [turf.bboxPolygon(data.bounds)]
            }};

            map.addSource('tile', {{
              'type': 'geojson',
              'data': geojson
            }});

            map.addLayer({{
                'id': 'tile',
                'type': 'line',
                'source': 'tile',
                'layout': {{
                  'line-cap': 'round',
                  'line-join': 'round'
                }},
                'paint': {{
                  'line-color': '#1b34db',
                  'line-width': 2
                }}
            }});

            const extent = data.bounds;
            const llb = mapboxgl.LngLatBounds.convert(
              [
                [extent[0],extent[1]],
                [extent[2],extent[3]]
              ]
            );
            map.fitBounds(llb, {{padding: 50}});

          }});

      }});
    </script>

  </body>
</html>
"""
