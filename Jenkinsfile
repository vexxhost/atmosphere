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

    // promote images
    // release?
    // todo: manual pin commit to main (avoiding loop)
  }
}
