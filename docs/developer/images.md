# Images

The images are built using Earthly and the contents of these files are all
located in the `images/` directory.

## Adding Gerrit packages

If you need to cherry-pick a specific Gerrit patch, you can use the following
command to download and extract the patch:

```bash
earthly ./images+fetch-gerrit-patch \
  --IMAGE keystone \
  --CHANGE 893737
```
