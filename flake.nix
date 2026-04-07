{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";

    treefmt-nix.url = "github:numtide/treefmt-nix";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";

    devshell.url = "github:numtide/devshell";
    devshell.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.treefmt-nix.flakeModule
        inputs.devshell.flakeModule
      ];

      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
        "x86_64-darwin"
      ];
      perSystem =
        {
          config,
          self',
          inputs',
          pkgs,
          system,
          ...
        }:
        {
          treefmt = {
            programs.jsonnetfmt = {
              enable = true;
            };

            programs.nixfmt = {
              enable = true;
            };

            programs.rustfmt = {
              enable = true;
            };

            settings.global.excludes = [
              "charts/**"
              "roles/kube_prometheus_stack/files/jsonnet/vendor/**"
            ];
          };

          devshells.default = {
            env = [
              {
                name = "LD_LIBRARY_PATH";
                value = "${pkgs.stdenv.cc.cc.lib}/lib";
              }
              {
                name = "RUST_SRC_PATH";
                value = pkgs.rust.packages.stable.rustPlatform.rustLibSrc;
              }
            ];

            packages =
              with pkgs;
              [
                cargo
                clippy
                docutils
                gh
                go
                jsonnet-bundler
                kubernetes-helm
                patchutils
                pre-commit
                python311Packages.tox
                reno
                renovate
                rust-analyzer
                rustc
                uv
                vale
              ]
              ++ (builtins.attrValues config.treefmt.build.programs);
          };
        };

      flake = {
      };
    };
}
