# lambda-tiler

#### AWS Lambda + rio-tiler to serve tiles from any web hosted files

# Info


---

# Installation

##### Requirement
  - AWS Account
  - Docker
  - node + npm


#### Create the package

```bash
# Build Amazon linux AMI docker container + Install Python modules + create package
git clone https://github.com/vincentsarago/lambda-tiler.git
cd lambda-tiler/
make all
```

#### Deploy to AWS

```bash
#configure serverless (https://serverless.com/framework/docs/providers/aws/guide/credentials/)
npm install
sls deploy
```

# Endpoint

## /bounds

*Inputs:*
- url: any valid url

*Returns:*
A JSON object with the bounds of the tiff.

*example:*
```
$ curl {your-endpoint}/bounds?url=https://any-file.on/the-internet.tif

  {"url": "https://any-file.on/the-internet.tif", "bounds": [90.47546096087822, 23.803014490532913, 90.48441996322644, 23.80577697976369]}
```

## /metadata

*Inputs:*
- url: any valid url

*Returns:*
A JSON object with metadata about the tiff.

*example:*
```
$ curl {your-endpoint}/metadata?url=https://any-file.on/the-internet.tif
```

## /viewer

*Inputs:*
- url: any valid url

*Returns:*
A Leaflet viewer that allows you to pan & zoom the tiff.

*example:*
```
$ curl {your-endpoint}/metadata?url=https://any-file.on/the-internet.tif
```


#### /tiles/z/x/y.png

*Inputs:*
- url: any valid url

*Options:*
- rgb: select bands indexes to return (e.g: (1,2,3), (4,1,2))
- nodata: nodata value to create mask

*example:*
```
$ curl {your-endpoint}/tiles/7/10/10.png?url=https://any-file.on/the-internet.tif

```

## /viewer

*Inputs:*
None

*Returns:*
A Leaflet viewer that allows you to pan & zoom on a sample tiff hosted on s3.

*example:*
```
$ curl {your-endpoint}/viewer
```

