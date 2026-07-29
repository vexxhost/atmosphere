# `glance`

This role deploys the OpenStack Image service using the vendored Glance Helm
chart. It also configures the service endpoints and image storage integration.
Configured images are imported after the service becomes available.
Image definitions are supplied through the `glance_images` role variable.
