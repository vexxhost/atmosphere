pipeline {
	agent none

	options {
		disableConcurrentBuilds(abortPrevious: true);
	}

	environment {
		EARTHLY_CI = 'true'
		EARTHLY_BUILD_ARGS = "REGISTRY=registry:5000"
	}

	stages {
		// run-linters

		stage('build') {
			parallel {
				// build-collection

				stage('images') {
					agent {
						label 'earthly'
					}

					stages {
						stage('build') {
							steps {
								checkout scm
								sh 'earthly +images'
								// TODO: pin using temporary registry
								stash name: 'src-with-pinned-images', includes: '**'
							}
						}

						stage('scan') {
							steps {
								unstash 'src-with-pinned-images'
								sh 'earthly +scan-images'
							}
						}
					}
				}

				stage('docs') {
					agent {
						label 'earthly'
					}

					steps {
						checkout scm
						sh 'earthly +mkdocs-build'
					}
				}
			}
		}

		stage('integration') {
			agent {
				label 'jammy-16c-64g'
			}

			steps {
				// Checkout code with built/pinned images
				unstash 'src-with-pinned-images'

				// Install dependencies
				sh 'sudo apt-get update'
				sh 'sudo apt-get install -y git python3-pip'
				sh 'sudo pip install poetry'

				// Run tests
				dir("${WORKSPACE}") {
					sh 'sudo poetry install --with dev'
					sh 'sudo poetry run molecule test -s aio'
				}
			}
		}

		// promote images
		// release?
		// todo: manual pin commit to main (avoiding loop)
	}
}
