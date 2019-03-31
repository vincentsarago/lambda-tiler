#!/bin/bash
echo "-----------------------"
echo "Creating lambda package ${PACKAGE_PATH}"
echo "-----------------------"
echo
echo "Remove useless python files"

find $PACKAGE_TMP -name "*-info" -type d -exec rm -rdf {} +

echo "Remove lambda python packages"
rm -rdf $PACKAGE_TMP/boto3/ \
  && rm -rdf $PACKAGE_TMP/botocore/ \
  && rm -rdf $PACKAGE_TMP/docutils/ \
  && rm -rdf $PACKAGE_TMP/dateutil/ \
  && rm -rdf $PACKAGE_TMP/jmespath/ \
  && rm -rdf $PACKAGE_TMP/s3transfer/ \
  && rm -rdf $PACKAGE_TMP/numpy/doc/

echo "Remove uncompiled python scripts"
find $PACKAGE_TMP -type f -name '*.pyc' | while read f; do n=$(echo $f | sed 's/__pycache__\///' | sed 's/.cpython-36//'); cp $f $n; done;
find $PACKAGE_TMP -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf
find $PACKAGE_TMP -type d -a -name 'tests' -print0 | xargs -0 rm -rf
find $PACKAGE_TMP -type f -a -name '*.py' -print0 | xargs -0 rm -f

echo "Strip shared libraries"
cd $PREFIX && find lib -name \*.so\* -exec strip {} \;
cd $PREFIX && find lib64 -name \*.so\* -exec strip {} \;

echo "Create archive"
cd $PACKAGE_TMP && zip -r9q $PACKAGE_PATH *
cd $PREFIX && zip -r9q --symlinks $PACKAGE_PATH lib/*.so*
cd $PREFIX && zip -r9q --symlinks $PACKAGE_PATH lib64/*.so*
cd $PREFIX && zip -r9q $PACKAGE_PATH share
