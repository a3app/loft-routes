# Overlay

[English](README.md) · [Русский](README_ru.md) · [中文](README_zh.md)

Community and extra routes on top of upstream. The converter merges this with
`tools/sources.json` into `global.bat` / `ru.bat` / `cn.bat` / `ir.bat` /
`kz.bat` / `by.bat` (and a new file if a new folder appears).

Generated `.bat` files at the root are overwritten on the next run.

## Add a service to an existing list

Keenetic `.bat` or bare CIDRs, one folder = one list:

```
overlay/ru/my-bank.bat
overlay/global/some-cdn.bat
overlay/cn/wechat-extra.bat
overlay/ir/bank-melli.bat
overlay/kz/kaspi.bat
overlay/by/egov.bat
```

Service name: `:: rem` on the line, otherwise the file name.

```
route ADD 203.0.113.0 MASK 255.255.255.0 0.0.0.0 :: rem My Bank
```

or

```
203.0.113.0/24
```

`ru`, `cn`, `ir`, `kz`, and `by` go to Local (around loft); `global` goes
through loft. A new folder (`overlay/ua/…`) is also around loft until
`catalog.json` gets a row for the client Lists picker.

## Add a foreign git as a source

`overlay/sources.json`, same shape as `tools/sources.json`:

```json
{
  "sources": [
    {
      "name": "example-ua",
      "git": "https://github.com/org/ua-routes.git",
      "ref": "main",
      "roots": [
        {"path": ".", "via": false, "out": "ua"}
      ]
    }
  ]
}
```

`name` must not collide with official sources (`rockblack`, `chnroutes2`,
`iran-ip-ranges`, `ipverse-as`).
`out` is the file name: `ua` → `ua.bat`. To show up in the client, add a row
in the root `catalog.json`.

Official upstreams live in `tools/sources.json` and are changed by maintainers.

## KZ and BY

Not a country CIDR bag. Services that check a local IP:

| List | Own AS ([ipverse/as-ip-blocks](https://github.com/ipverse/as-ip-blocks), daily) | Host prefix in this folder |
|------|----------------------------------------------------------------------------------|----------------------------|
| `kz` | Kaspi AS35673, Halyk AS44653+AS39433, BCC AS43601, Jusan AS213146, Forte AS48502, Egov/NITEC AS15549 | `kgd.bat` (`kgd.gov.kz` on Kazakhtelecom) |
| `by` | Priorbank AS38980, NCES AS205155 (`portal.gov.by`), BeCloud AS60330 (nalog, raschet, minfin, nbrb) | Belarusbank, Alfa-Bank, MTBank, ERIP, Belpost |

Kazakhtelecom, Beltelecom, and MTS BY stay out: those ASNs are the country.

## How it lands in the lists

A PR to `overlay/` or `tools/` runs the Action immediately. Foreign GitHub
repos do not webhook us — hourly `git ls-remote`, and if the SHA moved, the
lists rebuild.
