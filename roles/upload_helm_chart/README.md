# `upload_helm_chart`

This role takes a Helm chart and uploads it from Atmosphere to the remote
system which is running the Helm commands.

Since we bundle all of the Helm charts into the Ansible collection, we need
to upload the chart to the remote system before we can install it.
