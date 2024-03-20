pipeline {
  agent none

  options {
    disableConcurrentBuilds(abortPrevious: true);
  }

  // TODO: periodic multi-node jobs

  environment {
    EARTHLY_CI = 'true'
  }

  stages {
    stage('lint') {
      parallel {
        stage('ansible-lint') {
          agent {
            label 'earthly-2c-4g'
          }

          steps {
            sh 'earthly --output +lint.ansible-lint'
          }

          post {
            always {
              junit testResults: 'ansible-lint.xml', allowEmptyResults: true
            }
          }
        }

        stage('markdownlint') {
          agent {
            label 'earthly-2c-4g'
          }

          steps {
            sh 'earthly --output +lint.markdownlint'
          }

          post {
            always {
              junit testResults: 'junit.xml', allowEmptyResults: true
            }
          }
        }
      }
    }

    stage('unit') {
      agent {
        label 'earthly-2c-4g'
      }

      steps {
        sh 'earthly --output +unit.go'
      }

      post {
        always {
          junit 'junit-go.xml'
        }
      }
    }

    stage('build') {
      parallel {
        stage('collection') {
          agent {
            label 'earthly-2c-4g'
          }

          steps {
            sh 'earthly --output +build.collection'
          }

          post {
            success {
              archiveArtifacts artifacts: 'dist/**'
            }
          }
        }

        stage('images') {
          agent {
            label 'earthly'
          }

          environment {
            TEST_REGISTRY = "registry.atmosphere.dev/builds/${env.BRANCH_NAME.toLowerCase()}"
            PROD_REGISTRY = "ghcr.io/vexxhost/atmosphere"
            REGISTRY = "${env.BRANCH_NAME == 'main' ? PROD_REGISTRY : TEST_REGISTRY}"

            EARTHLY_BUILD_ARGS = "REGISTRY=${REGISTRY}"
            EARTHLY_PUSH = "true"
          }

          steps {
            script {
              if (env.BRANCH_NAME == 'main') {
                docker.withRegistry('https://ghcr.io', 'github-packages-token') {
                  sh 'earthly --push +images'
                }
              } else {
                docker.withRegistry('https://registry.atmosphere.dev', 'harbor-registry') {
                  sh 'earthly --push +images'
                }
              }
            }

            sh 'earthly --output +pin-images'
            sh 'earthly +scan-images'
            stash name: 'src-with-pinned-images', includes: '**'
          }
        }

        stage('docs') {
          agent {
            label 'earthly-2c-4g'
          }

          steps {
            sh 'earthly +mkdocs-build'
          }
        }
      }
    }

    stage('integration') {
      matrix {
        axes {
          axis {
            name 'SCENARIO'
            values 'openvswitch', 'ovn', 'keycloak'
          }
        }

        agent {
          label 'jammy-16c-64g'
        }

        environment {
          ATMOSPHERE_DEBUG = "true"
          ATMOSPHERE_NETWORK_BACKEND = "${SCENARIO}"

          // NOTE(mnaser): OVN is currently unstable and we don't want it to mark builds as failed.
          BUILD_RESULT_ON_FAILURE = "${SCENARIO == 'ovn' ? 'SUCCESS' : 'FAILURE'}"
          STAGE_RESULT_ON_FAILURE = "${SCENARIO == 'ovn' ? 'UNSTABLE' : 'FAILURE'}"
        }

        stages {
          stage('keycloak') {
            when { expression { env.SCENARIO == "keycloak" } }
            steps {
              // Checkout code with built/pinned images
              unstash 'src-with-pinned-images'

              // Install dependencies
              sh 'sudo apt-get install -y git python3-pip docker.io'
              sh 'sudo pip install poetry'
              sh 'sudo poetry install --with dev'
              sh 'sudo poetry run molecule test -s keycloak'
            }
            post {
              always {
                // Kubernetes logs
                sh "sudo ./build/fetch-kubernetes-logs.sh logs/${SCENARIO}/kubernetes || true"
                archiveArtifacts artifacts: 'logs/**', allowEmptyArchive: true
              }
            }
          }
          stage('molecule') {
            when { expression { env.SCENARIO != "keycloak" } }
            steps {
              // Checkout code with built/pinned images
              unstash 'src-with-pinned-images'

              // Install dependencies
              sh 'sudo apt-get install -y git python3-pip'
              sh 'sudo pip install poetry'
              sh 'sudo poetry install --with dev'

              catchError(buildResult: "${BUILD_RESULT_ON_FAILURE}", stageResult: "${STAGE_RESULT_ON_FAILURE}") {
                sh 'sudo --preserve-env=ATMOSPHERE_DEBUG,ATMOSPHERE_NETWORK_BACKEND poetry run molecule test -s aio'
              }
            }
            post {
              always {
                // Kubernetes logs
                sh "sudo ./build/fetch-kubernetes-logs.sh logs/${SCENARIO}/kubernetes || true"
                archiveArtifacts artifacts: 'logs/**', allowEmptyArchive: true

                // JUnit results for Tempest
                sh "sudo ./build/fetch-junit-xml.sh tempest-${SCENARIO}.xml || true"
                junit "tempest-${SCENARIO}.xml"
              }
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
