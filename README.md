# Hísilómë

The Zola site and the radio station behind [hisilo.me](https://hisilo.me):
a static site with zero JavaScript, and a liquidsoap → icecast stream whose
"now playing" UI is nginx SSI over fragments the encoder rewrites.

Everything here is relative to the repo root (`radio/state/`, `music/`,
`public/`), so run commands from here.

## Layout

| path                       | what                                                                |
| -------------------------- | ------------------------------------------------------------------- |
| `content/ templates/ static/ syntaxes/ config.toml` | the Zola site; `.d2` diagrams live next to their post |
| `radio/`                   | `radio.liq`, `icecast.xml`; `radio/state/` is runtime (gitignored)  |
| `bin/`                     | station scripts, wrapped as packages by `nix/packages.nix`          |
| `music/`                   | the library — gitignored, rsync it in                               |
| `nix/packages.nix`         | `pkgs: { site, build-site, … }` — every derivation, one file        |
| `nix/modules/`             | the NixOS module (`services.hisilome.*`)                            |
| `nix/devshell.nix`         | the dev shell                                                       |

## Build and preview

```sh
nix build            # ./result = the rendered site (packages.default = site)
nix develop          # zola, d2, ffmpeg, flac, icecast, liquidsoap, process-compose + the scripts
build-site           # d2 → svg, then zola build into public/ (SITE_DRAFTS=0 hides drafts)
process-compose up -f process-compose.yaml   # site on :8099 through the prod nginx config + icecast + liquidsoap
process-compose up -f process-compose.yaml -f process-compose.dev.yaml   # same, plus rebuild on change
```

`direnv allow` loads the shell automatically (`.envrc` = `use flake`).

Use `process-compose`, not `zola serve`: the pages carry SSI includes that only
nginx resolves.

## Consuming the module

```nix
# flake.nix
inputs.hisilome = {
  url = "github:0x0lor1n/hisilome";
  inputs.nixpkgs.follows = "nixpkgs";
};

# a host
{
  imports = [inputs.hisilome.nixosModules.default];
  services.hisilome = {
    enable = true;
    domain = "hisilo.me";
    stateDir = "/persist/radio";                        # library, queue, state
    sourcePasswordFile = "/run/keys/icecast-source-password";
    adminPasswordFile = "/run/keys/icecast-admin-password";
  };
}
```

The module builds the site with the *host's* `pkgs`, not this flake's
`nixpkgs` input, so a consumer never carries two nixpkgs. This flake's own
pin only serves standalone `nix build` / `nix develop` — keep it on the same
rev as the consumer if you want the two `site` outputs byte-identical.

Options: `enable`, `domain`, `enableACME` (default `true`), `stateDir`
(default `/var/lib/hisilome`), `site` (default the package), `user`/`group`,
`sourcePasswordFile`/`adminPasswordFile` (read at unit start, never in the
store; `null` keeps the loopback-only dev password), `queueRounds`.

The host side — certificate e-mail, firewall, persistence of the ACME state,
`www.` alias — is the consumer's.

## License

Code — [AGPL-3.0-or-later](LICENSE). Texts under `content/` —
[CC BY-SA 4.0](content/LICENSE). Music is not in the repository.
