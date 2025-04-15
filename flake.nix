{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem
      (system:
        let
          pkgs = import nixpkgs {
            inherit system;
          };
        in
        {
          devShell = pkgs.mkShell {
            buildInputs = with pkgs; [
              bashInteractive
              docutils
              earthly
              glibcLocales
              go
              just
              kubernetes-helm
              nixpkgs-fmt
              patchutils
              python311Packages.tox
              reno
              renovate
              vale
            ];
          };
        }
      );
}
