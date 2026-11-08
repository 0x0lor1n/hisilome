# What the station tells Prometheus. Two exporters on one address:
#   node      - the box, plus a textfile the listener poller writes every tick
#               (listeners per mount, peak, queue length, station/icecast up);
#   nginxlog  - the access log, folded to status x method x page x entry.
# No address, UA or referer leaves the box through metrics; those stay in the
# log file for the consumer to pull.
{
  config,
  lib,
  ...
}: let
  cfg = config.services.hisilome;
  m = cfg.metrics;
  textfileDir = "/var/lib/node_exporter/textfile";
in {
  config = lib.mkIf (cfg.enable && m.enable) {
    assertions = [
      {
        assertion = cfg.accessLog.enable;
        message = "services.hisilome.metrics needs services.hisilome.accessLog.enable: the nginxlog exporter tails that file.";
      }
    ];

    services.prometheus.exporters.node = {
      enable = true;
      inherit (m) listenAddress;
      port = m.nodePort;
      enabledCollectors = ["systemd" "textfile"];
      extraFlags = ["--collector.textfile.directory=${textfileDir}"];
    };

    # The poller already fetches icecast's stats for the page fragment;
    # the .prom file is the same fetch rendered twice.
    systemd.tmpfiles.rules = ["d ${textfileDir} 0755 ${cfg.user} ${cfg.group} -"];
    systemd.services.hisilome-listeners = {
      environment.METRICS_OUT = "${textfileDir}/hisilome.prom";
      serviceConfig.ReadWritePaths = [textfileDir];
    };

    services.prometheus.exporters.nginxlog = {
      enable = true;
      inherit (m) listenAddress;
      port = m.nginxlogPort;
      # The log is 0750 nginx:nginx (LogsDirectoryMode); DynamicUser cannot
      # take a supplementary group, so a static user in nginx's group.
      user = "nginxlog-exporter";
      group = config.services.nginx.group;
      settings.namespaces = [
        {
          name = "hisilome";
          parser = "json";
          source.files = [cfg.accessLog.path];
          # 1 vCPU, static files: a tight bucket set catches the stall, the rest is noise.
          histogram_buckets = [0.005 0.01 0.05 0.1 0.5 1 5];
          relabel_configs = [
            {
              target_label = "entry";
              from = "entry";
              whitelist = ["clearnet"] ++ map (l: l.entry) cfg.overlayListen;
            }
            {
              target_label = "page";
              from = "request";
              split = 2;
              separator = " ";
              whitelist = m.pages;
            }
          ];
        }
      ];
    };
    systemd.services.prometheus-nginxlog-exporter.serviceConfig.DynamicUser = false;
    users.users.nginxlog-exporter = {
      isSystemUser = true;
      group = config.services.nginx.group;
    };
  };
}
