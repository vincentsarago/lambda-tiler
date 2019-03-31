SHELL = /bin/bash

all: package test

package:
	docker build --tag lambdatiler:latest .
	docker run \
		--name lambdatiler \
		-w /tmp \
		--volume $(shell pwd)/bin:/tmp/bin \
		--volume $(shell pwd)/:/local \
		--env PACKAGE_TMP=/tmp/package \
		--env PACKAGE_PATH=/local/package.zip \
		-itd lambdatiler:latest \
		bash
	docker exec -it lambdatiler bash '/tmp/bin/package.sh'
	docker stop lambdatiler
	docker rm lambdatiler

test:
	docker run \
		--name lambda \
		-w /var/task/ \
		--volume $(shell pwd)/bin:/tmp/bin \
		--volume $(shell pwd)/:/local \
		--env GDAL_DATA=/var/task/share/gdal \
		--env PYTHONWARNINGS=ignore \
		--env GDAL_CACHEMAX=75% \
		--env VSI_CACHE=TRUE \
		--env VSI_CACHE_SIZE=536870912 \
		--env CPL_TMPDIR="/tmp" \
		--env GDAL_HTTP_MERGE_CONSECUTIVE_RANGES=YES \
		--env GDAL_HTTP_MULTIPLEX=YES \
		--env GDAL_HTTP_VERSION=2 \
		--env GDAL_DISABLE_READDIR_ON_OPEN=EMPTY_DIR \
		-itd \
		lambci/lambda:build-python3.6 bash
	docker exec -it lambda bash -c 'unzip -q /local/package.zip -d /var/task/'
	docker exec -it lambda python3 -c 'from lambda_tiler.handler import APP; assert APP({"path": "/bounds", "queryStringParameters": {"url": "https://oin-hotosm.s3.amazonaws.com/5ac626e091b5310010e0d482/0/5ac626e091b5310010e0d483.tif"}, "pathParameters": "null", "requestContext": "null", "httpMethod": "GET"}, None)'
	docker exec -it lambda python3 -c 'from lambda_tiler.handler import APP; assert APP({"path": "/processing/19/319379/270522.png", "queryStringParameters": {"url": "https://oin-hotosm.s3.amazonaws.com/5ac626e091b5310010e0d482/0/5ac626e091b5310010e0d483.tif", "ratio":"(b3-b2)/(b3+b2)"}, "pathParameters": "null", "requestContext": "null", "httpMethod": "GET"}, None)'
	docker exec -it lambda python3 -c 'from lambda_tiler.handler import APP; assert APP({"path": "/tiles/19/319379/270522.png", "queryStringParameters": {"url": "https://oin-hotosm.s3.amazonaws.com/5ac626e091b5310010e0d482/0/5ac626e091b5310010e0d483.tif"}, "pathParameters": "null", "requestContext": "null", "httpMethod": "GET"}, None)'
	docker stop lambda
	docker rm lambda


clean:
	docker stop lambda
	docker rm lambda
