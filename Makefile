
SHELL = /bin/bash

all: build package

build:
	docker build --tag lambda:latest .

package:
	docker run \
		-w /var/task/ \
		--name lambda \
		-itd \
		lambda:latest
	docker cp lambda:/tmp/package.zip package.zip
	docker stop lambda
	docker rm lambda

shell:
	docker run \
		--name lambda  \
		--volume $(shell pwd)/:/data \
		--env PYTHONPATH=/var/task/vendored \
		--env GDAL_CACHEMAX=75% \
		--env GDAL_DISABLE_READDIR_ON_OPEN=TRUE \
		--env GDAL_TIFF_OVR_BLOCKSIZE=512 \
		--env VSI_CACHE=TRUE \
		--env VSI_CACHE_SIZE=536870912 \
		--rm \
		-it \
		lambda:latest /bin/bash

test:
	docker run \
		-w /var/task/ \
		--name lambda \
		--env AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
		--env AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
 		--env AWS_REGION=us-west-2 \
		--env PYTHONPATH=/var/task \
		--env GDAL_CACHEMAX=75% \
		--env GDAL_DISABLE_READDIR_ON_OPEN=TRUE \
		--env GDAL_TIFF_OVR_BLOCKSIZE=512 \
		--env VSI_CACHE=TRUE \
		--env VSI_CACHE_SIZE=536870912 \
		-itd \
		lambda:latest
	docker cp package.zip lambda:/tmp/package.zip
	docker exec -it lambda bash -c 'unzip -q /tmp/package.zip -d /var/task/'
	docker exec -it lambda bash -c 'pip3 install boto3 jmespath python-dateutil -t /var/task'
	docker exec -it lambda python3 -c 'from app.handler import APP; print(APP({"path": "/bounds", "queryStringParameters": {"url": "https://landsat-pds.s3.amazonaws.com/c1/L8/002/056/LC08_L1TP_002056_20171201_20171207_01_T1/LC08_L1TP_002056_20171201_20171207_01_T1_B10.TIF"}, "pathParameters": "null", "requestContext": "null", "httpMethod": "GET"}, None))'
	docker exec -it lambda python3 -c 'from app.handler import APP; print(APP({"path": "/tiles/7/41/61.png", "queryStringParameters": {"url": "https://landsat-pds.s3.amazonaws.com/c1/L8/002/056/LC08_L1TP_002056_20171201_20171207_01_T1/LC08_L1TP_002056_20171201_20171207_01_T1_B10.TIF"}, "pathParameters": "null", "requestContext": "null", "httpMethod": "GET"}, None))'
	docker stop lambda
	docker rm lambda



clean:
	docker stop lambda
	docker rm lambda
