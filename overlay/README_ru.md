# Overlay

[English](README.md) · [Русский](README_ru.md) · [中文](README_zh.md)

Сюда сообщество и мы сами дописываем маршруты поверх апстрима. Конвертер
сливает это с `tools/sources.json` в `global.bat` / `ru.bat` / `cn.bat` /
`ir.bat` / `kz.bat` / `by.bat` (и в новый файл, если появится новая папка).

Сгенерированные `.bat` в корне следующий прогон затрёт.

## Дописать сервис в существующий список

Keenetic `.bat` или голые CIDR, одна папка = один список:

```
overlay/ru/my-bank.bat
overlay/global/some-cdn.bat
overlay/cn/wechat-extra.bat
overlay/ir/bank-melli.bat
overlay/kz/kaspi.bat
overlay/by/egov.bat
```

Имя сервиса: `:: rem` на строке, иначе имя файла.

```
route ADD 203.0.113.0 MASK 255.255.255.0 0.0.0.0 :: rem My Bank
```

или

```
203.0.113.0/24
```

`ru`, `cn`, `ir`, `kz` и `by` едут в Local (мимо лофта), `global` — через лофт.
Любая новая папка (`overlay/ua/…`) тоже мимо, пока в `catalog.json` не
добавят строку для кнопки «Списки».

## Добавить чужой git как источник

`overlay/sources.json`, тот же формат что `tools/sources.json`:

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

`name` не должен совпадать с официальными (`rockblack`, `chnroutes2`,
`iran-ip-ranges`, `ipverse-as`).
`out` — имя файла: `ua` → `ua.bat`. Для появления в клиенте — ещё строка
в корневом `catalog.json`.

Официальные апстримы живут в `tools/sources.json` и меняются мейнтейнерами.

## KZ и BY

Не весь CIDR страны. Сервисы, которые смотрят локальный IP:

| Список | Свой AS ([ipverse/as-ip-blocks](https://github.com/ipverse/as-ip-blocks), каждый день) | Префикс хоста в этой папке |
|--------|----------------------------------------------------------------------------------------|----------------------------|
| `kz` | Kaspi AS35673, Halyk AS44653+AS39433, BCC AS43601, Jusan AS213146, Forte AS48502, Egov/NITEC AS15549 | `kgd.bat` (`kgd.gov.kz` на Kazakhtelecom) |
| `by` | Priorbank AS38980, NCES AS205155 (`portal.gov.by`), BeCloud AS60330 (nalog, raschet, minfin, nbrb) | Belarusbank, Alfa-Bank, MTBank, ERIP, Belpost |

Kazakhtelecom, Beltelecom и MTS BY не берём: это AS страны.

## Как попадает в списки

PR в `overlay/` или `tools/` сразу гоняет Action. Чужие репозитории GitHub
нам вебхук не шлёт — раз в час `git ls-remote`, и если SHA сдвинулся,
списки пересобираются.
