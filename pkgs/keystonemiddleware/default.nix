{
  lib,
  buildPythonApplication,
  fetchFromGitea,
  pbr,
  keystoneauth1,
  oslo-cache,
  oslo-config,
  oslo-context,
  oslo-i18n,
  oslo-log,
  oslo-serialization,
  oslo-utils,
  pycadf,
  pyjwt,
  python-keystoneclient,
  requests,
  webob,
  bandit,
  coverage,
  cryptography,
  fixtures,
  flake8-docstrings,
  hacking,
  oslo-messaging,
  oslotest,
  python-binary-memcached,
  python-memcached,
  requests-mock,
  stestr,
  stevedore,
  testresources,
  testtools,
  webtest,
}:

buildPythonApplication rec {
  pname = "keystonemiddleware";
  version = "10.9.0";

  src = fetchFromGitea {
    domain = "opendev.org";
    owner = "openstack";
    repo = "keystonemiddleware";
    rev = version;
    hash = "sha256-AOL/wcSWElZwt+40pZWllr81h9bd2F7wPL11chiet4c=";
  };

  env.PBR_VERSION = version;

  build-system = [
    pbr
  ];

  dependencies = [
    keystoneauth1
    oslo-cache
    oslo-config
    oslo-context
    oslo-i18n
    oslo-log
    oslo-serialization
    oslo-utils
    pycadf
    pyjwt
    python-keystoneclient
    requests
    webob
  ];

  nativeCheckInputs = [
    bandit
    coverage
    cryptography
    fixtures
    flake8-docstrings
    hacking
    oslo-messaging
    oslotest
    python-binary-memcached
    python-memcached
    requests-mock
    stestr
    stevedore
    testresources
    testtools
    webtest
  ];

  checkPhase = ''
    runHook preCheck
    stestr run
    runHook postCheck
  '';

  meta = with lib; {
    description = "OpenStack Identity (Keystone) Middleware";
    homepage = "https://opendev.org/openstack/keystonemiddleware";
    license = licenses.asl20;
  };
}
