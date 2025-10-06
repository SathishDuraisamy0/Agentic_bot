pipeline {
    agent any

    environment {
        VENV_DIR = 'venv'
    }

    stages {
        stage('Cloning GitHub Repo to Jenkins') {
            steps {
                script {
                    echo '📥 Cloning GitHub repo to Jenkins............'
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

        stage('Setting up Virtual Environment & Installing Dependencies') {
            steps {
                script {
                    echo '⚙️ Setting up Virtual Environment & Installing Dependencies............'
                    sh '''
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -e .
                    '''
                }
            }
        }
    }
}
