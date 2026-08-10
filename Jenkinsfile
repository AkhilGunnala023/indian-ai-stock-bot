pipeline {

    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Python Environment') {
            steps {
                bat 'py -3.14 -m venv .jenkins-venv'
                bat '.jenkins-venv\\Scripts\\python.exe -m pip install --upgrade pip'
                bat '.jenkins-venv\\Scripts\\python.exe -m pip install -r requirements.txt'
            }
        }

        stage('Environment Test') {
            steps {
                bat 'java -version'
                bat '.jenkins-venv\\Scripts\\python.exe --version'
                bat '.jenkins-venv\\Scripts\\python.exe -c "import pandas, yfinance, xgboost, sklearn, joblib; print(\'AI BOT DEPENDENCIES OK\')"'
            }
        }
    }

    post {

        success {
            echo 'GitHub + Jenkins environment setup successful'
        }

        failure {
            echo 'GitHub + Jenkins setup failed'
        }
    }
}