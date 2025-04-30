{
  lib,
  buildPythonApplication,
  fetchFromGitea,
  pbr,
  oslo-config,
  oslo-log,
  oslo-utils,
  prometheus-client,
  coverage,
  oslotest,
  stestr,
}:

buildPythonApplication rec {
  pname = "oslo-metrics";
  version = "0.11.0";

  src = fetchFromGitea {
    domain = "opendev.org";
    owner = "openstack";
    repo = "oslo.metrics";
    rev = version;
    hash = "sha256-PiMrfVWRV3GQPJ7PnXzhAdTncXcFDPZFd+sMHVr65UU=";
  };

  env.PBR_VERSION = version;

  build-system = [
    pbr
  ];

  dependencies = [
    oslo-config
    oslo-log
    oslo-utils
    prometheus-client
  ];

  nativeCheckInputs = [
    coverage
    oslotest
    stestr
  ];

  checkPhase = ''
    runHook preCheck
    stestr run
    runHook postCheck
  '';

  meta = with lib; {
    description = "OpenStack library for collecting metrics from Oslo libraries";
    homepage = "https://opendev.org/openstack/oslo.metrics";
    license = licenses.asl20;
  };
}
