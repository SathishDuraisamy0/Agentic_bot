pipeline {
    agent {
        // ✅ Run all pipeline stages inside a Python container
        docker {
            image 'python:3.11-slim'
            args '-u root'
        }
    }

    environment {
        VENV_DIR = 'venv'
    }

    stages {
        stage('Clone GitHub Repo to Jenkins') {
            steps {
                script {
                    echo '📥 Cloning GitHub repository into Jenkins workspace...'
                    checkout scmGit(
                        branches: [[name: '*/main']],
                        extensions: [],
                        userRemoteConfigs: [[
                            credentialsId: 'github-token',
                            url: 'https://github.com/SathishDuraisamy0/Agentic_bot.git'
                        ]]
                    )
                }
            }
        }

        stage('Setup Virtual Environment & Install Dependencies') {
            steps {
                script {
                    echo '⚙️ Setting up Python virtual environment and installing dependencies...'
                    sh '''
                    python -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -e .
                    '''
                }
            }
        }
    }
}

