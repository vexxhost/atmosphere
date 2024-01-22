{ pkgs ? import <nixpkgs> { } }:

pkgs.mkShell {
  packages = with pkgs; [
    pkgs.go
    pkgs.earthly
    pkgs.poetry
  ];
}
