# loft-routes

[English](README.md) · [Русский](README_ru.md) · [中文](README_zh.md)

Один `.bat` на список, с именем сервиса на каждой строке. Loft и KeeneticOS 5.0
читают комментарий `:: rem`.

В корне только то, что подписывают клиенты. Конвертер, апстримы и утилиты — в
[`tools/`](tools/). Свои и community-маршруты — в [`overlay/`](overlay/).

## Списки

| Список | Обычная зона | Адрес |
|--------|--------------|-------|
| Global | через лофт | `https://raw.githubusercontent.com/a3app/loft-routes/main/global.bat` |
| RU | мимо лофта | `https://raw.githubusercontent.com/a3app/loft-routes/main/ru.bat` |
| CN | мимо лофта | `https://raw.githubusercontent.com/a3app/loft-routes/main/cn.bat` |
| IR | мимо лофта | `https://raw.githubusercontent.com/a3app/loft-routes/main/ir.bat` |
| KZ | мимо лофта | `https://raw.githubusercontent.com/a3app/loft-routes/main/kz.bat` |
| BY | мимо лофта | `https://raw.githubusercontent.com/a3app/loft-routes/main/by.bat` |

Каталог кнопки «Списки» в клиенте:

```
https://raw.githubusercontent.com/a3app/loft-routes/main/catalog.json
```

У зоны loft один URL: Global — `global.bat`, Local — `ru.bat`, `cn.bat`, `ir.bat`, `kz.bat` или `by.bat`.
Направление живёт у зоны.

В списках «вокруг loft» по сервисам выкидываются префиксы шире `/16` и известные
суперсети Cloudflare / Google / Fastly / AWS / GCP. Строка `yandex` или
`kino.pub` с `104.16.0.0/12` уводила speedtest и весь Cloudflare мимо loft.
Страновые дампы (`cn`, `ir`) как были, так и остаются.

Keenetic:

```
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-global.bat
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-ru.bat
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-cn.bat
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-ir.bat
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-kz.bat
https://raw.githubusercontent.com/a3app/loft-routes/main/keenetic-by.bat
```

## Откуда берётся

| Список | Апстрим |
|--------|---------|
| `global`, `ru` | [RockBlack-VPN/ip-address](https://github.com/RockBlack-VPN/ip-address) (`Global/`, `RU-RU/`) |
| `cn` | [misakaio/chnroutes2](https://github.com/misakaio/chnroutes2) — материковый IPv4 с BGP, один сервис `China` |
| `ir` | [farshidmousavii/iran-ip-ranges](https://github.com/farshidmousavii/iran-ip-ranges) — объявленный IPv4 из RIPE Stat, раз в 6 часов, сервис `Iran` |
| `kz`, `by` | дерево сервисов: свои AS из [ipverse/as-ip-blocks](https://github.com/ipverse/as-ip-blocks) (Kaspi, Halyk, BCC, Jusan, Forte, Egov, Priorbank, NCES, BeCloud), плюс префиксы хостов в [`overlay/kz/`](overlay/kz/) и [`overlay/by/`](overlay/by/) |

Официальные git-источники: [`tools/sources.json`](tools/sources.json).

Готового китайского дерева по сервисам (WeChat, Alipay, …) нет: Clash-списки —
домены и ASN, loft едет по CIDR.

## Как обновляется

Чужой репозиторий нам вебхук не шлёт. Action раз в час делает `git ls-remote`
по всем источникам из `tools/sources.json` и `overlay/sources.json`. Если SHA
сдвинулся относительно [`tools/lock.json`](tools/lock.json) — пересобирает
списки и коммитит. PR или пуш в `tools/` / `overlay/` пересобирает сразу.
Вручную: Actions → build → Run workflow.

## Дописать свой список

См. [`overlay/README_ru.md`](overlay/README_ru.md). Кратко:

1. Файл в `overlay/ru/` (или `global/`, `cn/`, `ir/`, `kz/`, `by/`, новая папка = новый список).
2. Или git-источник в `overlay/sources.json`.
3. Новый список в кнопке клиента — строка в `catalog.json`.

Сгенерированные `.bat` в корне следующий прогон затрёт. Правка живёт в
`overlay/` или в апстриме.

Локально:

```
python3 tools/convert.py --self-test
python3 tools/convert.py
```

## Формат строки

```
route ADD 142.250.0.0 MASK 255.255.0.0 0.0.0.0 :: rem YouTube
route ADD 87.240.128.0 MASK 255.255.192.0 0.0.0.0 :: rem VK.com
```

Шлюз `0.0.0.0` игнорируется: loft и Keenetic биндят список на интерфейс.

## Лицензия

MIT. Сгенерированные префиксы несут лицензию исходников, см. [NOTICE](NOTICE).
