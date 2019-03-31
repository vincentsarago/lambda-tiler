FROM remotepixel/amazonlinux-gdal:2.4.0

ENV PACKAGE_TMP /tmp/package

COPY setup.py setup.py
COPY lambda_tiler/ lambda_tiler/

# Install dependencies
RUN pip3 install . --no-binary numpy,rasterio -t $PACKAGE_TMP -U
