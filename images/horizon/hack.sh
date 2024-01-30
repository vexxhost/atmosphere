#!/bin/bash
set -ex
SITE_PACKAGES_ROOT=$(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")
rm -f ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/local_settings.py
ln -s /etc/openstack-dashboard/local_settings ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/local_settings.py

cp -r ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled /tmp/enabled

PANEL_DIR="${SITE_PACKAGES_ROOT}/designatedashboard/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/designatedashboard/local/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/heat_dashboard/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/heat_dashboard/local/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/ironic_ui/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/ironic_ui/local/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/magnum_ui/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/magnum_ui/local/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/manila_ui/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/manila_ui/local/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/monitoring/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/monitoring/local/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/neutron_vpnaas_dashboard/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/neutron_vpnaas_dashboard/local/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/octavia_dashboard/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/octavia_dashboard/local/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/senlin_dashboard/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR
PANEL_DIR="${SITE_PACKAGES_ROOT}/senlin_dashboard/local/enabled"
if [ -d ${PANEL_DIR} ];then
  for panel in `ls -1 ${PANEL_DIR}/_[1-9]*.py`
  do
    ln -s ${panel} ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled/$(basename ${panel})
  done
fi
unset PANEL_DIR

/manage.py collectstatic --noinput
/manage.py compress --force
rm -f /etc/openstack-dashboard/local_settings
rm -rf ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled
cp -r /tmp/enabled ${SITE_PACKAGES_ROOT}/openstack_dashboard/local/enabled
