# `magnum_pre`

This role uploads Glance images for Magnum. It runs in parallel with the
main `magnum` role during deployment to overlap image downloads with the
Helm install.
