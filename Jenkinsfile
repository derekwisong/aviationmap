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
scp tar avwx-$(cat VERSION).tar.gz map@ledvfrmap:builds/'''
      }
    }

  }
}