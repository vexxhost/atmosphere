# `glance_images` role

Uploads Glance images defined in `glance_images` (see `glance` role
defaults). Split out from the main `glance` role so that downstream
services (Nova, Magnum, etc.) only wait for the Glance API to be
deployed and not for image downloads to finish.
