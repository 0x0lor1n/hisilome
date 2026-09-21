{
  description = "Hísilómë — the Zola site and the radio station behind hisilo.me";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = {
    self,
    nixpkgs,
  }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
    lib = pkgs.lib;
    hisilome = import ./nix/packages.nix pkgs;
  in {
    # nginxHttpConfig / nginxLocations are not derivations (`nix flake check`
    # would reject them) and devNginxConf is an internal file, not a package;
    # the module and the dev stack read all three from nix/packages.nix.
    packages.${system} =
      lib.filterAttrs (_: lib.isDerivation) (removeAttrs hisilome ["devNginxConf"])
      // {default = hisilome.site;};

    # Consumer's pkgs, not this flake's nixpkgs: the host never mixes two.
    nixosModules.default = import ./nix/modules/default.nix;

    devShells.${system}.default = import ./nix/devshell.nix pkgs hisilome;
  };
}
