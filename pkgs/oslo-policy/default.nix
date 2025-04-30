{
  lib,
  buildPythonApplication,
  fetchFromGitea,
  pbr,
  oslo-config,
  oslo-context,
  oslo-i18n,
  oslo-serialization,
  oslo-utils,
  pyyaml,
  requests,
  stevedore,
  coverage,
  oslotest,
  requests-mock,
  sphinx,
  stestr,
}:

buildPythonApplication rec {
  pname = "oslo-policy";
  version = "4.5.1";

  src = fetchFromGitea {
    domain = "opendev.org";
    owner = "openstack";
    repo = "oslo.policy";
    rev = version;
    hash = "sha256-3uSVSE+0LlvIInHLOptGNFEu1DLdLiXWY8LlPY80Eq0=";
  };

  env.PBR_VERSION = version;

  build-system = [
    pbr
  ];

  dependencies = [
    oslo-config
    oslo-context
    oslo-i18n
    oslo-serialization
    oslo-utils
    pyyaml
    requests
    stevedore
  ];

  nativeCheckInputs = [
    coverage
    oslotest
    requests-mock
    sphinx
    stestr
  ];

  checkPhase = ''
    runHook preCheck
    stestr run
    runHook postCheck
  '';

  meta = with lib; {
    description = "Rules engine to enforce access control policy";
    homepage = "https://opendev.org/openstack/oslo.policy";
    license = licenses.asl20;
  };
}
