#!/bin/bash
echo "lambda-tiler Version: " && python3.6 -c 'from lambda_tiler import __version__ as lt_version; print(lt_version)'

echo "/bounds"
python3 -c 'from lambda_tiler.handler import APP; resp = APP({"path": "/bounds", "queryStringParameters": {"url": "https://oin-hotosm.s3.amazonaws.com/5ac626e091b5310010e0d482/0/5ac626e091b5310010e0d483.tif"}, "pathParameters": "null", "requestContext": "null", "httpMethod": "GET", "headers": {}}, None); print("OK") if resp["statusCode"] == 200 else print("NOK")'

echo "/metadata"
python3 -c 'from lambda_tiler.handler import APP; resp = APP({"path": "/metadata", "queryStringParameters": {"url": "https://oin-hotosm.s3.amazonaws.com/5ac626e091b5310010e0d482/0/5ac626e091b5310010e0d483.tif"}, "pathParameters": "null", "requestContext": "null", "httpMethod": "GET", "headers": {}}, None); print("OK") if resp["statusCode"] == 200 else print("NOK")'

echo "/tilejson.json"
python3 -c 'from lambda_tiler.handler import APP; resp = APP({"path": "/tilejson.json", "queryStringParameters": {"url": "https://oin-hotosm.s3.amazonaws.com/5ac626e091b5310010e0d482/0/5ac626e091b5310010e0d483.tif"}, "pathParameters": "null", "requestContext": "null", "httpMethod": "GET", "headers": {}}, None); print("OK") if resp["statusCode"] == 200 else print("NOK")'

echo "/tiles"
python3 -c 'from lambda_tiler.handler import APP; resp = APP({"path": "/tiles/19/319379/270522.png", "queryStringParameters": {"url": "https://oin-hotosm.s3.amazonaws.com/5ac626e091b5310010e0d482/0/5ac626e091b5310010e0d483.tif"}, "pathParameters": "null", "requestContext": "null", "httpMethod": "GET", "headers": {}}, None); print("OK") if resp["statusCode"] == 200 else print("NOK")'
python3 -c 'from lambda_tiler.handler import APP; resp = APP({"path": "/tiles/19/319379/270522.png", "queryStringParameters": {"url": "https://oin-hotosm.s3.amazonaws.com/5ac626e091b5310010e0d482/0/5ac626e091b5310010e0d483.tif", "expr":"(b3-b2)/(b3+b2)", "rescale": "-1,1"}, "pathParameters": "null", "requestContext": "null", "httpMethod": "GET", "headers": {}}, None); print("OK") if resp["statusCode"] == 200 else print("NOK")'

echo "Done"