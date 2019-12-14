pipeline {
  agent any
  stages {
    stage('Test Step') {
      steps {
        sh '''#!/bin/bash

echo "Hello World"
env'''
      }
    }

    stage('Python Setup') {
      steps {
        sh '''#!/bin/bash
set -e

PYENV_HOME=env

if [ -d $PYENV_HOME ]
then
    rm -rf $PYENV_HOME
fi

python3 -m venv $PYENV_HOME
source $PYENV_HOME/bin/activate

pip install wheel
pip install setuptools
pip install -r requirements.txt

python setup.py build install
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