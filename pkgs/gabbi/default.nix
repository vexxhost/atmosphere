{
  lib,
  buildPythonApplication,
  fetchFromGitHub,
  pbr,
  certifi,
  colorama,
  httpx,
  jsonpath-rw-ext,
  pytest,
  pyyaml,
  coverage,
  hacking,
  mock,
  pytest-cov,
  sphinx,
  stestr,
}:

buildPythonApplication rec {
  pname = "gabbi";
  version = "4.1.0";

  src = fetchFromGitHub {
    owner = "cdent";
    repo = "gabbi";
    rev = version;
    hash = "sha256-5yyKX5pJOn0lYloSHsbZayEFqjex7SWnHhykx9/42n0=";
  };

  env.PBR_VERSION = version;

  build-system = [
    pbr
  ];

  dependencies = [
    certifi
    colorama
    httpx
    jsonpath-rw-ext
    pytest
    pyyaml
  ] ++ httpx.optional-dependencies.http2;

  nativeCheckInputs = [
    coverage
    hacking
    mock
    pytest-cov
    sphinx
    stestr
  ];

  # Tests require access to /etc/resolv.conf
  doCheck = false;

  checkPhase = ''
    runHook preCheck
    stestr run
    runHook postCheck
  '';

  meta = with lib; {
    description = "Declarative HTTP Testing for Python and anything else";
    homepage = "https://github.com/cdent/gabbi";
    license = licenses.asl20;
  };
}
