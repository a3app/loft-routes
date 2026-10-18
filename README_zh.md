# loft-routes

[English](README.md) · [Русский](README_ru.md) · [中文](README_zh.md)

一个列表一个 `.bat`，每行带服务名。Loft 和 KeeneticOS 5.0 认 `:: rem` 注释。

根目录是客户端拉的成品。转换脚本、上游和工具在 [`tools/`](tools/)；社区补丁、自己加的段在 [`overlay/`](overlay/)。

## 列表

| 列表 | 默认区域 | 地址 |
|------|----------|------|
| Global | 走 loft | `https://raw.githubusercontent.com/a3app/loft-routes/main/global.bat` |
| RU | 直连 | `https://raw.githubusercontent.com/a3app/loft-routes/main/ru.bat` |
| CN | 直连 | `https://raw.githubusercontent.com/a3app/loft-routes/main/cn.bat` |
| IR | 直连 | `https://raw.githubusercontent.com/a3app/loft-routes/main/ir.bat` |
| KZ | 直连 | `https://raw.githubusercontent.com/a3app/loft-routes/main/kz.bat` |
| BY | 直连 | `https://raw.githubusercontent.com/a3app/loft-routes/main/by.bat` |

客户端「列表」选择器的目录：

```
https://raw.githubusercontent.com/a3app/loft-routes/main/catalog.json
```

loft 一个区域只挂一个 URL：Global 用 `global.bat`，Local 用 `ru.bat` / `cn.bat` / `ir.bat` / `kz.bat` / `by.bat`。走 loft 还是直连，写在区域上。

Keenetic：

```
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-global.bat
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-ru.bat
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-cn.bat
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-ir.bat
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-kz.bat
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-by.bat
```

## 数据从哪来

| 列表 | 上游 |
|------|------|
| `global`, `ru` | [RockBlack-VPN/ip-address](https://github.com/RockBlack-VPN/ip-address)（`Global/`、`RU-RU/`，按服务拆） |
| `cn` | [misakaio/chnroutes2](https://github.com/misakaio/chnroutes2) — 国内 IPv4，BGP 表，整包一个服务 `China` |
| `ir` | [farshidmousavii/iran-ip-ranges](https://github.com/farshidmousavii/iran-ip-ranges) — RIPE Stat 已宣告 IPv4，6 小时一轮，服务 `Iran` |
| `kz`, `by` | 按服务拆：有自己 AS 的从 [ipverse/as-ip-blocks](https://github.com/ipverse/as-ip-blocks) 拉（Kaspi、Halyk、BCC、Jusan、Forte、Egov、Priorbank、NCES、BeCloud），其余主机前缀在 [`overlay/kz/`](overlay/kz/) 和 [`overlay/by/`](overlay/by/) |

官方 git 源：[`tools/sources.json`](tools/sources.json)。

国内没有现成的按服务拆的 CIDR 树（微信、支付宝这类）。Clash 规则是域名和 ASN，loft 只吃 CIDR。

## 怎么更新

别人的仓库 GitHub 不会给我们推 webhook。Action 每小时对 `tools/sources.json` 和 `overlay/sources.json` 里的源跑 `git ls-remote`，SHA 相对 [`tools/lock.json`](tools/lock.json) 有变动才重新生成并提交。PR 或 push 到 `tools/` / `overlay/` 会立刻重跑。手动：Actions → build → Run workflow。

## 自己补列表

见 [`overlay/README_zh.md`](overlay/README_zh.md)。短版：

1. 文件丢进 `overlay/ru/`（或 `global/`、`cn/`、`ir/`、`kz/`、`by/`；新文件夹就是新列表）。
2. 或者在 `overlay/sources.json` 加 git 源。
3. 要出现在客户端选择器，还得在 `catalog.json` 加一行。

根目录生成的 `.bat` 下次跑 convert 会被覆盖，别手改。改 overlay 或改上游。

本地：

```
python3 tools/convert.py --self-test
python3 tools/convert.py
```

## 行格式

```
route ADD 142.250.0.0 MASK 255.255.0.0 0.0.0.0 :: rem YouTube
route ADD 87.240.128.0 MASK 255.255.192.0 0.0.0.0 :: rem VK.com
```

网关 `0.0.0.0` 没用：loft 和 Keenetic 把列表绑到接口上。

## 许可

MIT。生成出来的前缀跟上游许可证走，见 [NOTICE](NOTICE)。
