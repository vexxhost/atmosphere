def installDocker() {
	sh 'curl -fsSL https://get.docker.com | sh'
	sh "sudo usermod -aG docker $USER"
}

def installEarthly() {
	installDocker()

	sh 'curl -fsSL https://github.com/earthly/earthly/releases/latest/download/earthly-linux-amd64 -o /usr/local/bin/earthly'
	sh 'chmod +x /usr/local/bin/earthly'
	sh 'earthly bootstrap --allow-privileged'
}

pipeline {
	agent none

	options {
		disableConcurrentBuilds(abortPrevious: true);
	}

	// TODO: periodic multi-node jobs

	environment {
		TEST_REGISTRY = "registry.atmosphere.dev:5000/${env.BRANCH_NAME.toLowerCase()}"
		PROD_REGISTRY = "ghcr.io/vexxhost/atmosphere"
		REGISTRY = "${env.BRANCH_NAME == 'main' ? PROD_REGISTRY : TEST_REGISTRY}"

		EARTHLY_CI = 'true'
		EARTHLY_BUILD_ARGS = "REGISTRY=${REGISTRY}"
	}

	stages {
		stage('lint') {
			parallel {
				stage('ansible-lint') {
					agent {
						label 'jammy-2c-4g'
					}

					steps {
						installEarthly()
						sh 'earthly --output +lint.ansible-lint'
					}

					post {
						always {
							junit testResults: 'ansible-lint.xml', allowEmptyResults: true
						}
					}
				}

				stage('helm') {
					agent {
						label 'jammy-2c-4g'
					}

					steps {
						installEarthly()
						sh 'earthly --output +lint.helm'
					}

					post {
						always {
							junit testResults: 'output/junit-helm-*.xml', allowEmptyResults: true
						}
					}
				}

				stage('markdownlint') {
					agent {
						label 'jammy-2c-4g'
					}

					steps {
						installEarthly()
						sh 'earthly --output +lint.markdownlint'
					}

					post {
						always {
							junit testResults: 'junit.xml', allowEmptyResults: true
						}
					}
				}

				stage('image-manifest') {
					agent {
						label 'jammy-2c-4g'
					}

					steps {
						installEarthly()
						sh 'earthly +lint.image-manifest'
					}
				}
			}
		}

		stage('unit') {
			parallel {
				stage('go') {
					agent {
						label 'jammy-2c-4g'
					}

					steps {
						installEarthly()
						sh 'earthly --output +unit.go'
					}

					post {
						always {
							junit 'junit-go.xml'
						}
					}
				}
			}
		}

		stage('build') {
			parallel {
				stage('collection') {
					agent {
						label 'jammy-2c-4g'
					}

					steps {
						installEarthly()
						sh 'earthly --output +build.collection'
						archiveArtifacts artifacts: 'dist/**'
					}
				}

				stage('images') {
					agent {
						label 'earthly'
					}

					steps {
						script {
							if (env.BRANCH_NAME == 'main') {
								docker.withRegistry('https://ghcr.io', 'github-packages-token') {
									sh 'earthly --push +images'
								}
							} else {
								sh 'earthly --push +images'
							}
						}

						sh 'earthly --output +pin-images'
						sh 'earthly +scan-images'
						stash name: 'src-with-pinned-images', includes: '**'
					}
				}

				stage('docs') {
					agent {
						label 'jammy-2c-4g'
					}

					steps {
						installEarthly()
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
						// Kubernetes logs
						sh "sudo ./build/fetch-kubernetes-logs.sh logs/${NETWORK_BACKEND}/kubernetes || true"
						archiveArtifacts artifacts: 'logs/**', allowEmptyArchive: true

						// JUnit results for Tempest
						sh "sudo ./build/fetch-junit-xml.sh tempest-${NETWORK_BACKEND}.xml || true"
						junit "tempest-${NETWORK_BACKEND}.xml"
					}
				}
			}
		}

		// promote images
		// release?
		// todo: manual pin commit to main (avoiding loop)
	}
}
