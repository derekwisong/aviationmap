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

python3 -m venv env
source env/bin/activate

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
ls -l'''
      }
    }

  }
}