# lambda-tiler

[![CircleCI](https://circleci.com/gh/vincentsarago/lambda-tiler.svg?style=svg)](https://circleci.com/gh/vincentsarago/lambda-tiler)
[![codecov](https://codecov.io/gh/vincentsarago/lambda-tiler/branch/master/graph/badge.svg)](https://codecov.io/gh/vincentsarago/lambda-tiler)

#### AWS Lambda + rio-tiler to serve tiles from any web hosted files

![image_preview](https://user-images.githubusercontent.com/10407788/56755674-0fbad500-675e-11e9-8996-f0fae4a1a30c.jpeg)

**lambda-tiler** is a simple serverless (AWS Lambda function) application that serves Map Tiles dynamically created from COGs hosted remotely (s3, http, ...)

# Deploy

#### Requirement
  - AWS Account
  - Docker (+ docker-compose)
  - node + npm (serverless)


#### Create the package

```bash
# Build Amazon linux AMI docker container + Install Python modules + create package
$ git clone https://github.com/vincentsarago/lambda-tiler.git
$ cd lambda-tiler/

$ docker-compose build
$ docker-compose run --rm package

# Tests
$ docker-compose run --rm tests
```

Note: Docker image from https://github.com/RemotePixel/amazonlinux-gdal

#### Deploy to AWS

```bash
#configure serverless (https://serverless.com/framework/docs/providers/aws/guide/credentials/)
npm install
sls deploy
```

# API

## Viewer
`/viewer` - GET

A web viewer that allows you to pan & zoom the COG.

Inputs:
- **url** (required, str): mosaic id
- **kwargs** (optional): Other querystring parameters will be forwarded to the tile url.

Outputs:
- **html** (text/html)

`$ curl {your-endpoint}/viewer?url=https://any-file.on/the-internet.tif`

## TileJSON (2.1.0)
`/tilejson.json` - GET

Inputs:
- **url** (required): mosaic definition url
- **tile_format** (optional, str): output tile format (default: "png")
- **kwargs** (in querytring): Other querystring parameters will be forwarded to the tile url

Outputs:
- **tileJSON** (application/json) 

`$ curl https://{endpoint-url}/tilejson.json?url=https://any-file.on/the-internet.tif`

```json
{
    "bounds": [...],      
    "center": [lon, lat], 
    "minzoom": 18,        
    "maxzoom": 22,        
    "name": "the-internet.tif",
    "tilejson": "2.1.0",  
    "tiles": [...] ,      
}
```

## Bounds

Inputs:
- **url** (required): mosaic definition url

Outputs:
- **metadata** (application/json) 

`$ curl https://{endpoint-url}/bounds?url=https://any-file.on/the-internet.tif`

```json
{
  "url": "https://any-file.on/the-internet.tif", 
  "bounds": [...]
}
```

## Metadata

`/metadata` - GET

Inputs:
- **url** (required, str): dataset url
- **pmin** (optional, str): min percentile (default: 2).
- **pmax** (optional, str): max percentile (default: 98).
- **nodata** (optional, str): Custom nodata value if not preset in dataset.
- **indexes** (optional, str): dataset band indexes
- **overview_level** (optional, str): Select the overview level to fetch for statistic calculation
- **max_size** (optional, str): Maximum size of dataset to retrieve for overview level automatic calculation
- **histogram_bins** (optional, str, default:20): number of equal-width histogram bins
- **histogram_range** (optional, str): histogram min/max

Outputs:
- **metadata** (application/json) 


`$ curl https://{endpoint-url}/metadata?url=s3://url=https://any-file.on/the-internet.tif`

```json
{
    'address': 's3://myfile.tif',
    'bbox': [...],
    'band_descriptions': [(1, 'red'), (2, 'green'), (3, 'blue'), (4, 'nir')]
    'statistics': {
        '1': {
            'pc': [38, 147],
            'min': 20,
            'max': 180,
            'std': 28.123562304138662,
            'histogram': [
                [...],
                [...]
            ]
        },
        ...
    }
}
```


## Tiles
`/tiles/{z}/{x}/{y}` - GET

`/tiles/{z}/{x}/{y}.{ext}` - GET

`/tiles/{z}/{x}/{y}@{scale}x` - GET

`/tiles/{z}/{x}/{y}@{scale}x.{ext}` - GET

Inputs:
- **z**: Mercator tile zoom value
- **x**: Mercator tile x value
- **y**: Mercator tile y value
- **ext**: image format (e.g `jpg`)
- **scale** (optional, int): tile scale (default: 1)
- **url** (required, str): dataset url
- **indexes** (optional, str): dataset band indexes (default: dataset indexes)
- **expr** (optional, str): dataset expression
- **nodata** (optional, str): Custom nodata value if not preset in dataset (default: None)
- **rescale** (optional, str): min/max for data rescaling (default: None)
- **color_formula** (optional, str): rio-color formula (default: None)
- **color_map** (optional, str): rio-tiler colormap (default: None)

Outputs:
- **image body** (image/jpeg) 

`$ curl {your-endpoint}/tiles/7/10/10.png?url=https://any-file.on/the-internet.tif`

## Example

A web viewer that allows you to pan & zoom on a sample tiff.

Inputs: None

Outputs:
- **html** (text/html)

`$ curl {your-endpoint}/example`