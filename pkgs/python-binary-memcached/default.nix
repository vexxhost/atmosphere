{
  lib,
  pkgs,
  buildPythonApplication,
  fetchFromGitHub,
  setuptools,
  six,
  uhashring,
  flake8,
  mock,
  pytest-cov,
  pytestCheckHook,
  trustme,
}:

buildPythonApplication rec {
  pname = "python-binary-memcached";
  version = "0.31.2";

  src = fetchFromGitHub {
    owner = "jaysonsantos";
    repo = "python-binary-memcached";
    rev = "v${version}";
    hash = "sha256-+o6jP6gI1gRhLLz7JhNTspqmpW+7MHiRJUeyD1PHwbo=";
  };

  build-system = [
    setuptools
  ];

  dependencies = [
    six
    uhashring
  ];

  nativeCheckInputs = [
    pkgs.memcached
    flake8
    mock
    pytest-cov
    pytestCheckHook
    trustme
  ];

  meta = with lib; {
    description = "A pure python module (thread safe) to access memcached via it's binary protocol with SASL auth support.";
    homepage = "https://github.com/jaysonsantos/python-binary-memcached";
    license = licenses.mit;
  };
}
