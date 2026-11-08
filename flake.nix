{
  description = "Hísilómë - the Zola site and the radio station behind hisilo.me";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = {nixpkgs, ...}: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
    inherit (pkgs) lib;
    hisilome = import ./nix/packages.nix pkgs;
  in {
    # Not derivations; `nix flake check` would reject them.
    packages.${system} =
      lib.filterAttrs (_: lib.isDerivation) (removeAttrs hisilome ["devNginxConf" "site-html-check"])
      // {default = hisilome.site;};

    # `nix flake check`: the site builds and validates. Guards the push (lefthook.yml).
    checks.${system}.html = hisilome.site-html-check;

    # Consumer's pkgs, not this flake's nixpkgs: the host never mixes two.
    nixosModules.default = import ./nix/modules/default.nix;

    devShells.${system}.default = import ./nix/devshell.nix pkgs hisilome;
  };
}
