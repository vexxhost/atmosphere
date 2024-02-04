pipeline {
	agent none

	options {
		disableConcurrentBuilds(abortPrevious: true);
	}

	environment {
		EARTHLY_CI = 'true'
		EARTHLY_BUILD_ARGS = "REGISTRY=registry.atmosphere.dev:5000/${env.BRANCH_NAME.toLowerCase()}"
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

					steps {
						checkout scm
						sh 'earthly --push +images'

						script {
							env.EARTHLY_OUTPUT = "true"
							sh 'earthly +pin-images'
						}

						sh 'earthly +scan-images'
						stash name: 'src-with-pinned-images', includes: '**'
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
			parallel {
				stage('openvswitch') {
					agent {
						label 'jammy-16c-64g'
					}

					steps {
						// Checkout code with built/pinned images
						unstash 'src-with-pinned-images'

						// Install dependencies
						sh 'sudo apt-get install -y git python3-pip'
						sh 'sudo pip install poetry'

						// Run tests
						dir("${WORKSPACE}") {
							sh 'sudo poetry install --with dev'

							script {
								env.ATMOSPHERE_NETWORK_BACKEND = 'openvswitch'
								sh 'sudo --preserve-env=ATMOSPHERE_NETWORK_BACKEND poetry run molecule test -s aio'
							}
						}
					}

					post {
						always {
							sh 'sudo ./build/fetch-kubernetes-logs.sh kubernetes-logs/ || true'
							archiveArtifacts artifacts: 'kubernetes-logs/**', allowEmptyArchive: true
						}
					}
				}

				stage('ovn') {
					agent {
						label 'jammy-16c-64g'
					}

					steps {
						// Checkout code with built/pinned images
						unstash 'src-with-pinned-images'

						// Install dependencies
						sh 'sudo apt-get install -y git python3-pip'
						sh 'sudo pip install poetry'

						// Run tests
						dir("${WORKSPACE}") {
							sh 'sudo poetry install --with dev'

							script {
								env.ATMOSPHERE_NETWORK_BACKEND = 'ovn'
								sh 'sudo --preserve-env=ATMOSPHERE_NETWORK_BACKEND poetry run molecule test -s aio'
							}
						}
					}

					post {
						always {
							sh 'sudo ./build/fetch-kubernetes-logs.sh kubernetes-logs/ || true'
							archiveArtifacts artifacts: 'kubernetes-logs/**', allowEmptyArchive: true
						}
					}
				}
			}
		}

		// promote images
		// release?
		// todo: manual pin commit to main (avoiding loop)
	}
}
