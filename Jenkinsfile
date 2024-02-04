pipeline {
	agent none

	options {
		disableConcurrentBuilds(abortPrevious: true);
	}

	// TODO: periodic multi-node jobs

	environment {
		EARTHLY_CI = 'true'
		EARTHLY_BUILD_ARGS = "REGISTRY=registry.atmosphere.dev:5000/${env.BRANCH_NAME.toLowerCase()}"
	}

	stages {
		// run-linters
		// template all helm charts during lint stage to catch early failure

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
			matrix {
				axes {
					axis {
						name 'NETWORK_BACKEND'
						values 'openvswitch', 'ovn'
					}
				}

				agent {
					label 'jammy-16c-64g'
				}

				environment {
					ATMOSPHERE_DEBUG = "true"
					ATMOSPHERE_NETWORK_BACKEND = "${NETWORK_BACKEND}"
				}

				stages {
					stage('molecule') {
						steps {
							// Checkout code with built/pinned images
							unstash 'src-with-pinned-images'

							// Install dependencies
							sh 'sudo apt-get install -y git python3-pip'
							sh 'sudo pip install poetry'

							// Run tests
							sh 'sudo poetry install --with dev'
							sh 'sudo --preserve-env=ATMOSPHERE_DEBUG,ATMOSPHERE_NETWORK_BACKEND poetry run molecule test -s aio'
						}
					}
				}

				post {
					always {
						sh "sudo ./build/fetch-kubernetes-logs.sh logs/${NETWORK_BACKEND}/kubernetes || true"
						archiveArtifacts artifacts: 'logs/**', allowEmptyArchive: true
					}
				}
			}
		}

		// promote images
		// release?
		// todo: manual pin commit to main (avoiding loop)
	}
}
