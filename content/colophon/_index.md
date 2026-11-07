+++
title = "colophon"
description = "What this site runs on and what it does not: Zola, nginx with SSI, NixOS, Njalla, Snowcore. No JavaScript, no Cloudflare, no analytics, no IPv6."
template = "colophon.html"
+++
## Build

- Static pages: [Zola](https://www.getzola.org/) 0.22.1, pinned in the flake. Templates are Tera, syntax theme is Kanagawa, highlighting is inlined at build time.
- Diagrams: [d2](https://d2lang.com/) compiled to SVG next to each post and inlined into the page, so labels stay clickable and selectable.
- Font: [Iosevka](https://typeof.net/Iosevka/), two woff2 subsets served from here. Nothing is fetched from a third party.
- Radio: [liquidsoap](https://www.liquidsoap.info/) feeding [icecast](https://icecast.org/). The now-playing widget is three HTML fragments liquidsoap rewrites on disk and nginx includes with SSI. How that works is a [post of its own](/zero-js-radio/).

## Serve

- [NixOS](https://nixos.org/). The site, the station and the nginx locations are one flake module; the host imports it and sets a domain. The repo is public: [github.com/0x0lor1n/hisilome](https://github.com/0x0lor1n/hisilome).
- nginx with `ssi on`, HTTP/2 and HTTP/3, TLS 1.3, HSTS, certificate from Let's Encrypt.
- CSP is `default-src 'none'` with `style-src 'self' 'unsafe-inline'`, `img-src 'self' data:` and the stream's `media-src 'self'`. There is no `script-src` because there is no script.
- VPS: [Snowcore](https://snowcore.io/). Domain and DNS: [Njalla](https://njal.la/).
- Two more doors to the same nginx, no TLS because the overlay is the transport: [Yggdrasil](https://yggdrasil-network.github.io/) at `http://[201:f885:7585:1739:35f4:1185:b21e:967d]/` and Tor at `http://hisilojocbfh7h3qnp5dssb6xukuq2q3sd4jc5hrgajazsokpgsq5pqd.onion/`. The clearnet host sends `Onion-Location`. Both keys are pinned, so the addresses survive a rebuild.

## Not here

- No JavaScript. The progress bar, the ticking clock, the persistent player and the copy button are CSS, SSI and `Sec-Fetch-Dest`.
- No Cloudflare, no CDN, no proxy in front. What answers on 443 is the box itself.
- No analytics, no pixel, no cookies. nginx keeps its own access log and nobody else reads it.
- No IPv6. The VPS has no v6 allocation; the AAAA record lands when the box actually answers on it, not before.
- No comments. Mail, XMPP and SimpleX are in the top bar.

## License

Text and diagrams are [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Templates, CSS and the Nix code are [AGPL-3.0-or-later](https://www.gnu.org/licenses/agpl-3.0.html). Both files sit in the repo.
