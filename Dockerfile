FROM remotepixel/amazonlinux:gdal3.0-py3.7-cogeo

WORKDIR /tmp

ENV PYTHONUSERBASE=/var/task

COPY setup.py setup.py
COPY lambda_tiler/ lambda_tiler/

RUN pip install . --user
