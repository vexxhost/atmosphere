# Changelog

## 0.1.0 (2022-09-21)


### Features

* add simple controller to generate helm values ([12676ed](https://github.com/vexxhost/atmosphere/commit/12676edad82b187b1b2339a3c8f3d64cf5a3b006))
* add value overrides ([0f98213](https://github.com/vexxhost/atmosphere/commit/0f982131350a65dc36d6da5ec9b2e8c60070dea7))
* added operator role ([edc9b87](https://github.com/vexxhost/atmosphere/commit/edc9b87bd580b276bd49448a664a808a819db718))
* clean-up more code for helm repos ([64da5c6](https://github.com/vexxhost/atmosphere/commit/64da5c6b3ac4c2898b145b38bfc64baa0eb552a2))
* **ethtool:** add automatic tuning ([64f84a4](https://github.com/vexxhost/atmosphere/commit/64f84a4f016d33687a1c5d59d000a1113a9aaa40))
* **ethtool:** add initial commit ([34c5b53](https://github.com/vexxhost/atmosphere/commit/34c5b5341ceceeb14f6510fd66f28249c8a2db9b))
* **ethtool:** add podmonitor + basic rules ([b529c33](https://github.com/vexxhost/atmosphere/commit/b529c33e7917ce206099eb2134da5948b5828c47))
* **ethtool:** faster convergence + multiarch image ([25e5f6c](https://github.com/vexxhost/atmosphere/commit/25e5f6c075c31ac87a60e7eb4d542665749faacb))
* move nfd to operator ([52f3feb](https://github.com/vexxhost/atmosphere/commit/52f3feb3562e42904c4bb2e40331461e1abd5a7f))
* switch openstack-helm-infra to atmosphere ([313085b](https://github.com/vexxhost/atmosphere/commit/313085b210532d850c179edf368c8a7beff93b76))


### Bug Fixes

* add helmrelease to cluster role ([4787745](https://github.com/vexxhost/atmosphere/commit/4787745e9ebb23956b0e8d87e9548e953936c3dc))
* add novnc to nova images ([5a4eb80](https://github.com/vexxhost/atmosphere/commit/5a4eb80f73307a3ccab30dd7aa329171cb08cabe))
* commit time ([501dc41](https://github.com/vexxhost/atmosphere/commit/501dc41fd86deeaf67aabdc23a6540f18c6584d0))
* drop extra var ([64b555b](https://github.com/vexxhost/atmosphere/commit/64b555b7b4a8e602d138ab3fe3014843ed3dd0c1))
* enable glance with cinder ([01c78ca](https://github.com/vexxhost/atmosphere/commit/01c78ca2d0e6dc6902bccdc244161a355bf51ee3))
* **ethtool:** add variable for image tag ([29d7134](https://github.com/vexxhost/atmosphere/commit/29d7134e4ed1349f95705037b6065ca1754e9600))
* **ethtool:** fix linting for ethtool ([1f75624](https://github.com/vexxhost/atmosphere/commit/1f7562437962d3153355cc90f3729daa4904a7aa))
* fix tomli import ([50483b4](https://github.com/vexxhost/atmosphere/commit/50483b477b32a88bf852b212d1f7a8dda66472af))
* **glance:** switch to using cinder internal url ([602b116](https://github.com/vexxhost/atmosphere/commit/602b116aebef603b2b87d7bed7daa9e82f4c105a))
* **glance:** use updated image ([5e5de25](https://github.com/vexxhost/atmosphere/commit/5e5de25b8fc618cee8f5b98e68790e512d450f1f))
* improper role permissions ([da4016b](https://github.com/vexxhost/atmosphere/commit/da4016b77b1e4628ec432674fe6cd97a7ec5e81e))
* iscsi/fc for cinder/nova ([fdc71b7](https://github.com/vexxhost/atmosphere/commit/fdc71b73b6ef532a57d8f40472bdde5619a4d799))
* **metrics:** don't wait for entire helmrelease, just deployment ([2a8ce6a](https://github.com/vexxhost/atmosphere/commit/2a8ce6a4011f3e32b48d38b42211181d40be8e99))
* point to v5 api for git ([98ec126](https://github.com/vexxhost/atmosphere/commit/98ec12632fbc8a7bedba1d82957fb5da9d3723af))
* retry flavor creation in ci ([6f85b3a](https://github.com/vexxhost/atmosphere/commit/6f85b3ad2d624b4c6c89c515cb60cdc4879ecd5b))
* stop waiting for kube-prometheus-stack ([b8d3432](https://github.com/vexxhost/atmosphere/commit/b8d34325c00c8f039bc137ba60ebc446bbabe95c))
* switch openstack-exporter to new image repo ([6e24e87](https://github.com/vexxhost/atmosphere/commit/6e24e87d02ad9878db45bed5743f1cdd142f8762))
* use tomli ([ea2e521](https://github.com/vexxhost/atmosphere/commit/ea2e5211c1f1e22c3f2c7504f9cc3aa95a649418))


### Documentation

* add powerstore for nova ([8539edc](https://github.com/vexxhost/atmosphere/commit/8539edcb3cf152b873945e9989c33c7812d5b524))
* update powerstore ([d4098be](https://github.com/vexxhost/atmosphere/commit/d4098bed63f0caed8c5246c668b9a476b9a3b661))
