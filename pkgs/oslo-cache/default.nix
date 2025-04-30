{
  lib,
  buildPythonApplication,
  fetchFromGitea,
  pbr,
  debtcollector,
  dogpile-cache,
  oslo-config,
  oslo-i18n,
  oslo-log,
  oslo-utils,
  oslotest,
  pifpaf,
  stestr,
  pymemcache,
  python-binary-memcached,
  python-memcached,
  pymongo,
  etcd3gw,
  redis,
}:

buildPythonApplication rec {
  pname = "oslo-cache";
  version = "3.10.1";

  src = fetchFromGitea {
    domain = "opendev.org";
    owner = "openstack";
    repo = "oslo.cache";
    rev = version;
    hash = "sha256-Ydjfc/118ZOH+eLMG+RLbxYuPPvSMBXNwdEEgOrvWlA=";
  };

  env.PBR_VERSION = version;

  build-system = [
    pbr
  ];

  dependencies = [
    debtcollector
    dogpile-cache
    oslo-config
    oslo-i18n
    oslo-log
    oslo-utils
  ];

  nativeCheckInputs = [
    oslotest
    pifpaf
    stestr
    pymemcache
    python-binary-memcached
    python-memcached
    pymongo
    etcd3gw
    redis
  ];

  checkPhase = ''
    runHook preCheck
    stestr run
    runHook postCheck
  '';

  meta = with lib; {
    description = "An oslo.config enabled dogpile.cache.";
    homepage = "https://opendev.org/openstack/oslo.cache";
    license = licenses.asl20;
  };
}
