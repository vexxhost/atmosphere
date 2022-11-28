# Changelog

## [0.8.1](https://github.com/vexxhost/atmosphere/compare/v0.8.0...v0.8.1) (2022-11-28)


### Bug Fixes

* switch opsgenie config variable ([377a81b](https://github.com/vexxhost/atmosphere/commit/377a81b812c6c19b5af19753960f696165bd079e))

## [0.8.0](https://github.com/vexxhost/atmosphere/compare/v0.7.0...v0.8.0) (2022-11-28)


### Features

* **opsgenie:** add integration ([ad5e265](https://github.com/vexxhost/atmosphere/commit/ad5e265891d7ed06aa2f68e8448a7b4e4d3a2994))


### Bug Fixes

* bump to ovs 2.17.3 ([d2f69ef](https://github.com/vexxhost/atmosphere/commit/d2f69ef203a3dc654f249fccd01ca15d355e4133))

## [0.7.0](https://github.com/vexxhost/atmosphere/compare/v0.6.1...v0.7.0) (2022-11-15)


### Features

* **octavia:** add role ([d8d2aa1](https://github.com/vexxhost/atmosphere/commit/d8d2aa1eb40cad5028ff2c5a8224ffd1234e0e56))


### Bug Fixes

* bump osh for ovs fixes ([1ceda87](https://github.com/vexxhost/atmosphere/commit/1ceda87baa1e5fa3099d78b3d9a7b637f8fc20ef))
* bump ovs to 2.17.0 ([dc07e23](https://github.com/vexxhost/atmosphere/commit/dc07e23e9e1c10a71e1d7bd9b7bf6d261539d9c7))
* **containerd:** bump DefaultLimitMEMLOCK to inf ([ff1980a](https://github.com/vexxhost/atmosphere/commit/ff1980a9ba5a792ef04b754de383b85769c03752)), closes [#169](https://github.com/vexxhost/atmosphere/issues/169)
* **octavia:** resolve unit tests ([d945774](https://github.com/vexxhost/atmosphere/commit/d945774c6e63c9424dc32e26c7d881a704dd8fae))
* **octavia:** switch to cert-manager issuer certs ([c582420](https://github.com/vexxhost/atmosphere/commit/c58242052e49d30d01e0beb3d4c97f6d731180b6))
* unit tests + cluster role ([4a402ab](https://github.com/vexxhost/atmosphere/commit/4a402ab35aaffee3a86c1356bf84ddd018f5b8a6))
* use correct issuer name ([e7f470a](https://github.com/vexxhost/atmosphere/commit/e7f470af16a754a7078fab9aead05d6c5253aa0a))

## [0.6.1](https://github.com/vexxhost/atmosphere/compare/v0.6.0...v0.6.1) (2022-11-10)


### Bug Fixes

* **monitoring:** correct CoreDNS selector ([92df86a](https://github.com/vexxhost/atmosphere/commit/92df86a232c8f351bee2572443b15cb7478d9841))
* **monitoring:** fix NodeLowEntropy alerts ([5d41d7f](https://github.com/vexxhost/atmosphere/commit/5d41d7f3a201f12d8d9144396a5402aef3c1575d))
* **monitoring:** resolve etcd monitoring ([ba92607](https://github.com/vexxhost/atmosphere/commit/ba9260717d2547d74f92e37130c0cff2017f81d7))

## [0.6.0](https://github.com/vexxhost/atmosphere/compare/v0.5.0...v0.6.0) (2022-11-10)


### Features

* allow for a custom cluster IP address for the neutron coredns service, with a default of '10.96.0.20' ([662866f](https://github.com/vexxhost/atmosphere/commit/662866fb56b6601bf0348428641f445604b2b3fd))
* allow for a custom ingressClassName on OpenStack component ingress objects, with a default of 'openstack' ([d8d1fde](https://github.com/vexxhost/atmosphere/commit/d8d1fde11eeb7e36eb10ec01d318af4d2a1cee71))
* **ingress:** allow overriding ingress namespace ([31e528b](https://github.com/vexxhost/atmosphere/commit/31e528b39822db1513623e3db0cc8e4fe388ebc1))
* **memcached:** allow overriding namespace ([661b0b0](https://github.com/vexxhost/atmosphere/commit/661b0b0ee56361806f3d425e047705c5c76f6be0))
* **monitoring:** add to operator ([7d3c797](https://github.com/vexxhost/atmosphere/commit/7d3c797689f60c904a7a2bc3dd923af2fe3ef379))


### Bug Fixes

* bump magnum-capi ([aeb2081](https://github.com/vexxhost/atmosphere/commit/aeb208142574a289bab4044559437fa74d1b5b4e))
* bump magnum-capi ([3d9509a](https://github.com/vexxhost/atmosphere/commit/3d9509a8a50ff1bcfe214f8584d28da6b395dfae))
* use release specific dashboard addons ([7f45988](https://github.com/vexxhost/atmosphere/commit/7f45988ebf9db38463b9e91808b498cc9072e86f))


### Documentation

* add initial ([c45b71c](https://github.com/vexxhost/atmosphere/commit/c45b71ccd350207d1486bc534607b756c654a82f))

## [0.5.0](https://github.com/vexxhost/atmosphere/compare/v0.4.1...v0.5.0) (2022-10-06)


### Features

* **ingress:** enable overriding/disabling ([e04907d](https://github.com/vexxhost/atmosphere/commit/e04907d8d80c5bae7f601acb2315d0b4553377ef))


### Documentation

* **ingress:** add initial ([c9dddd0](https://github.com/vexxhost/atmosphere/commit/c9dddd054ba3fb5035abd0f03ec6f75ef10b83ae))

## [0.4.1](https://github.com/vexxhost/atmosphere/compare/v0.4.0...v0.4.1) (2022-10-04)


### Bug Fixes

* **ingress:** point to correct tcp port ([54e074c](https://github.com/vexxhost/atmosphere/commit/54e074c1b01a3a5cac2915c459e336932fe2b137))

## [0.4.0](https://github.com/vexxhost/atmosphere/compare/v0.3.0...v0.4.0) (2022-10-02)


### Features

* **cert-manager:** migrate to operator + add docs ([57b5339](https://github.com/vexxhost/atmosphere/commit/57b5339db15b28a6d29115e04be2ef24c764ff79))


### Bug Fixes

* add cert dep on helmrelease ([3cb0041](https://github.com/vexxhost/atmosphere/commit/3cb004114f3f2dd57c706d25a60e06f584044428))
* add designate minidns to ingress ([f5ab8b5](https://github.com/vexxhost/atmosphere/commit/f5ab8b5302cc4a05f461644fddfc18469f913d76))
* **atmosphere:** typo in atmosphere_issuer_config ([625b1e4](https://github.com/vexxhost/atmosphere/commit/625b1e4e98274c1049f23abbe97c75ad7c95da79))
* **certificates:** resolve secret retrival ([8e11a31](https://github.com/vexxhost/atmosphere/commit/8e11a3179949bb0819d6f969e26e67d8992786d0))
* **certs:** resolve ansible ternary ([6e557c8](https://github.com/vexxhost/atmosphere/commit/6e557c812a9860fae78f95c6065573f8fb91fc5c))
* **endpoints:** move novnc endpoint to correct url ([b0ffc60](https://github.com/vexxhost/atmosphere/commit/b0ffc60b2e41add67f91a9eb93c5262900660ef7))
* **endpoints:** Use /vnc_lite for novnc ([aeffc1b](https://github.com/vexxhost/atmosphere/commit/aeffc1b7a2e683a16764e624753bbba9a22018bd))
* **operator:** fix load_from_file ([921aac8](https://github.com/vexxhost/atmosphere/commit/921aac854ca2b6c9d0d86660fa3a6f1d1ce495ea))
* **operator:** openstack_cli deployment ([76605b1](https://github.com/vexxhost/atmosphere/commit/76605b1726bd532fd67733be04897505d75cf2fb))

## [0.3.0](https://github.com/vexxhost/atmosphere/compare/v0.2.2...v0.3.0) (2022-09-28)


### Features

* **ingress:** move to operator ([46475f8](https://github.com/vexxhost/atmosphere/commit/46475f8c98d538d8c194ba9de8b9b926a50193d2))

## [0.2.2](https://github.com/vexxhost/atmosphere/compare/v0.2.1...v0.2.2) (2022-09-27)


### Bug Fixes

* **memcached:** add protocol to service ([c252a9b](https://github.com/vexxhost/atmosphere/commit/c252a9b0db0d61a4745c4177c378d83232fa5c4c))

## [0.2.1](https://github.com/vexxhost/atmosphere/compare/v0.2.0...v0.2.1) (2022-09-27)


### Bug Fixes

* **rabbitmq:** drop terminationGracePeriodSeconds down ([f791801](https://github.com/vexxhost/atmosphere/commit/f791801625f30ae01d457a00cf223565261ec1b4))

## [0.2.0](https://github.com/vexxhost/atmosphere/compare/v0.1.1...v0.2.0) (2022-09-27)


### Features

* migrate cert-mgr + rmq to operator ([e1e1ae4](https://github.com/vexxhost/atmosphere/commit/e1e1ae4075bef7fec6668b5a10e1e847d2a9ff48))
* move pxc to operator ([bdb9774](https://github.com/vexxhost/atmosphere/commit/bdb9774bed5e819a19199bfc6b6f82643c22d6b1))
* move rmq to operator ([196945a](https://github.com/vexxhost/atmosphere/commit/196945a07fc381ca178d0cfab4c42e3500564d3c))
* use server-side apply ([2222854](https://github.com/vexxhost/atmosphere/commit/2222854a76cc4d778ccf092d0ada985ddc7feb18))


### Bug Fixes

* add services to cluster role ([168c264](https://github.com/vexxhost/atmosphere/commit/168c2649d2d5e1184cddae93fac82ca508409f25))
* avoid race condition with csi not up ([2621136](https://github.com/vexxhost/atmosphere/commit/2621136bce9d453d41353acbd653679cb3de0683))
* bump timeout to 300s ([ac0d453](https://github.com/vexxhost/atmosphere/commit/ac0d45336a5510a2dfe65597693adedb18a059b9))
* increase wait timeout ([3ffc33e](https://github.com/vexxhost/atmosphere/commit/3ffc33e751b56fcc632f64afe34e67529da436ce))
* move memcached to operator ([e48a677](https://github.com/vexxhost/atmosphere/commit/e48a6779969e9ad829d9d4366853db0fa5b9be7b))
* slow down API polls ([da561e3](https://github.com/vexxhost/atmosphere/commit/da561e36bcb5f32f3565a3f490fa41d86801e746))
* solve config.toml rendering ([40e63b1](https://github.com/vexxhost/atmosphere/commit/40e63b10f084288e921975825c1f869127620834))
* solve ingress race conditions ([ff5e860](https://github.com/vexxhost/atmosphere/commit/ff5e86011cfdad85af2b4c46931e74358b93af27))
* solve update_object for svc ([3e66870](https://github.com/vexxhost/atmosphere/commit/3e668702b16c6e6eb206b769a98c2332b0b97ecc))
* update role to create pxc ([6203025](https://github.com/vexxhost/atmosphere/commit/6203025ffef4cdc2f55ff2960dbc95475272685f))

## [0.1.1](https://github.com/vexxhost/atmosphere/compare/v0.1.0...v0.1.1) (2022-09-21)


### Bug Fixes

* galaxy.yml metadata ([7505359](https://github.com/vexxhost/atmosphere/commit/7505359ad515ac55e194f20573621e6ffebc4802))

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
