# Called with the consumer's pkgs: the module passes the host's, flake.nix its own.
pkgs: let
  inherit (pkgs) lib;
  zola = pkgs.callPackage ./zola-0.22.nix {};

  # music/ (1.1 GB) and radio/state/ (rewritten every second) would churn the host toplevel.
  src = builtins.path {
    path = ../.;
    name = "hisilome-src";
    filter = path: _type: let
      rel = lib.removePrefix (toString ../. + "/") (toString path);
    in
      !(lib.hasPrefix "music" rel || lib.hasPrefix "radio/state" rel || lib.hasPrefix "diagrams/out" rel);
  };

  mkScript = name: runtimeInputs:
    pkgs.writeShellApplication {
      inherit name runtimeInputs;
      text = builtins.readFile "${src}/bin/${name}.sh";
    };

  # d2 takes .ttf only (not the .ttc iosevka-bin ships); the page's woff2 subsets, decompressed.
  d2-fonts =
    pkgs.runCommand "hisilome-d2-fonts" {
      nativeBuildInputs = [(pkgs.python3.withPackages (p: [p.fonttools p.brotli]))];
    } ''
      mkdir -p $out
      for w in regular bold; do
        fonttools ttLib.woff2 decompress ${src}/static/fonts/iosevka-$w.woff2 -o $out/$w.ttf
      done
    '';

  # --scale 1 writes width/height on the <svg>: without it a 360px chain stretches to the column.
  build-site = pkgs.writeShellApplication {
    name = "build-site";
    runtimeInputs = [pkgs.d2 zola pkgs.coreutils pkgs.findutils pkgs.gnused pkgs.gnugrep pkgs.gawk];
    text = ''
      export D2_FONT_REGULAR=${d2-fonts}/regular.ttf
      export D2_FONT_ITALIC=${d2-fonts}/regular.ttf
      export D2_FONT_BOLD=${d2-fonts}/bold.ttf
      export D2_FONT_SEMIBOLD=${d2-fonts}/bold.ttf
      # A leading "# layout: dagre" line overrides elk. --no-xml-tag: the svg is inlined into HTML.
      find content -name '[0-9]*.d2' -print0 | while IFS= read -r -d "" f; do
        layout=$(sed -n '1,3s/^# layout: *//p' "$f" | head -1)
        d2 --layout "''${layout:-elk}" --theme 200 --pad 10 --scale 1 --no-xml-tag "$f" "''${f%.d2}.svg"
        # d2 paints stroke/fill onto <image>, invalid there; pixel-identical without.
        sed -i -E 's/(<image[^>]*)\s(stroke|fill)="[^"]*"/\1/g; s/(<image[^>]*)\s(stroke|fill)="[^"]*"/\1/g' "''${f%.d2}.svg"
      done
      # Drafts in unless SITE_DRAFTS=0; the site derivation sets 0.
      if [ "''${SITE_DRAFTS:-1}" != 0 ]; then set -- --drafts "$@"; fi
      zola build "$@"

      out=public prev=
      for a in "$@"; do
        case $prev in --output-dir | -o) out=$a ;; esac
        case $a in --output-dir=*) out=''${a#*=} ;; esac
        prev=$a
      done

      # live.html is not a Zola page: style.css's @font-face/:root plus _live.css inlined at the marker.
      css=$(mktemp)
      {
        sed -n '/^@font-face {/,/^}/p' "$out/style.css"
        printf ':root {\n'
        sed -n '/^:root {/,/^}/p' "$out/style.css" \
          | grep -E '^\s*(--[a-z0-9-]+: (#|var\()|color-scheme:)'
        printf '}\n'
        cat templates/_live.css
      } > "$css"
      awk -v f="$css" '
        /<!--@css@-->/ { while ((getline l < f) > 0) print l; next }
        { print }' templates/live.html > "$out/live.html"
      rm -f "$css"

      # <page>/meta.html, SSI-included by the shell so a framed post carries its own <title>.
      find "$out" -name index.html -print0 | while IFS= read -r -d "" f; do
        sed -n '/<!--meta-->/,/<!--\/meta-->/{/<!--/d;/^$/d;p}' "$f" > "''${f%index.html}meta.html"
      done
    '';
  };

  # Written by liquidsoap into radio/state: outside the site root so `zola build` cannot delete them.
  fragments = [
    {
      name = "console.html";
      file = "console.html";
      type = "text/html";
    }
    {
      name = "refresh.html";
      file = "refresh.html";
      type = "text/html";
    }
    {
      name = "schedule-body.html";
      file = "schedule.html";
      type = "text/html";
    }
    {
      name = "listeners.txt";
      file = "listeners.txt";
      type = "text/plain";
    }
    {
      name = "now-playing.txt";
      file = "now-playing.txt";
      type = "text/plain";
    }
    {
      # Empty while liquidsoap runs; ExecStopPost writes the offline <style> into it.
      name = "status.html";
      file = "status.html";
      type = "text/html";
    }
  ];

  # SSI cannot add a class to <body>, so the fragment flips a custom property instead.
  offlineStyle = "<style>:root{--station-ui:none;--ld-image:var(--ld-loader);--ld-anim:ld-crawl 1.8s steps(14,end) infinite}</style>";

  # volatile: a subrequest shares the parent's variable cache, and the shell's
  # meta.html include would get the shell again, forever.
  nginxHttpConfig = ''
    map "$http_sec_fetch_dest$uri" $shell_page {
      volatile;
      ~^document.*/$  /listen/index.html;
      default         /__none;
    }

    # A link inside a shell frame points at the shell's own URL plus the page
    # as a fragment (templates/macros.html `href`): :target flips the frame,
    # nothing reloads. The shell URL is the frame's Referer (same origin, so
    # the policy sends the path; fragments never travel in Referer). Empty
    # outside a frame, or when the frame has no referrer: a plain link.
    map "$http_sec_fetch_dest $http_referer" $shell_href {
      "~^iframe (?<shell_url>https?://[^#?]+/)$"  "$shell_url#";
      default                                     "";
    }

    # Who knocks: a class, not the string. The class is what the log exporter
    # labels and Grafana plots; the raw agent stays in the log on the box.
    # First match wins, so feed readers and tools go before the Mozilla catch-all
    # (most readers and every headless browser claim Mozilla).
    map $http_user_agent $hisilome_agent {
      default                                                   other;
      ""                                                        none;
      ~*(bot|crawl|spider|slurp|archiver|scrapy|facebookexternalhit|gptbot|claudebot|ccbot|bytespider|petalbot|semrush|ahrefs|mj12) bot;
      ~*(feed|rss|reader|tiny.?tiny|miniflux|newsblur|feedly|inoreader|freshrss|akregator|liferea|newsboat|nextcloud|thunderbird) feed;
      ~*(curl|wget|httpie|python-requests|python-urllib|go-http-client|okhttp|libwww|lwp|java/|axios|node-fetch|undici) tool;
      ~*(mpv|vlc|ffmpeg|liquidsoap|icecast|foobar|winamp|audacious|clementine|rhythmbox|kodi|lavf|gstreamer|bass/|strawberry|cmus|mpd) player;
      ~*(mozilla|lynx|w3m|links|dillo|netsurf) browser;
    }

    # One client holding a few hundred /stream.* connections took the station down (1 vCPU).
    limit_conn_zone $binary_remote_addr zone=stream:1m;
    limit_req_zone  $binary_remote_addr zone=pages:1m rate=10r/s;
    limit_conn_status 429;
    limit_req_status  429;
  '';

  # Studied at home, counted on the box (modules/metrics.nix). JSON so the
  # exporter needs no regex; the fields are what both consumers read. `entry`
  # is set per server block (clearnet/ygg/tor): one file, the door is a field.
  nginxLogFormat = ''
    log_format hisilome escape=json '{'
      '"time":"$time_iso8601",'
      '"entry":"$hisilome_entry",'
      '"agent":"$hisilome_agent",'
      '"remote_addr":"$remote_addr",'
      '"request":"$request",'
      '"status":$status,'
      '"body_bytes_sent":$body_bytes_sent,'
      '"request_time":$request_time,'
      '"http_referer":"$http_referer",'
      '"http_user_agent":"$http_user_agent",'
      '"server_protocol":"$server_protocol"'
    '}';
  '';

  # A shell load is ~10 requests at once, then a fragment every 10s per listener.
  pageLimit = "limit_req zone=pages burst=40 nodelay;";

  # extraHeaders is repeated wherever a location adds its own header:
  # nginx add_header in a location discards the inherited set.
  nginxLocations = {
    stateDir,
    extraHeaders ? "",
  }:
    {
      "/".extraConfig = ''
        ${pageLimit}
        try_files $shell_page $uri $uri/ =404;
      '';

      # The shell template lives at /listen/ only so zola renders it; as an
      # entry URL it would frame itself. Every page is the shell already.
      "= /listen/".extraConfig = ''
        return 301 /;
      '';

      # Cache-busted by ?v=hash in base.html; fonts are versioned by name.
      "= /style.css".extraConfig = ''
        ${pageLimit}
        add_header Cache-Control "public, max-age=31536000, immutable";
        ${extraHeaders}
      '';

      # A miss is an error status, so the shell's include falls to its stub.
      "~ /meta\\.html$".extraConfig = ''
        ${pageLimit}
        ssi off;
        log_not_found off;
      '';

      "~ ^/fonts/".extraConfig = ''
        ${pageLimit}
        add_header Cache-Control "public, max-age=31536000, immutable";
        ${extraHeaders}
      '';

      "~ ^/stream\\.(mp3|opus)$".extraConfig = ''
        # Two mounts plus a reconnect in flight per household.
        limit_conn stream 6;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_request_buffering off;
        chunked_transfer_encoding off;

        # Icecast answers "ICY 200 OK" to Icy-MetaData: 1; nginx cannot parse that -> 502.
        proxy_set_header Icy-MetaData "";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # default 60s trips on a liquidsoap restart
        proxy_read_timeout 24h;
        proxy_send_timeout 24h;

        gzip off;
      '';
    }
    // lib.listToAttrs (map (f:
      lib.nameValuePair "= /${f.name}" {
        extraConfig = ''
          ${pageLimit}
          alias ${stateDir}/${f.file};
          default_type ${f.type};
          add_header Cache-Control "no-store, no-cache, must-revalidate";
          ${extraHeaders}
          ssi off;
        '';
      })
    fragments);

  # Relative paths resolve against `-p $PWD`.
  devNginxConf = let
    locs = nginxLocations {stateDir = "radio/state";};
    render = lib.concatStringsSep "\n" (lib.mapAttrsToList (k: v: ''
        location ${k} {
        ${v.extraConfig}
        }
      '')
      locs);
  in
    pkgs.writeText "nginx.dev.conf" ''
      daemon off;
      error_log radio/state/logs/nginx_error.log;
      pid radio/state/nginx.pid;
      worker_processes auto;

      events { worker_connections 1024; }

      http {
        include ${pkgs.nginx}/conf/mime.types;
        default_type application/octet-stream;
        access_log radio/state/logs/nginx_access.log;
        client_body_temp_path radio/state/nginx_client_body;
        proxy_temp_path radio/state/nginx_proxy;
        ${nginxHttpConfig}

        server {
          listen 8099;
          root public;
          set $hisilome_origin "http://localhost:8099";
          ssi on;
          ssi_types text/xml application/rss+xml;
          error_page 404 /404.html;
          index index.html;
          ${render}
        }
      }
    '';

  dev-nginx = pkgs.writeShellApplication {
    name = "dev-nginx";
    runtimeInputs = [pkgs.nginx pkgs.coreutils];
    text = ''
      mkdir -p radio/state/logs
      exec nginx -c ${devNginxConf} -p "$PWD" "$@"
    '';
  };

  site = pkgs.runCommand "hisilome-site" {} ''
    set -e
    cp -r ${src} s
    chmod -R u+w s
    cd s
    export HOME=$TMPDIR
    SITE_DRAFTS=0 ${build-site}/bin/build-site --output-dir $out
  '';

  # vnu over the rendered site. The SSI directives are cut first: nginx
  # resolves them, the validator sees `<body<!--# if`. meta.html is a fragment
  # by design (no doctype). Accepted: `@property` (CSS Properties and Values
  # API, vnu's CSS parser predates it) and aria-hidden on the chevron label.
  site-html-check = pkgs.runCommand "hisilome-site-html-check" {nativeBuildInputs = [pkgs.validator-nu];} ''
    cp -r ${site} s
    chmod -R u+w s
    find s -name meta.html -delete
    find s -name '*.html' -exec sed -i -E 's/<!--#[^>]*-->//g' {} +
    vnu --skip-non-html --errors-only \
      --filterpattern '(.*aria-hidden.*label.*|.*Unrecognized at-rule .@property.*|.*Bad value .. for attribute .src. on element .iframe.*)' \
      s
    touch $out
  '';

  # Browser tests (tests/e2e). Chromium + Firefox from nixpkgs' pinned
  # playwright-driver; the python package must be the same minor, so both come
  # from the same nixpkgs rather than pip.
  pwBrowsers = pkgs.playwright-driver.browsers.override {withWebkit = false;};
  pwPython = pkgs.python3.withPackages (p: [p.playwright p.pytest]);

  # Playwright considers Firefox up once stderr says `Juggler listening to the
  # pipe`, which Firefox prints through dump(). A host autoconfig (phoenix.cfg
  # on this machine) turns dump() off system-wide, so the launch times out
  # although Juggler works. Re-enable both prefs in the per-launch profile
  # before the real binary starts; `firefox_user_prefs` cannot do it, it is
  # applied after the handshake.
  #
  # Audio: cubeb dlopens libpulse.so.0 by name and the nixpkgs browser bundle
  # does not carry it, so every <audio> source fails with MEDIASINK_ERR
  # ("libpulse not found" under MOZ_LOG=cubeb:5). Point the loader at the
  # pinned libpulseaudio; must be the same nixpkgs as the browser (glibc).
  #
  # The same autoconfig sets accessibility.blockautorefresh, which silently
  # ignores <meta http-equiv="refresh">: the live frame would never reload
  # and the test_live suite would be measuring the host, not the site.
  pw-firefox = pkgs.writeShellApplication {
    name = "pw-firefox";
    text = ''
      export LD_LIBRARY_PATH=${pkgs.libpulseaudio}/lib''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
      profile=""
      prev=""
      for a in "$@"; do
        [ "$prev" = "-profile" ] && profile=$a
        prev=$a
      done
      if [ -n "$profile" ]; then
        mkdir -p "$profile"
        {
          echo 'user_pref("browser.dom.window.dump.enabled", true);'
          echo 'user_pref("devtools.console.stdout.chrome", true);'
          echo 'user_pref("accessibility.blockautorefresh", false);'
        } >> "$profile/user.js"
      fi
      exec ${pwBrowsers}/firefox-*/firefox/firefox "$@"
    '';
  };

  # 30 s of sine as Ogg/Opus. The console tests serve it in place of
  # /stream.opus through a Playwright route, so playback is checked without
  # icecast and without a binary asset in the repo.
  e2eTone =
    pkgs.runCommand "e2e-tone.opus" {
      nativeBuildInputs = [pkgs.ffmpeg-headless];
    } ''
      ffmpeg -v error -f lavfi -i "sine=frequency=440:duration=30" \
        -c:a libopus -b:a 24k -f ogg "$out"
    '';

  e2eEnv = ''
    export PLAYWRIGHT_BROWSERS_PATH=${pwBrowsers}
    export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1
    export PLAYWRIGHT_FIREFOX_EXECUTABLE=${pw-firefox}/bin/pw-firefox
    export E2E_TONE=${e2eTone}
  '';

  # `nix run .#e2e [pytest args]`: the suite against the dev stack (E2E_BASE,
  # default :8099). Not a flake check: it needs the running stack.
  e2e = pkgs.writeShellApplication {
    name = "e2e";
    runtimeInputs = [pwPython];
    text = ''
      ${e2eEnv}
      exec pytest tests/e2e "$@"
    '';
  };
in {
  # The non-derivations are for nginx.nix and the dev stack; flake.nix filters them out.
  inherit zola nginxLocations nginxHttpConfig nginxLogFormat devNginxConf build-site dev-nginx site site-html-check;
  inherit pw-firefox e2e e2eEnv pwPython;

  station-offline = pkgs.writeShellApplication {
    name = "station-offline";
    text = ''
      printf '%s' '${offlineStyle}' > radio/state/status.html.tmp
      mv radio/state/status.html.tmp radio/state/status.html
    '';
  };
  station-online = pkgs.writeShellApplication {
    name = "station-online";
    text = ''
      : > radio/state/status.html.tmp
      mv radio/state/status.html.tmp radio/state/status.html
    '';
  };

  tag-replaygain = mkScript "tag-replaygain" (
    with pkgs; [
      ffmpeg
      flac
      python3Packages.mutagen
      coreutils
      findutils
      gawk
    ]
  );

  # Not in process-compose: a boot-time rewrite would remux the m4a tracks every run.
  tag-album = mkScript "tag-album" (
    with pkgs; [
      ffmpeg
      flac
      python3Packages.mutagen
      coreutils
      findutils
      gawk
    ]
  );

  build-queue = mkScript "build-queue" (
    with pkgs; [
      ffmpeg
      coreutils
      findutils
      gawk
    ]
  );

  listener-count = mkScript "listener-count" (
    with pkgs; [
      curl
      coreutils
      gnused
      gawk
    ]
  );
}
