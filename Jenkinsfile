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
                bat '"C:\\Users\\gunna\\AppData\\Local\\Programs\\Python\\Python314\\python.exe" -m venv .jenkins-venv'
                bat '.jenkins-venv\\Scripts\\python.exe -m pip install --upgrade pip'
                bat '.jenkins-venv\\Scripts\\python.exe -m pip install -r requirements.txt'
            }
        }

        stage('Environment Test') {
            steps {
                bat '"C:\\Program Files\\Eclipse Adoptium\\jdk-25.0.4.7-hotspot\\bin\\java.exe" -version'
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