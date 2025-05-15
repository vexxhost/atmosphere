{
  lib,
  buildGoModule,
  fetchFromGitHub,
  fetchpatch,
}:

buildGoModule rec {
  pname = "cluster-api-provider-openstack";
  version = "0.11.6";

  src = fetchFromGitHub {
    owner = "kubernetes-sigs";
    repo = "cluster-api-provider-openstack";
    rev = "v${version}";
    hash = "sha256-+gLGrnA4OV+Nn5oOmPmQ4y8Spw7fg58k7DWLO/Bbsvc=";
  };

  patches = [
    (fetchpatch {
      url = "https://github.com/kubernetes-sigs/cluster-api-provider-openstack/commit/60f18058b239edac7aad3cf7b1effafae460794c.patch";
      hash = "sha256-QNc4N63QdJlbv7Sw6C62io35BrJ69nyBAZYoMA7bgsU=";
    })
  ];

  vendorHash = "sha256-uR341ST8RJQQ6zomhgZhF2ODzWn4ibqWrLoOBeiKxuM=";

  ldflags =
    let
      t = "sigs.k8s.io/cluster-api-provider-openstack/version";
    in
    [
      "-s"
      "-w"
      "-X ${t}.buildDate=1970-01-01T01:01:01Z"
      "-X ${t}.gitCommit=${src.rev}"
      "-X ${t}.gitTreeState=clean"
      "-X ${t}.gitMajor=${lib.versions.major version}"
      "-X ${t}.gitMinor=${lib.versions.minor version}"
      "-X ${t}.gitVersion=v${version}"
      "-X ${t}.gitReleaseCommit=${src.rev}"
    ];

  excludedPackages = [
    "orc"
    "hack"
  ];

  checkFlags =
    let
      skippedTests = [
        "TestAPIs" # requires setup-envtest which downloads binaries
        "TestController" # requires setup-envtest which downloads binaries
      ];
    in
    [ "-skip=^${builtins.concatStringsSep "$|^" skippedTests}$" ];

  meta = with lib; {
    description = "Cluster API implementation for OpenStack";
    license = licenses.asl20;
    homepage = "https://cluster-api-openstack.sigs.k8s.io/";
    mainProgram = "cluster-api-provider-openstack";
  };
}
