pipeline {
  agent any
  stages {
    stage('Test Step') {
      steps {
        sh '''#!/bin/bash

echo "Hello World"'''
      }
    }

    stage('Python Setup') {
      steps {
        sh '''#!/bin/bash
set -e

python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
'''
      }
    }

  }
}