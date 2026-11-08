{
  config,
  lib,
  pkgs,
  ...
}: let
  cfg = config.services.hisilome;
  hisilome = import ../packages.nix pkgs;
  radioState = "${cfg.stateDir}/radio/state";

  # One file for all doors; the entry is a field, set per server block.
  logging = entry:
    lib.optionalString cfg.accessLog.enable ''
      set $hisilome_entry ${entry};
      access_log ${cfg.accessLog.path} hisilome;
    '';

  # 'unsafe-inline' on style-src only: liquidsoap's fragments and the tag cloud
  # use style attributes.
  contentHeaders = ''
    add_header Content-Security-Policy "default-src 'none'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; media-src 'self'; frame-src 'self'; frame-ancestors 'self'; base-uri 'none'; form-action 'none'" always;
    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
  '';
  # Clearnet only: HSTS on a plain-HTTP overlay listener is harmful. Inside the
  # header set, not vhost extraConfig: a location's add_header drops the inherited set.
  securityHeaders =
    contentHeaders
    + ''
      add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
      add_header Alt-Svc 'h3=":443"; ma=86400' always;
    ''
    + lib.optionalString (cfg.onionLocation != null) ''
      add_header Onion-Location "http://${cfg.onionLocation}$request_uri" always;
    '';

  # An overlay address does not route on the clearnet, so there is no
  # redirect to https here and no cert: the overlay is the transport security.
  overlayHost = {
    addr,
    port,
    entry,
  }:
    lib.nameValuePair "${cfg.domain}-${lib.replaceStrings ["[" "]" ":"] ["" "" "_"] addr}-${toString port}" {
      serverName = cfg.domain;
      listen = [
        {
          inherit addr port;
        }
      ];
      root = "${cfg.site}";
      extraConfig = ''
        ssi on;
        error_page 404 /404.html;
        # The slash redirect (/logs -> /logs/) would otherwise name the
        # loopback port the onion maps away: Location: http://x.onion:8081/logs/
        absolute_redirect off;
        ${logging entry}
        ${contentHeaders}
      '';
      locations = hisilome.nginxLocations {
        stateDir = radioState;
        extraHeaders = contentHeaders;
      };
    };
in {
  config = lib.mkIf cfg.enable {
    services.nginx = {
      enable = true;

      # Reload, not restart: listeners hold /stream.* open for hours.
      enableReload = true;

      recommendedProxySettings = false; # would override the Icy-MetaData fix
      recommendedGzipSettings = true;
      recommendedOptimisation = true;

      appendHttpConfig = hisilome.nginxHttpConfig;
      # Before the server blocks: nginx rejects an access_log naming a format
      # it has not read yet.
      commonHttpConfig = lib.optionalString cfg.accessLog.enable hisilome.nginxLogFormat;

      virtualHosts =
        {
          ${cfg.domain} = {
            inherit (cfg) enableACME;
            forceSSL = cfg.enableACME;
            quic = cfg.enableACME;
            http3 = cfg.enableACME;
            root = "${cfg.site}";

            # live.html and schedule.html include fragments liquidsoap writes;
            # without ssi they render an empty hole and still return 200.
            extraConfig = ''
              ssi on;
              error_page 404 /404.html;
              ${logging "clearnet"}
              ${securityHeaders}
            '';

            locations = hisilome.nginxLocations {
              stateDir = radioState;
              extraHeaders = securityHeaders;
            };
          };
        }
        // lib.listToAttrs (map overlayHost cfg.overlayListen);
    };

    users.users.${config.services.nginx.user}.extraGroups = [cfg.group];
  };
}
