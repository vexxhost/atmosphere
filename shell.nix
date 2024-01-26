{ pkgs ? import <nixpkgs> { } }:

pkgs.mkShell {
  packages = with pkgs; [
    pkgs.earthly
    pkgs.go
    pkgs.kind
    pkgs.poetry
  ];
}
