pipeline {
  agent any
  stages {
    stage('Build') {
      steps {
        sh '''#!/bin/bash
set -e

# Create a virtual environment

PYENV_HOME=env

if [ -d env ]
then
    rm -rf env
fi

python3 -m venv env

# Prepare environment

source env/bin/activate
pip install -r requirements.txt



'''
        sh '''#!/bin/bash
source env/bin/activate

python setup.py build sdist

# Install package into test environment

python setup.py install'''
      }
    }

    stage('Test') {
      steps {
        sh '''#!/bin/bash
source env/bin/activate
python setup.py nosetests'''
      }
    }

    stage('Deploy') {
      steps {
        sh '''#!/bin/bash

tar cvzf avwx-$(cat VERSION).tar.gz \\
    config.yml \\
    map2.py \\
    dist/avwx_map-$(cat VERSION).tar.gz
'''
        sh '''#!/bin/bash
VERSION=$(head -n 1 VERSION)
REMOTE=map@ledvfrmap
NAME="avwx_map-$VERSION"
FILENAME="$NAME.tar.gz"
DIR="/app/$VERSION"
TARBALL="dist/$FILENAME"

scp $TARBALL $REMOTE:/app

ssh $REMOTE bash <<EOF
set -e
cd /app
mkdir -p src
mv $FILENAME src/
source ~/venv/map/bin/activate
python -m venv $VERSION
source $VERSION/bin/activate
cd src
tar xf $FILENAME
cd $NAME
python setup.py install
cd ..
rm -r $NAME
EOF'''
      }
    }

  }
}