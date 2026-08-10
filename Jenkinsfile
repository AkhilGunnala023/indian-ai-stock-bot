pipeline {

    agent any

    stages {

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

        stage('Run AI Stock Bot') {
            steps {
                bat '''
                    set PYTHONPATH=%WORKSPACE%
                    set PYTHONIOENCODING=utf-8
                    set PYTHONUTF8=1
                    .jenkins-venv\\Scripts\\python.exe scripts\\run_daily_pipeline.py
                '''
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