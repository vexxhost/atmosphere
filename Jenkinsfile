pipeline {
    stages {
        stage('integration') {
	    agent {
                label 'jammy-16c-64g'
	    }

            steps {
	    	checkout scm

		// Install dependencies
		sh 'sudo apt-get update'
		sh 'sudo apt-get install -y git python3-pip'
		sh 'sudo pip install poetry'

		// Run tests
		dir("${WORKSPACE}") {
		    sh 'sudo poetry install --with dev'
		    sh 'sudo poetry run molecule converge -s aio'
		}
	    }
	}
    }
}
