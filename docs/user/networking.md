# Networking

## Hardware Acceleration

### SR-IOV

#### BIOS configuration

Depending on your hardware, you may need to enable a few options in the BIOS
in order to get SR-IOV working.  You should consult with your hardware vendor
to ensure that you have all the options but you can use the following as a
guideline.

##### Supermicro

You need to make sure that you have the latest BIOS installed on your system
and that you have the following options enabled:

* Advanced > CPU configuration > SVM Mode > Enabled
* Advanced > NB Configuration > ACS Enable > Enabled
* Advanced > NB Configuration > IOMMU > Enabled
* Advanced > PCIe/PCI/PnP Configuration > SR-IOV Support > Enabled

Additionally, if you're using a H12/H11 series motherboard with Rome
CPU (EPYC 7xx2):

* Advanced > ACPI settings > PCI AER Support > Enabled 

#### NIC configuration

In order to get started with SR-IOV, you must first enable it in the NIC's
configuration.  As a general rule, need to make sure to enable a few things:

* Enable Intel VT-d or AMD-Vi in the BIOS
* Enable vendor-specific `iommu` in GRUB by appending to `/etc/default/grub`

  For systems with Intel CPUs:
  ```console
  GRUB_CMDLINE_LINUX="... iommu=pt intel_iommu=on"
  ```

  For systems with AMD CPUs:
  ```console
  GRUB_CMDLINE_LINUX="... iommu=pt amd_iommu=on"
  ```

  Once that change is done, you will need to run `update-grub` and restart
  your system.

##### Mellanox

In order to enable SR-IOV for Mellanox NICs, the following steps must be taken:

1. Install the `mstflint` tools on the compute node which will be used:

   ```bash
   sudo apt-get install mstflint
   ```

1. Get the device's PCI by using `lspci`.

   ```console
   $ lspci | grep Mellanox
   61:00.0 Ethernet controller: Mellanox Technologies MT2892 Family [ConnectX-6 Dx]
   61:00.1 Ethernet controller: Mellanox Technologies MT2892 Family [ConnectX-6 Dx]
   ```

1. Check if SR-IOV is enabled in the firmware

   ```console
   $ sudo mstconfig -d 61:00.0 q | grep SRIOV_EN
        SRIOV_EN                            True(1)
   ```

   If SR-IOV is not enabled, you can enable it with the following command:

   ```console
   $ sudo mstconfig -d 61:00.0 set SRIOV_EN=1
   ```

1. Configure the needed number of VFs

   ```console
   $ sudo mstconfig -d 61:00.0 set NUM_OF_VFS=16
   ```

1. Restart the system

   !!! note

   A useful tip is to prefix this command with an extra space (before `sudo`),
   so that it is not saved in the shell history and prevents accidental reboot.

   ```console
   $ sudo reboot
   ```

### Mellanox Accelerated Switching And Packet Processing (ASAP2)

Mellanox ASAP2 is a technology that enables the offloading of the Open vSwitch
datapath to the NIC. This offloading is done by the NIC's firmware, and is
transparent to the host.

#### NIC configuration

One of the dependencies of ASAP2 is SR-IOV, so you must follow the steps above
to configure your Mellanox NIC for SR-IOV.  There is work pending inside
Atmosphere to natively integrate this however for the meantime you must create
a script to configure the NIC for ASAP2.

```shell
#!/bin/bash -xe

PF=$1
NUM_VFS=16

# Detect PCI address of the PF
PCI_ADDR=`grep PCI_SLOT_NAME /sys/class/net/$PF/device/uevent | sed 's:.*PCI_SLOT_NAME=::'`

# Set the number of VFs
echo $NUM_VFS > /sys/class/net/$PF/device/sriov_numvfs

# Unbind all of the VFs from the PF driver
for VF in `grep PCI_SLOT_NAME /sys/class/net/$PF/device/virtfn*/uevent | cut -d'=' -f2`; do
  echo $VF > /sys/bus/pci/drivers/mlx5_core/unbind
done

# Switch to "switchdev" mode
echo "Setting $PF to switchdev mode"
devlink dev eswitch set pci/$PCI_ADDR mode switchdev

# Enable hardware offloads
ethtool -K $PF hw-tc-offload on

# Bind the VFs to the mlx5_core driver
for VF in `grep PCI_SLOT_NAME /sys/class/net/$PF/device/virtfn*/uevent | cut -d'=' -f2`; do
  echo $VF > /sys/bus/pci/drivers/mlx5_core/bind
done
```

Once that is done, you'll have to enable hardware offloading and tuning the
aging time inside Open vSwitch by running the following:

```console
$ kubectl -n openstack exec openvswitch-<POD_ID> -- ovs-vsctl set Open_vSwitch . other_config:hw-offload=true
$ kubectl -n openstack exec openvswitch-<POD_ID> -- ovs-vsctl set Open_vSwitch . other_config:max-idle=30000
```

