FROM remotepixel/amazonlinux-gdal:2.4.2

RUN pip3 install pip -U

ENV PACKAGE_PREFIX /tmp/python

COPY setup.py setup.py
COPY lambda_tiler/ lambda_tiler/

# Install dependencies
RUN CFLAGS="--std=c99" pip3 install . --no-binary numpy,rasterio -t $PACKAGE_PREFIX -U
