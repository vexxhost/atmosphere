{
  lib,
  pkgs,
  buildPythonApplication,
  fetchFromGitea,
  pbr,
  requests,
  futurist,
  coverage,
  hacking,
  oslotest,
  pifpaf,
  pytest,
  python-subunit,
  testrepository,
  testscenarios,
  testtools,
  urllib3,
}:

buildPythonApplication rec {
  pname = "etcd3gw";
  version = "2.4.2";

  src = fetchFromGitea {
    domain = "opendev.org";
    owner = "openstack";
    repo = "etcd3gw";
    rev = version;
    hash = "sha256-9OhKEwqfH+91MhAXs1yWsAtN5An1GSrB/lhVeLPISao=";
  };

  env.PBR_VERSION = version;

  build-system = [
    pbr
  ];

  dependencies = [
    requests
    futurist
  ];

  nativeCheckInputs = [
    pkgs.etcd
    coverage
    hacking
    oslotest
    pifpaf
    pytest
    python-subunit
    testrepository
    testscenarios
    testtools
    urllib3
  ];

  checkPhase = ''
    runHook preCheck
    pifpaf -g TOOZ_TEST run etcd -- py.test
    runHook postCheck
  '';

  meta = with lib; {
    description = "An etcd3 grpc-gateway v3 API Python client.";
    homepage = "https://opendev.org/openstack/etcd3gw";
    license = licenses.asl20;
  };
}
