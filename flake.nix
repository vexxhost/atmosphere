{
  description = "Nix Packages collection for Atmosphere";

  inputs = {
    nixpkgs.url = "github:/nixos/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default";
    flake-parts.url = "github:hercules-ci/flake-parts";
    pkgs-by-name-for-flake-parts.url = "github:drupol/pkgs-by-name-for-flake-parts";
    nix2container.url = "github:nlewo/nix2container";
  };

  outputs =
    inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } (
      { withSystem, ... }:
      {
        systems = import inputs.systems;

        imports = [
          inputs.pkgs-by-name-for-flake-parts.flakeModule
        ];

        perSystem =
          { config, system, pkgs, ... }:
          let
            n2c = inputs.nix2container.packages.${system}.nix2container;
          in
          {
            formatter = pkgs.nixfmt-rfc-style;

            # Load local packages into `nixpkgs`
            _module.args.pkgs = import inputs.nixpkgs {
              inherit system;
              overlays = [
                inputs.self.overlays.default
              ];
            };
            pkgsDirectory = ./pkgs/by-name;

            # Images
            packages = {
              capoControllerManager = n2c.buildImage {
                name = "ghcr.io/vexxhost/atmosphere/capo-controller-manager";
                maxLayers = 64;

                copyToRoot = with pkgs.dockerTools; [
                  caCertificates
                ];

                config = {
                  Entrypoint = [ (pkgs.lib.getExe config.packages.cluster-api-provider-openstack) ];
                };
              };
            };

            devShells.default = pkgs.mkShell {
              LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
              RUST_SRC_PATH = pkgs.rust.packages.stable.rustPlatform.rustLibSrc;

              buildInputs = with pkgs; [
                cargo
                clippy
                docutils
                gh
                go
                kubernetes-helm
                patchutils
                pre-commit
                python311Packages.tox
                reno
                renovate
                rust-analyzer
                rustc
                rustfmt
                uv
                vale
              ];
            };
          };

        flake = {
          # Expose package out of the Flake
          overlays.default =
            final: prev:
            withSystem prev.stdenv.hostPlatform.system (
              { config, ... }:
              {
                local = config.packages;
              }
            );
        };
      }
    );
}
