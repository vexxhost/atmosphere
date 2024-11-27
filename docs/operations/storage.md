# Replace Ceph OSD drive

To replace OSD storage drive and reuse same OSD number, you can consider
following workflow.

## Identify which drive

To identify which hard drive the OSD is using.

Use `ceph osd find` command to locate which host that OSD is running on.

```shell
ceph osd find osd.XX
```

Once you have the host information, access into that host and run this
command to check what device that OSD is using:

```shell
ceph-volume lvm list
```

Finally find the Serial number of that specific device.
For example if your device type is nvme,
use commands like `nvme list` to locate the device and its SN.

Now you should have the location of the drive you're target to replace.

## Prepare the OSD drive for replace

Few step to prepare Ceph OSD for the drive replacement.

On Ceph controller side:

```shell
ceph osd set noout
```

Stop OSD on that Ceph host side:

```shell
systemctl stop ceph-osd@XX
```

And back on Ceph controller side:

```shell
ceph osd destroy {OSD_ID} --yes-i-really-mean-it
```

You might want to use `ceph -s` to check any ceph step, and make sure
all goes accordingly.

And now access to IPMI of the host. Compare the drive SN number we got
and eject the slot of that drive.

Use `dmesg` to make sure the drive does get ejected.
Now you are all good to replace that drive.
Also a good hobit at this point to confirm that the drive is visibly
different, so we can make sure we don't replace the wrong drive.

## Add OSD back

### Check the drive status

Once the drvie is replaced, Use tool like `dmesg` and `fdisk -l` to check
what drive is inserted, and make sure it's a success insert to the
Operating System before we added it back to Ceph.

### Add it back to Ceph

Now, you should have the device path of that drive in System.
use it on the OSD host with command:

```shell
ceph-volume lvm create --osd-id {OSD_ID} --data  /dev/nvmeXXX
```

And back to Ceph controller:

```shell
ceph osd unset noout
```

Finally, check the OSD status with command like
`ceph osd df tree` and `ceph-volume lvm list`.

At this point, if OSD successfully added back. Ceph will start
backfilling data.
Keep watching with `ceph -s` and make sure the process goes well.
