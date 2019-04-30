SHELL = /bin/bash

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