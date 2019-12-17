pipeline {
  agent any
  stages {
    stage('Build') {
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

# Install package into test environment

python setup.py install


'''
      }
    }

    stage('Test') {
      steps {
        sh 'python setup.py nosetests'
      }
    }

    stage('Deploy') {
      steps {
        sh '''tar cvzf avwx-$(cat VERSION).tar.gz \\
    config.yml \\
    map2.py \\
    dist/avwx_map-$(cat VERSION).tar.gz
'''
        sh 'scp tar avwx-$(cat VERSION).tar.gz map@ledvfrmap:builds/'
      }
    }

  }
}