# loft-routes

[English](README.md) · [Русский](README_ru.md) · [中文](README_zh.md)

One `.bat` per list, with the service name on every line. Loft and KeeneticOS 5.0
read the `:: rem` comment.

The repo root is what clients fetch. Converter, upstreams, and tools live in
[`tools/`](tools/). Community and extra routes live in [`overlay/`](overlay/).

## Lists

| List | Default zone | URL |
|------|--------------|-----|
| Global | through loft | `https://raw.githubusercontent.com/a3app/loft-routes/main/global.bat` |
| RU | around loft | `https://raw.githubusercontent.com/a3app/loft-routes/main/ru.bat` |
| CN | around loft | `https://raw.githubusercontent.com/a3app/loft-routes/main/cn.bat` |
| IR | around loft | `https://raw.githubusercontent.com/a3app/loft-routes/main/ir.bat` |
| KZ | around loft | `https://raw.githubusercontent.com/a3app/loft-routes/main/kz.bat` |
| BY | around loft | `https://raw.githubusercontent.com/a3app/loft-routes/main/by.bat` |

Catalog for the client Lists picker:

```
https://raw.githubusercontent.com/a3app/loft-routes/main/catalog.json
```

A loft zone takes one URL: Global uses `global.bat`; Local uses `ru.bat`,
`cn.bat`, `ir.bat`, `kz.bat`, or `by.bat`. Direction lives on the zone.

Keenetic:

```
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-global.bat
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-ru.bat
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-cn.bat
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-ir.bat
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-kz.bat
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-by.bat
```

## Sources

| List | Upstream |
|------|----------|
| `global`, `ru` | [RockBlack-VPN/ip-address](https://github.com/RockBlack-VPN/ip-address) (`Global/`, `RU-RU/`) |
| `cn` | [misakaio/chnroutes2](https://github.com/misakaio/chnroutes2) — mainland IPv4 from BGP, one service `China` |
| `ir` | [farshidmousavii/iran-ip-ranges](https://github.com/farshidmousavii/iran-ip-ranges) — announced IPv4 from RIPE Stat, every 6 hours, service `Iran` |
| `kz`, `by` | overlay service tree: own-AS prefixes from [ipverse/as-ip-blocks](https://github.com/ipverse/as-ip-blocks) (Kaspi, Halyk, BCC, Jusan, Forte, Egov, Priorbank, NCES, BeCloud), plus host prefixes in [`overlay/kz/`](overlay/kz/) and [`overlay/by/`](overlay/by/) |

Official git sources: [`tools/sources.json`](tools/sources.json).

China has no per-service tree (WeChat, Alipay, …). Clash lists are domains and
ASNs; loft routes by CIDR.

## How it updates

GitHub cannot webhook a foreign repo. An Action runs `git ls-remote` hourly
against every source in `tools/sources.json` and `overlay/sources.json`. If a
SHA moved relative to [`tools/lock.json`](tools/lock.json), it rebuilds the
lists and commits. A PR or push to `tools/` / `overlay/` rebuilds immediately.
Manual: Actions → build → Run workflow.

## Add your own list

See [`overlay/README.md`](overlay/README.md). Short version:

1. A file in `overlay/ru/` (or `global/`, `cn/`, `ir/`, `kz/`, `by/`; a new folder is a new list).
2. Or a git source in `overlay/sources.json`.
3. A new list in the client picker needs a row in `catalog.json`.

Generated `.bat` files at the root are overwritten on the next run. Edits live
in `overlay/` or upstream.

Locally:

```
python3 tools/convert.py --self-test
python3 tools/convert.py
```

## Line format

```
route ADD 142.250.0.0 MASK 255.255.0.0 0.0.0.0 :: rem YouTube
route ADD 87.240.128.0 MASK 255.255.192.0 0.0.0.0 :: rem VK.com
```

Gateway `0.0.0.0` is ignored: loft and Keenetic bind the list to an interface.

## License

MIT. Generated prefixes keep the license of their sources, see [NOTICE](NOTICE).
