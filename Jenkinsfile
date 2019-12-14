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

date
pwd

python --version

python3 --version

#python -m venv env'''
      }
    }

  }
}