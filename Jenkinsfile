pipeline {
  agent any
  stages {
    stage('Test Step') {
      steps {
        sh '''#!/bin/bash

whoami
pwd
echo "Hello World"
env
'''
      }
    }

    stage('Python Setup') {
      steps {
        sh '''#!/bin/bash
set -e

# Create a virtual environment

PYENV_HOME=env

if [ -d $PYENV_HOME ]
then
    rm -rf $PYENV_HOME
fi

python3 -m venv $PYENV_HOME

# Build distribution
source $PYENV_HOME/bin/activate
pip install -r requirements.txt

python setup.py build sdist

# Install package

python setup.py install

# Write out path to source distribution

DISTFILE="dist/avwx_map-$(head -n 1 VERSION).tar.gz"
echo "$DISTFILE" > DISTFILE

'''
      }
    }

    stage('Create Tarball') {
      steps {
        sh '''#!/bin/bash

tar cvzf avwx_map.tar.gz env/ map2.py config.yml
ls -lh'''
      }
    }

    stage('Deploy') {
      steps {
        sh '''#!/bin/bash

scp avwx_map.tar.gz map@ledvfrmap:builds/'''
      }
    }

  }
}