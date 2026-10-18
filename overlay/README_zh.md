# Overlay

[English](README.md) · [Русский](README_ru.md) · [中文](README_zh.md)

社区和自己在上游之上补路由。convert 会跟 `tools/sources.json` 合成进 `global.bat` / `ru.bat` / `cn.bat` / `ir.bat` / `kz.bat` / `by.bat`（新文件夹会出新文件）。

根目录生成的 `.bat` 下次跑会被覆盖，别手改。

## 往现有列表加服务

Keenetic `.bat` 或裸 CIDR，一个文件夹一个列表：

```
overlay/ru/my-bank.bat
overlay/global/some-cdn.bat
overlay/cn/wechat-extra.bat
overlay/ir/bank-melli.bat
overlay/kz/kaspi.bat
overlay/by/egov.bat
```

服务名：行上的 `:: rem`，没有就用文件名。

```
route ADD 203.0.113.0 MASK 255.255.255.0 0.0.0.0 :: rem My Bank
```

或

```
203.0.113.0/24
```

`ru`、`cn`、`ir`、`kz`、`by` 进 Local（直连），`global` 走 loft。新文件夹（`overlay/ua/…`）也是直连，直到 `catalog.json` 加一行才会进客户端「列表」选择器。

## 把别人的 git 当源

`overlay/sources.json`，格式跟 `tools/sources.json` 一样：

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

`name` 别跟官方源撞名（`rockblack`、`chnroutes2`、`iran-ip-ranges`、`ipverse-as`）。
`out` 是文件名：`ua` → `ua.bat`。要进客户端，还得在根目录 `catalog.json` 加一行。

官方上游在 `tools/sources.json`，归维护者改。

## KZ 和 BY

不是整国 CIDR。只收会查本地 IP 的服务：

| 列表 | 自己的 AS（[ipverse/as-ip-blocks](https://github.com/ipverse/as-ip-blocks)，每天） | 本目录里的主机前缀 |
|------|-----------------------------------------------------------------------------------|--------------------|
| `kz` | Kaspi AS35673、Halyk AS44653+AS39433、BCC AS43601、Jusan AS213146、Forte AS48502、Egov/NITEC AS15549 | `kgd.bat`（`kgd.gov.kz` 在 Kazakhtelecom） |
| `by` | Priorbank AS38980、NCES AS205155（`portal.gov.by`）、BeCloud AS60330（nalog、raschet、minfin、nbrb） | Belarusbank、Alfa-Bank、MTBank、ERIP、Belpost |

Kazakhtelecom、Beltelecom、MTS BY 不收：那是运营商全国 AS。

## 怎么进列表

PR 到 `overlay/` 或 `tools/` 立刻跑 Action。别人的 GitHub 仓库不会给我们 webhook — 每小时 `git ls-remote`，SHA 动了就重编。
