pipeline {
    agent any

    environment {
        VENV_DIR = 'venv'
        GCP_PROJECT="chatbot-474313"
        GCLOUD_PATH= "/var/jenkins_home/google-cloud-sdk/bin"
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
        stage('Building and pushing Docker image to GCR') {
            steps {
                withCredentials([file(credentialsId :'gcp-key',variable :'google_application_credentials')]){
                   script{
                      echo 'Building and pushing Docker image to GCR....'
                      sh '''
                      export PATH=$PATH:$(GCLOUD_PATH)

                      gcloud auth activate-service-account--key-file=${google_application_credentials}

                      gcloud config set project ${GCP_PROJECT}

                      gcloud auth configure-docker --quiet

                      docker build -t gcr.io/${GCP_PROJECT}/bot:latest .

                      docker push gcr.io/${GCP_PROJECT}/bot:latest 

                      '''

                    }
                }
            }
        }
    }


}

