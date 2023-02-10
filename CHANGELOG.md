# Changelog

## [1.0.0-rc.1](https://github.com/vexxhost/atmosphere/compare/v0.13.0...v1.0.0-rc.1) (2023-02-03)


### Features

* add ability to sync charts + use offline install for pxc-operator ([e04accd](https://github.com/vexxhost/atmosphere/commit/e04accd8b0c2a1e860f2735ebb77596eb84f83b7))
* add openstack_helm_image_tags filter ([427f6aa](https://github.com/vexxhost/atmosphere/commit/427f6aa474cda7fe677c94d315e79a377eaccb34))
* added docker_image filter + image_list in ansible ([21d5581](https://github.com/vexxhost/atmosphere/commit/21d55818dd6200202f35aec792d52e2f756bcbdd))
* added playbook to suspend project ([707e65b](https://github.com/vexxhost/atmosphere/commit/707e65b2596ca525809e96068492013d874f069e))
* Install Magnum client ([#268](https://github.com/vexxhost/atmosphere/issues/268)) ([5908fb8](https://github.com/vexxhost/atmosphere/commit/5908fb80453b203aadc5ab0dad6f92f3e0f2ec66))
* move cilium to offline install ([c397259](https://github.com/vexxhost/atmosphere/commit/c397259113609aa3cd833ab3510027acc6ec5c04))
* move to image_manifest ([fef44b1](https://github.com/vexxhost/atmosphere/commit/fef44b129da22d3c4153a28dd4620dbb463fcba7))
* Set retries of helmreleases ([#253](https://github.com/vexxhost/atmosphere/issues/253)) ([9bcc2a0](https://github.com/vexxhost/atmosphere/commit/9bcc2a04102b5bd86e67ceafbf7596c149b3fa37))
* Support coredns offline-install ([ceff992](https://github.com/vexxhost/atmosphere/commit/ceff99247ed2deb3fd58bb61c62ca2003b562796))


### Bug Fixes

* add ansible-based ingress ([b07e905](https://github.com/vexxhost/atmosphere/commit/b07e9058c2bce9c3026d96d114354380de4c5eea))
* Add bmemcached ([98aedb6](https://github.com/vexxhost/atmosphere/commit/98aedb67971be355a2d28c67c9c547afea8934b9))
* add ingress for magnum ([4c33bb5](https://github.com/vexxhost/atmosphere/commit/4c33bb5b75a752805ca970084cc40d2f49d2ac13))
* Add missing images for mirroring ([#265](https://github.com/vexxhost/atmosphere/issues/265)) ([271d9de](https://github.com/vexxhost/atmosphere/commit/271d9de70ceeec5477e66d460c34bd63aed47eb4))
* Deploy cni before flux ([16e0492](https://github.com/vexxhost/atmosphere/commit/16e0492bd8439a91a37003ebfdad64cd24209af5))
* drop un-used openstack_helm_endpoints_repo_url ([1fe6c6c](https://github.com/vexxhost/atmosphere/commit/1fe6c6cd0ced627711a7b41cfea143beb6ad0d7b))
* enforce cri-tools version ([b19a631](https://github.com/vexxhost/atmosphere/commit/b19a631bb79c62d7f49473bdb3c191401c3b0bff))
* Fix ansible var names for helm value overrides ([789b174](https://github.com/vexxhost/atmosphere/commit/789b174643a6bc61978492148ed320b0ef87528f))
* fix correct value for container_infra in horizon ([2b8a46f](https://github.com/vexxhost/atmosphere/commit/2b8a46f5642dc5f71112665427af0036b781fd96))
* Fix pre-commit error because of deps conflict ([5298740](https://github.com/vexxhost/atmosphere/commit/5298740ac45cb1b2dcda32e4bc9f8c86baba69e9))
* Fix tempest helm values var name ([495bf00](https://github.com/vexxhost/atmosphere/commit/495bf004cc51e23fe0188c0d07198fdc3fef4c59))
* Fix test failures ([6ffcda5](https://github.com/vexxhost/atmosphere/commit/6ffcda54d92b6237cfe3c8df486edd1a0ea2bc37))
* Fix the condition if atmosphere_image_repository is defined in flux role ([81cf6ab](https://github.com/vexxhost/atmosphere/commit/81cf6ab8541633272cdac0d48ba456482f9969ed))
* flush handlers after installing ca certs ([cf8424d](https://github.com/vexxhost/atmosphere/commit/cf8424d7fef7246f6e4c23be52b02e10c1d01659))
* install flux early ([81ea080](https://github.com/vexxhost/atmosphere/commit/81ea08087980d629c319d7d42220da19d9f1b51c))
* **magnum:** drop hard-coded storage class ([885b53f](https://github.com/vexxhost/atmosphere/commit/885b53f0a7b1035e3d4efbeb8bc02db20f4900f5))
* **magnum:** load registry correctly ([756b717](https://github.com/vexxhost/atmosphere/commit/756b71700918ca69b652279a0e3253b418799e30))
* move ceph_csi_rbd to offline-install ([90f91b3](https://github.com/vexxhost/atmosphere/commit/90f91b3dda9fed24bad292cf232cce9259d70635))
* move pxc to role and allow overriding ([6aa0b91](https://github.com/vexxhost/atmosphere/commit/6aa0b91db2416120784a2225c94449873f404bcf))
* **nfd:** use correct vars ([512c173](https://github.com/vexxhost/atmosphere/commit/512c173b672b6b3ba9a29d162ff529446b396bf8))
* resolve json parsing ([69868be](https://github.com/vexxhost/atmosphere/commit/69868bec5d84b7e5214f442ee8ee5c8d45f5ec61))
* restore openstacksdk ([34db5a4](https://github.com/vexxhost/atmosphere/commit/34db5a49faf7e6c760f8a28da23b9de4ec609213))
* Revert issuer config for molecule deployment ([168b177](https://github.com/vexxhost/atmosphere/commit/168b1775516f106f379322954cf5d97f2e23f742))
* Revert openstack_helm_barbican_kek var in barbican role ([5d7f71f](https://github.com/vexxhost/atmosphere/commit/5d7f71f004dc24fe5e93deb22769a6adf76ffd3c))
* Specify the gallaxy collection for the filter. ([#270](https://github.com/vexxhost/atmosphere/issues/270)) ([60d09f9](https://github.com/vexxhost/atmosphere/commit/60d09f9b02141f486cd362a3d9c49159d8edfae4))
* sync charts + add hooks for cinder ([feec995](https://github.com/vexxhost/atmosphere/commit/feec9959d6f4c8c8cc6b681f074f640d502638f7))
* Synchronize files based on checksum in upload_helm_chart role ([8974d07](https://github.com/vexxhost/atmosphere/commit/8974d079d1843a24c330d13aa40a5747dd79cf7c))
* update k8s gpg key ([65eb66e](https://github.com/vexxhost/atmosphere/commit/65eb66ec6ec279f2320aeb67dc9ad7cd56a75a27))
* use atmosphere_images for an image manifest ([8b5c306](https://github.com/vexxhost/atmosphere/commit/8b5c30614acfc0d58150a90e89d73d6ddfceb47c))
* use cacert for self-signed or custom ca ([0148f7b](https://github.com/vexxhost/atmosphere/commit/0148f7b65cef5fdb17f38d481993054eb5eb6046))
* Use default imagePullPolicy in openstack-helm, i.e. IfNotPresent ([03b4120](https://github.com/vexxhost/atmosphere/commit/03b412013578fecc8d81dd4cf024f4e24ff107f2))
* use offline deploy for magnum ([fef6942](https://github.com/vexxhost/atmosphere/commit/fef6942b8a3e2053e9f144b15ddf700e1f2dbe6b))


### Documentation

* add details for backups ([58c23fd](https://github.com/vexxhost/atmosphere/commit/58c23fd591ac42d4b1ca3c81c323f707b1321e21))
* add external ceph backup docs ([0c9c70e](https://github.com/vexxhost/atmosphere/commit/0c9c70e5f119f6797ff9a086d97487190e9223c3))
* added ref to backups ([4c29e55](https://github.com/vexxhost/atmosphere/commit/4c29e559485b77bf8a2894b13194d25ecbdbbef1))
* fix typo in cinder docs ([278bc71](https://github.com/vexxhost/atmosphere/commit/278bc7119f499bbea6c6038e2b63c18b50213362))
* refactor pxc backup docs ([e48be3a](https://github.com/vexxhost/atmosphere/commit/e48be3a2beaa194aedc1e05b085dbc6ff365bbe8))


### Miscellaneous Chores

* release 1.0.0-rc.1 ([d4cbf73](https://github.com/vexxhost/atmosphere/commit/d4cbf733ab1b6c28c10211e36968307647543ee8))

## [0.13.0](https://github.com/vexxhost/atmosphere/compare/v0.12.0...v0.13.0) (2022-12-28)


### Features

* allow for custom registry ([71ebfe8](https://github.com/vexxhost/atmosphere/commit/71ebfe89536fad3f6aabaf83309499298449c373))


### Bug Fixes

* Ignore unrechable hosts error in log capture playbook of molecule destroy ([76e81f8](https://github.com/vexxhost/atmosphere/commit/76e81f83f6a958653fe7794e88fedaebac2ae646))

## [0.12.0](https://github.com/vexxhost/atmosphere/compare/v0.11.0...v0.12.0) (2022-12-19)


### Features

* allow cloud spec overrides ([d469eb6](https://github.com/vexxhost/atmosphere/commit/d469eb63f6a95c7dea204799c4e693ec4ab24bb0)), closes [#231](https://github.com/vexxhost/atmosphere/issues/231)


### Bug Fixes

* bump rabbitmq operator version ([a0874ad](https://github.com/vexxhost/atmosphere/commit/a0874ada6ccdc4e5967b0e11d72d52c7a0ff230e))
* Correct task "Upload logs to object storage" ([7d40bf2](https://github.com/vexxhost/atmosphere/commit/7d40bf291cb82f8981156dd6d0ef3f45bed439ea))
* solve typo in atmosphere_cloud_spec ([0aecdae](https://github.com/vexxhost/atmosphere/commit/0aecdaee1102b4e6d18f2019ada512019a1368ad))

## [0.11.0](https://github.com/vexxhost/atmosphere/compare/v0.10.0...v0.11.0) (2022-12-15)


### Features

* add cloud resource + magnum ([#217](https://github.com/vexxhost/atmosphere/issues/217)) ([096ade0](https://github.com/vexxhost/atmosphere/commit/096ade0076a386aa64b5f3c0884be8f4643216ad))

## [0.10.0](https://github.com/vexxhost/atmosphere/compare/v0.9.0...v0.10.0) (2022-12-13)


### Features

* add endpoint, implied_role, role & service ([84ba2ec](https://github.com/vexxhost/atmosphere/commit/84ba2ec5a37957d9501e18491f5c0c6900fa2125))
* enable rbd write-back cache ([1e3180b](https://github.com/vexxhost/atmosphere/commit/1e3180b0ccadb5bdcb71d5a5f5da2056791a22a3))


### Bug Fixes

* Add masquerade rule in molecule env ([50bbcf0](https://github.com/vexxhost/atmosphere/commit/50bbcf0bbfc1864176f1979c2e9f7ccc94c0c0ed))
* install crds before resources ([d886654](https://github.com/vexxhost/atmosphere/commit/d886654aea06bc23262eada9368f9b075699f068))
* **keystone:** add updated libapache-mod-oauth2 ([a99d799](https://github.com/vexxhost/atmosphere/commit/a99d7997ecd590ba1bafe2f8411dd2d490405b9c))
* **keystone:** clean up after ourselves in images ([19b2032](https://github.com/vexxhost/atmosphere/commit/19b20324ffbe69f59fa6d8de234552e62cd9bb1a))
* **keystone:** install openidc only ([8fd074e](https://github.com/vexxhost/atmosphere/commit/8fd074ef873f7996e4806e9cf1a17099c1da6a70))
* move arg up ([8856fb1](https://github.com/vexxhost/atmosphere/commit/8856fb196293aa90deb315561c7268c76c95e649))
* **operator:** stop validating resources ([90e2c2a](https://github.com/vexxhost/atmosphere/commit/90e2c2acb0434fbc3123a7178f92ab0c6da1b60b))
* resolve if statement ([686e5c4](https://github.com/vexxhost/atmosphere/commit/686e5c4b4067915521a308e8358a271c35e59065))
* use correct base image ([67abe6a](https://github.com/vexxhost/atmosphere/commit/67abe6a22b9998ddfc9bda10286b94f8b6d15f7e))
* use correct builder image ([19c4e4e](https://github.com/vexxhost/atmosphere/commit/19c4e4e5716c1b7f4d08e122760bb03a725cdf09))
* use runtime image ([1ff73d7](https://github.com/vexxhost/atmosphere/commit/1ff73d766d72a868c8ac86db9b2d69345738a73e))


### Documentation

* clean-up rbd persistent cache ([90afb1d](https://github.com/vexxhost/atmosphere/commit/90afb1dd42ab5fa77b8decb31e46e3772b4f6465))
* **monitoring:** add info how to expose ([431ab87](https://github.com/vexxhost/atmosphere/commit/431ab87e61a2029952d22e0151b309b3c2e5ef00))

## [0.9.0](https://github.com/vexxhost/atmosphere/compare/v0.8.1...v0.9.0) (2022-11-29)


### Features

* allow for custom clusterissuer and certificate secretName when atmosphere is not responsible for cert-manager. ([fa960d4](https://github.com/vexxhost/atmosphere/commit/fa960d40c93bfcd17d5af2b6f5405ce174b193a2))


### Bug Fixes

* **monitoring:** enable openstack exporter ([b77cea1](https://github.com/vexxhost/atmosphere/commit/b77cea160393211c65df7afa5db564ba2b1666c7))
* **openstack-exporter:** solve containerPort issues ([c90235e](https://github.com/vexxhost/atmosphere/commit/c90235ea57bd01b1f833315397b0fdd8157296fb))
* **opsgenie:** adjust severity levels ([b26524f](https://github.com/vexxhost/atmosphere/commit/b26524fbefe1fe9829614cb35c21cf8e0acbf7bb))


### Documentation

* basic etcdDatabaseHighFragmentationRatio response ([5af93c0](https://github.com/vexxhost/atmosphere/commit/5af93c07716972c9039bc9158aaf6c02f808f80d))

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
