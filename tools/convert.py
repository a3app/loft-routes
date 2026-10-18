#!/usr/bin/env python3
"""Walk Keenetic-style route trees into loft-routes / Keenetic lists.

Each `route ADD` line gets `:: rem <service>`. The service name is the
folder (Global/YouTube → YouTube) or the file stem (RU-RU/gosuslugi.bat).
An existing `:: rem` / `& rem` on the line wins.

Stdlib only. Python 3.9+.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

ROUTE_RE = re.compile(
    r"^\s*route\s+(?:add\s+)?(.+)$",
    re.IGNORECASE,
)
REM_RE = re.compile(r"(::\s*rem|&\s*rem)\s*", re.IGNORECASE)
VER_SUFFIX_RE = re.compile(r"_\d+(?:\.\d+)*$")
SKIP_NAME_RE = re.compile(
    r"(?:^|[/\\])(?:license|readme|logo)(?:$|[./\\])|_domain|_domains",
    re.IGNORECASE,
)
KEEP_EXT = {".bat", ".txt", ".lst"}
ROOT_NAMES = {"global", "ru", "ru-ru", "ru_ru", "cn", "ir", "kz", "by"}
SLUG_ALIASES = {"ru-ru": "ru", "ru_ru": "ru"}
STALE_LISTS = ("via.bat", "keenetic.bat", "ru-ru.bat", "keenetic-ru-ru.bat", "lists.md")
OVERLAY_SKIP = {"sources.json"}


def ipv4(s: str) -> Optional[str]:
    parts = s.split(".")
    if len(parts) != 4:
        return None
    out = []
    for p in parts:
        if not p.isdigit():
            return None
        n = int(p)
        if n < 0 or n > 255:
            return None
        out.append(str(n))
    return ".".join(out)


def prefix_from_mask(mask: str) -> Optional[int]:
    octs = mask.split(".")
    if len(octs) != 4:
        return None
    try:
        nums = [int(x) for x in octs]
    except ValueError:
        return None
    if any(n < 0 or n > 255 for n in nums):
        return None
    n = (nums[0] << 24) | (nums[1] << 16) | (nums[2] << 8) | nums[3]
    bits = 0
    while n & 0x80000000:
        bits += 1
        n = (n << 1) & 0xFFFFFFFF
    return bits if n == 0 else None


def mask_from_prefix(bits: int) -> str:
    bits = max(0, min(32, bits))
    n = 0 if bits == 0 else ((0xFFFFFFFF << (32 - bits)) & 0xFFFFFFFF)
    return f"{(n >> 24) & 255}.{(n >> 16) & 255}.{(n >> 8) & 255}.{n & 255}"


def normalize_cidr(raw: str) -> Optional[str]:
    t = raw.strip()
    if not t:
        return None
    if "/" in t:
        ip_s, bits_s = t.split("/", 1)
        ip = ipv4(ip_s)
        if ip is None:
            return None
        try:
            bits = int(bits_s)
        except ValueError:
            return None
        if bits < 0 or bits > 32:
            return None
        return f"{ip}/{bits}"
    ip = ipv4(t)
    return f"{ip}/32" if ip else None


def cidr_sort_key(cidr: str) -> tuple:
    ip, bits = cidr.split("/", 1)
    octs = [int(x) for x in ip.split(".")]
    return (octs[0], octs[1], octs[2], octs[3], int(bits))


def ip_to_int(ip: str) -> int:
    a, b, c, d = (int(x) for x in ip.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


def covers(outer: str, inner: str) -> bool:
    o_ip, o_bits = outer.split("/")
    i_ip, i_bits = inner.split("/")
    ob, ib = int(o_bits), int(i_bits)
    if ob > ib:
        return False
    shift = 32 - ob
    if shift == 32:
        return True
    return (ip_to_int(o_ip) >> shift) == (ip_to_int(i_ip) >> shift)


def collapse_cidrs(cidrs: Iterable[str]) -> list[str]:
    """Drop a prefix that is already covered by a wider one in the same set."""
    items = sorted(set(cidrs), key=lambda c: (int(c.split("/")[1]), cidr_sort_key(c)))
    kept: list[str] = []
    for c in items:
        if any(covers(k, c) for k in kept):
            continue
        kept.append(c)
    kept.sort(key=cidr_sort_key)
    return kept


def parse_route_line(line: str) -> Optional[tuple[str, str]]:
    """Return (cidr, rem_name) or None."""
    s = line.strip()
    if not s or s.startswith("#") or s.upper().startswith("@ECHO"):
        return None
    up = s.upper()
    if up.startswith("REM ") or (up.startswith("::") and "ROUTE" not in up):
        return None
    m = ROUTE_RE.match(s)
    if not m:
        cidr = normalize_cidr(s.split()[0]) if s[0].isdigit() else None
        return (cidr, "") if cidr else None
    rest = m.group(1).strip()
    comment = ""
    rm = REM_RE.search(rest)
    if rm:
        comment = rest[rm.end() :].strip()
        rest = rest[: rm.start()].strip()
    if comment.lower().startswith("rem "):
        comment = comment[4:].strip()
    # Old loft-routes files stamped "| via" / "| bypass" on rem.
    if "|" in comment:
        comment = comment.split("|", 1)[0].strip()
    toks = rest.split()
    if not toks:
        return None
    dest = toks[0]
    cidr = None
    if "/" in dest:
        cidr = normalize_cidr(dest)
    else:
        ip = ipv4(dest)
        if ip is None:
            return None
        mask = "255.255.255.255"
        for i, t in enumerate(toks):
            if t.upper() == "MASK" and i + 1 < len(toks):
                mask = toks[i + 1]
                break
        bits = prefix_from_mask(mask)
        if bits is None:
            return None
        cidr = f"{ip}/{bits}"
    if cidr is None:
        return None
    return cidr, comment


def clean_name(name: str) -> str:
    n = name.strip()
    n = n.replace("_", " ")
    n = re.sub(r"\s+", " ", n)
    n = n.strip(" .")
    return n


def service_from_rel(rel: Path) -> str:
    parts = list(rel.parts)
    if parts and parts[0].lower() in ROOT_NAMES:
        parts = parts[1:]
    if not parts:
        return "net"
    if len(parts) >= 2:
        return clean_name(parts[0])
    stem = Path(parts[0]).stem
    stem = VER_SUFFIX_RE.sub("", stem)
    return clean_name(stem) or "net"


def should_skip(rel: Path) -> bool:
    s = str(rel).replace("\\", "/")
    if SKIP_NAME_RE.search(s):
        return True
    if rel.suffix.lower() not in KEEP_EXT:
        return True
    name = rel.name.lower()
    if name.endswith("_domain") or name.endswith("_domains"):
        return True
    if name in OVERLAY_SKIP:
        return True
    return False


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1251", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def walk_tree(root: Path, roots: list[str]) -> list[Path]:
    bases = [root / r if r else root for r in roots] if roots else [root]
    files: list[Path] = []
    for base in bases:
        if not base.exists():
            continue
        if base.is_file():
            files.append(base)
            continue
        for p in base.rglob("*"):
            if p.is_file():
                files.append(p)
    files.sort()
    return files


class Bucket:
    def __init__(self, name: str, source: str, via: bool, group: str):
        self.name = name
        self.source = source
        self.via = via
        self.group = group
        self.cidrs: OrderedDict[str, None] = OrderedDict()

    def add(self, cidr: str) -> None:
        self.cidrs.setdefault(cidr, None)


def slug_root(path: str) -> str:
    s = path.strip().replace("\\", "/").replace("_", "-").lower()
    if "/" not in s and "." in s:
        s = Path(s).stem.lower().replace("_", "-")
    return SLUG_ALIASES.get(s, s)


def default_via_for_slug(slug: str) -> bool:
    """Only global goes through loft. Regional lists attach to Local."""
    return slug == "global"


def normalize_roots(raw) -> list[dict]:
    """String roots or {path, via, out, service} maps. Only global defaults to via."""
    out: list[dict] = []
    for r in raw or []:
        if isinstance(r, str):
            slug = slug_root(r)
            out.append({"path": r, "via": default_via_for_slug(slug), "out": slug})
            continue
        path = r["path"]
        slug = r.get("out") or slug_root(path)
        via = r["via"] if "via" in r else default_via_for_slug(slug)
        spec = {"path": path, "via": bool(via), "out": slug}
        if r.get("service"):
            spec["service"] = str(r["service"])
        out.append(spec)
    return out


def rel_for_service(root: Path, spec_path: str, file_path: Path) -> Path:
    """Name a service relative to the ingested root folder, not the clone root."""
    if not spec_path:
        return file_path.relative_to(root)
    base = root / spec_path
    if base.is_file():
        return Path(base.name)
    try:
        return file_path.relative_to(base)
    except ValueError:
        return file_path.relative_to(root)


def ingest_tree(
    root: Path,
    roots: list[dict],
    source_name: str,
    buckets: dict[str, Bucket],
) -> int:
    n = 0
    specs = roots or [{"path": "", "via": True, "out": "all"}]
    for spec in specs:
        base = [spec["path"]] if spec["path"] else []
        group = spec["out"]
        via = spec["via"]
        forced = spec.get("service")
        for path in walk_tree(root, base):
            rel = path.relative_to(root)
            if should_skip(rel):
                continue
            named = rel_for_service(root, spec["path"], path)
            folder_name = forced or service_from_rel(named)
            text = read_text(path)
            for line in text.splitlines():
                parsed = parse_route_line(line)
                if not parsed:
                    continue
                cidr, rem = parsed
                name = clean_name(rem) if rem else folder_name
                if not name:
                    name = folder_name
                key = f"{group}:{name.lower()}"
                if key not in buckets:
                    buckets[key] = Bucket(name, source_name, via, group)
                buckets[key].add(cidr)
                n += 1
    return n


def overlay_roots(overlay: Path) -> list[dict]:
    """Each overlay/<list-id>/ folder becomes that list."""
    if not overlay.is_dir():
        return []
    out: list[dict] = []
    for child in sorted(overlay.iterdir()):
        if child.name.startswith(".") or child.name in OVERLAY_SKIP:
            continue
        if not child.is_dir():
            continue
        slug = slug_root(child.name)
        out.append({"path": child.name, "via": default_via_for_slug(slug), "out": slug})
    return out


def emit_bat(buckets: list[Bucket], loft: bool, sources: list[str]) -> str:
    lines = ["@echo off\r\n"]
    if loft:
        lines.append("REM loft-routes 1.0\r\n")
        lines.append("REM Keenetic eats this file as a normal .bat. Gateway is ignored.\r\n")
    for s in sources:
        lines.append(f"REM source: {s}\r\n")
    groups = sorted({b.group for b in buckets if b.group})
    if groups:
        lines.append(f"REM group: {', '.join(groups)}\r\n")
    lines.append("REM\r\n")
    for b in buckets:
        cidrs = list(b.cidrs.keys())
        for c in cidrs:
            ip, bits = c.split("/", 1)
            mask = mask_from_prefix(int(bits))
            lines.append(f"route ADD {ip} MASK {mask} 0.0.0.0 :: rem {b.name}\r\n")
    return "".join(lines)


def sources_for(rows: list[Bucket], labels: list[str]) -> list[str]:
    names = {b.source for b in rows}
    picked = [s for s in labels if s.split()[0] in names]
    return picked or labels


def drop_stale(out_dir: Path) -> None:
    for name in STALE_LISTS:
        p = out_dir / name
        if p.exists():
            p.unlink()
            print(f"removed {p.name}", file=sys.stderr)


def write_lists(out_dir: Path, buckets: list[Bucket], sources: list[str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    drop_stale(out_dir)
    ordered = sorted(buckets, key=lambda b: (b.group, b.name.lower()))
    for b in ordered:
        b.cidrs = OrderedDict((c, None) for c in collapse_cidrs(b.cidrs.keys()))
    total = sum(len(b.cidrs) for b in ordered)
    by_group: dict[str, list[Bucket]] = OrderedDict()
    for b in ordered:
        by_group.setdefault(b.group, []).append(b)
    for group, rows in by_group.items():
        if not group or group == "all":
            continue
        srcs = sources_for(rows, sources)
        (out_dir / f"{group}.bat").write_bytes(emit_bat(rows, True, srcs).encode("utf-8"))
        (out_dir / f"keenetic-{group}.bat").write_bytes(emit_bat(rows, False, srcs).encode("utf-8"))
        n = sum(len(b.cidrs) for b in rows)
        print(f"  {group}: {len(rows)} services, {n} CIDRs → {group}.bat", file=sys.stderr)
    print(f"{len(ordered)} services, {total} CIDRs", file=sys.stderr)


def sparse_paths(raw) -> list[str]:
    if not raw:
        return []
    if not isinstance(raw, list):
        raise SystemExit("sparse must be a list of paths")
    return [str(p).strip() for p in raw if str(p).strip()]


def git_clone(url: str, ref: str, dest: Path, sparse: Optional[list[str]] = None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    paths = sparse_paths(sparse)
    if dest.exists():
        if paths:
            subprocess.run(["git", "-C", str(dest), "sparse-checkout", "init", "--cone"], check=True)
            subprocess.run(["git", "-C", str(dest), "sparse-checkout", "set", "--"] + paths, check=True)
        subprocess.run(["git", "-C", str(dest), "fetch", "--depth", "1", "origin", ref], check=True)
        subprocess.run(["git", "-C", str(dest), "checkout", "--force", "FETCH_HEAD"], check=True)
        return
    if paths:
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--filter=blob:none",
                "--sparse",
                "--branch",
                ref,
                url,
                str(dest),
            ],
            check=True,
        )
        subprocess.run(["git", "-C", str(dest), "sparse-checkout", "set", "--"] + paths, check=True)
        return
    subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", ref, url, str(dest)],
        check=True,
    )


def git_head(dest: Path) -> str:
    r = subprocess.run(
        ["git", "-C", str(dest), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return r.stdout.strip()


def git_ls_remote(url: str, ref: str) -> str:
    r = subprocess.run(
        ["git", "ls-remote", url, ref, f"refs/heads/{ref}", f"refs/tags/{ref}"],
        check=True,
        capture_output=True,
        text=True,
    )
    wanted = {ref, f"refs/heads/{ref}", f"refs/tags/{ref}"}
    for line in r.stdout.splitlines():
        if not line.strip():
            continue
        sha, name = line.split("\t", 1)
        if name in wanted:
            return sha
    raise SystemExit(f"no ref {ref} at {url}")


def load_sources(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    srcs = data.get("sources", data)
    if not isinstance(srcs, list):
        raise SystemExit(f"{path}: expected {{\"sources\": [...]}}")
    return srcs


def load_source_files(paths: Iterable[Path]) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        for src in load_sources(path):
            if "git" not in src:
                raise SystemExit(f"{path}: source missing git")
            name = src.get("name") or slug_from_git(src["git"])
            if name in seen:
                raise SystemExit(f"duplicate source name {name}")
            seen.add(name)
            src = dict(src)
            src["name"] = name
            out.append(src)
    return out


def slug_from_git(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    name = path.split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name or "src"


def collect_shas(srcs: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for src in srcs:
        url = src["git"]
        ref = src.get("ref", "main")
        name = src["name"]
        sha = git_ls_remote(url, ref)
        print(f"  {name} {ref} {sha[:12]}", file=sys.stderr)
        out[name] = sha
    return out


def read_lock(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    srcs = data.get("sources", data)
    if not isinstance(srcs, dict):
        return {}
    return {str(k): str(v) for k, v in srcs.items()}


def write_lock(path: Path, shas: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"sources": dict(sorted(shas.items()))}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def self_test() -> None:
    cases = [
        ("route ADD 17.0.0.0 MASK 255.0.0.0 0.0.0.0", "17.0.0.0/8", ""),
        ("route add 108.177.14.0 mask 255.255.255.0 0.0.0.0", "108.177.14.0/24", ""),
        ("route add 142.250.0.0 mask 255.255.0.0 0.0.0.0 & rem YouTube", "142.250.0.0/16", "YouTube"),
        ("route ADD 1.1.1.1 MASK 255.255.255.255 0.0.0.0 :: rem Cloudflare | via", "1.1.1.1/32", "Cloudflare"),
        ("#AS714", None, None),
        ("@echo off", None, None),
        ("10.0.0.0/8", "10.0.0.0/8", ""),
    ]
    for line, cidr, name in cases:
        got = parse_route_line(line)
        if cidr is None:
            assert got is None, (line, got)
        else:
            assert got == (cidr, name), (line, got)
    assert service_from_rel(Path("Global/Youtube/youtube_minimum.bat")) == "Youtube"
    assert service_from_rel(Path("RU-RU/gosuslugi.bat")) == "gosuslugi"
    assert service_from_rel(Path("RU-RU/2ip.ru.bat")) == "2ip.ru"
    assert service_from_rel(Path("Global/ChatGPT(OpenAI)/ChatGPT(OpenAI)_0.0.6.bat")) == "ChatGPT(OpenAI)"
    assert service_from_rel(Path("gosuslugi.bat")) == "gosuslugi"
    assert collapse_cidrs(["142.250.0.0/16", "142.250.1.0/24"]) == ["142.250.0.0/16"]
    assert prefix_from_mask("255.255.0.0") == 16
    assert mask_from_prefix(16) == "255.255.0.0"
    assert slug_root("RU-RU") == "ru"
    assert slug_root("chnroutes.txt") == "chnroutes"
    assert default_via_for_slug("global") is True
    assert default_via_for_slug("ru") is False
    assert default_via_for_slug("cn") is False
    assert default_via_for_slug("ir") is False
    assert default_via_for_slug("kz") is False
    assert default_via_for_slug("by") is False
    assert default_via_for_slug("ua") is False
    ir = normalize_roots([{"path": "dist/raw/ipv4.txt", "via": False, "out": "ir", "service": "Iran"}])
    assert ir[0] == {"path": "dist/raw/ipv4.txt", "via": False, "out": "ir", "service": "Iran"}
    kz = normalize_roots(
        [{"path": "country/kz/ipv4-aggregated.txt", "via": False, "out": "kz", "service": "Kazakhstan"}]
    )
    assert kz[0]["out"] == "kz" and kz[0]["service"] == "Kazakhstan"
    assert sparse_paths(None) == []
    assert sparse_paths(["country/kz", "country/by"]) == ["country/kz", "country/by"]
    specs = normalize_roots(["Global", "RU-RU"])
    assert specs[0] == {"path": "Global", "via": True, "out": "global"}
    assert specs[1] == {"path": "RU-RU", "via": False, "out": "ru"}
    cn = normalize_roots([{"path": "chnroutes.txt", "via": False, "out": "cn", "service": "China"}])
    assert cn[0] == {"path": "chnroutes.txt", "via": False, "out": "cn", "service": "China"}
    a = Bucket("China", "chnroutes2", False, "cn")
    b = Bucket("YouTube", "rockblack", True, "global")
    labels = [
        "rockblack https://github.com/RockBlack-VPN/ip-address.git@main",
        "chnroutes2 https://github.com/misakaio/chnroutes2.git@master",
    ]
    assert sources_for([a], labels) == [labels[1]]
    assert sources_for([b], labels) == [labels[0]]
    a.add("1.0.1.0/24")
    loft_txt = emit_bat([a], True, labels)
    assert " | via" not in loft_txt
    assert " | bypass" not in loft_txt
    assert "REM list:" not in loft_txt
    assert ":: rem China\r\n" in loft_txt
    assert "REM loft-routes 1.0\r\n" in loft_txt
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        ov = Path(tmp)
        (ov / "ru").mkdir()
        (ov / "ru" / "my-bank.bat").write_text(
            "route ADD 203.0.113.0 MASK 255.255.255.0 0.0.0.0 :: rem My Bank\n",
            encoding="utf-8",
        )
        (ov / "ua").mkdir()
        (ov / "ua" / "extra.txt").write_text("198.51.100.0/24\n", encoding="utf-8")
        roots = overlay_roots(ov)
        assert {r["out"] for r in roots} == {"ru", "ua"}
        got: dict[str, Bucket] = {}
        n = ingest_tree(ov, roots, "overlay", got)
        assert n == 2
        assert got["ru:my bank"].cidrs.keys() == {"203.0.113.0/24"}
        assert got["ua:extra"].cidrs.keys() == {"198.51.100.0/24"}
        assert got["ua:extra"].via is False
    print("self-test ok")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sources", type=Path, action="append", default=[], help="Official or extra sources.json (repeatable)")
    ap.add_argument("--overlay", type=Path, default=ROOT / "overlay")
    ap.add_argument("--tree", type=Path, help="Local tree instead of git clone")
    ap.add_argument("--tree-name", default="local")
    ap.add_argument("--root", action="append", default=[], help="Folder under the tree (repeatable)")
    ap.add_argument("--out", type=Path, default=ROOT)
    ap.add_argument("--cache", type=Path, default=ROOT / ".cache")
    ap.add_argument("--lock", type=Path, default=HERE / "lock.json")
    ap.add_argument("--check-upstream", action="store_true", help="Exit 0 if git refs match lock.json, else 2")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        self_test()
        return 0

    source_paths = args.sources or [HERE / "sources.json", args.overlay / "sources.json"]
    srcs = load_source_files(source_paths)

    if args.check_upstream:
        if args.tree:
            print("check-upstream does not apply with --tree", file=sys.stderr)
            return 2
        print("ls-remote sources", file=sys.stderr)
        shas = collect_shas(srcs)
        old = read_lock(args.lock)
        if shas and shas == old:
            print("upstream unchanged")
            return 0
        print("upstream changed")
        return 2

    buckets: dict[str, Bucket] = {}
    source_labels: list[str] = []
    shas: dict[str, str] = {}

    if args.tree:
        roots = normalize_roots(args.root)
        ingest_tree(args.tree, roots, args.tree_name, buckets)
        source_labels.append(args.tree_name)
    else:
        if not srcs:
            print("no sources", file=sys.stderr)
            return 2
        for src in srcs:
            url = src["git"]
            ref = src.get("ref", "main")
            roots = normalize_roots(src.get("roots") or [])
            name = src["name"]
            dest = args.cache / name
            sparse = src.get("sparse")
            print(f"clone {url}@{ref} → {dest}", file=sys.stderr)
            git_clone(url, ref, dest, sparse)
            shas[name] = git_head(dest)
            n = ingest_tree(dest, roots, name, buckets)
            print(f"  {n} routes from {name}", file=sys.stderr)
            source_labels.append(f"{name} {url}@{ref}")

    overlay_specs = overlay_roots(args.overlay)
    if overlay_specs:
        n = ingest_tree(args.overlay, overlay_specs, "overlay", buckets)
        print(f"  {n} routes from overlay", file=sys.stderr)
        if n:
            source_labels.append("overlay")

    write_lists(args.out, list(buckets.values()), source_labels)
    if shas:
        write_lock(args.lock, shas)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as e:
        print(f"git failed: {e}", file=sys.stderr)
        sys.exit(1)
