# Site + station shell. Kept away from any deploy tooling: station work
# should not pull colmena/secrets, and a host shell should not pull
# liquidsoap's 2.85 GiB closure.
pkgs: hisilome:
pkgs.mkShellNoCC {
  name = "hisilome";
  packages =
    (with pkgs; [
      zola
      d2
      ffmpeg
      flac
      icecast
      liquidsoap
      process-compose
      watchexec
    ])
    ++ (with hisilome; [
      tag-replaygain
      tag-album
      build-queue
      listener-count
      dev-nginx
      build-site
      station-online
      station-offline
    ]);

  shellHook = ''
    echo "build-site                                   d2 -> svg next to each post, then zola build into public/ (SITE_DRAFTS=0 to hide drafts)"
    echo "process-compose up -f process-compose.yaml   local stack: build-site (+ rebuild on change) + nginx :8099 + icecast + liquidsoap"
    echo "  ... -f process-compose.dev.yaml            + restart liquidsoap on radio.liq edits"
    echo "tag-replaygain music                         write ReplayGain tags (-n to preview)"
    echo "tag-album music                              write ALBUM tags from [bracket] prefixes"
    echo "build-queue music                            rebuild the play queue + schedule"
    echo
    echo "NOTE: run these from the repo root -- the configs use relative paths."
  '';
}
