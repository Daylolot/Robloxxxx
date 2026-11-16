#!/usr/bin/env python3
"""Контроль диска для автопилота KONTUR (только стандартная библиотека).

Если свободно меньше порога (по умолчанию 5 ГБ):
  1. сохраняет последние версии в GitHub (commit + push в origin/main);
  2. ТОЛЬКО после проверки, что коммит есть на GitHub, удаляет старые карты, тяжёлые
     макеты и снимки проверок (всё это остаётся в истории git, вернуть: git checkout origin/main -- <путь>);
  3. чистит безопасный мусор: __pycache__, .DS_Store, *.blend1, старые логи Roblox, временные файлы автопилота;
  4. если места всё ещё мало, ничего чужого не трогает, а выводит список крупнейших потребителей.
Запускать перед каждым шагом автопилота: скрипт идемпотентен («по кругу при необходимости»).

Использование (из корня репозитория):
  python3 docs/evolution/disk_guard.py            # пробный прогон, ничего не меняет
  python3 docs/evolution/disk_guard.py --apply    # реально выполнить
Опции: --min-free-gb 5  --target-free-gb 7  --keep-maps 2  --no-push

Никогда не удаляет: Backups/, .git, venv, CLAUDE.md, AGENTS.md, исходники (*.luau, *.py), docs/, sessions/,
файлы с несохранёнными правками или не попавшие на GitHub, базовую карту сборки Kontur_Office_v26_Mirror*.
"""
import argparse, datetime, os, re, shutil, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LOG = REPO / "docs" / "evolution" / "disk_guard.log"
GB = 1024 ** 3
BIG_FILE = 95 * 1024 * 1024  # лимит GitHub 100 МБ
TRAILER = "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
ADD_PATHS = ["maps", "sources", "models", "docs", "sessions", "CHANGELOG.md", "README.md", "START_HERE.md", ".claude"]
PROTECTED_MAP = re.compile(r"Kontur_Office_v26_Mirror")


def free_gb() -> float:
    return shutil.disk_usage(REPO).free / GB


def log(msg: str) -> None:
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line)
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def git(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=check)


def size_of(p: Path) -> int:
    try:
        return p.stat().st_size
    except OSError:
        return 0


def push_latest(apply: bool) -> bool:
    """Коммит и push. True, если локальный HEAD гарантированно есть на GitHub."""
    if git("rev-parse", "--is-inside-work-tree").returncode != 0:
        log("не git-репозиторий: push невозможен")
        return False
    if not apply:
        log("[пробный] git add (maps, sources, models, docs, sessions, .claude) + commit + push origin main")
        return False
    for path in ADD_PATHS:
        if (REPO / path).exists():
            git("add", "--", path)
    # слишком большие файлы GitHub отвергнет: выводим из индекса
    for name in git("diff", "--cached", "--name-only").stdout.splitlines():
        p = REPO / name
        if p.exists() and (size_of(p) > BIG_FILE or name.endswith(".lock")):
            git("reset", "-q", "--", name)
            log(f"не отправляю (слишком большой или .lock): {name}")
    if git("diff", "--cached", "--quiet").returncode != 0:
        msg = f"Автопилот: сохранить версии перед очисткой диска ({datetime.date.today()})\n\n{TRAILER}"
        r = git("commit", "-m", msg)
        if r.returncode != 0:
            log("commit не удался: " + (r.stderr or r.stdout).strip()[:300])
            return False
    r = git("push", "origin", "HEAD:main")
    if r.returncode != 0:
        log("push не удался: " + (r.stderr or r.stdout).strip()[:300])
        return False
    git("fetch", "origin", "main")
    head = git("rev-parse", "HEAD").stdout.strip()
    remote = git("rev-parse", "origin/main").stdout.strip()
    ok = head == remote or git("merge-base", "--is-ancestor", head, "origin/main").returncode == 0
    log(f"push {'подтверждён' if ok else 'НЕ подтверждён'}: HEAD {head[:8]}, origin/main {remote[:8]}")
    return ok


def is_safe_to_delete(rel: str) -> bool:
    """Файл отслеживается, не изменён и есть в origin/main."""
    if git("ls-files", "--error-unmatch", "--", rel).returncode != 0:
        return False
    if git("status", "--porcelain", "--", rel).stdout.strip():
        return False
    return git("cat-file", "-e", f"origin/main:{rel}").returncode == 0


def delete_candidates() -> list:
    """Список (путь, причина) файлов, которые можно убрать после подтверждённого push."""
    out = []
    maps = sorted((REPO / "maps").glob("Kontur_Office_v*.rbxl")) if (REPO / "maps").exists() else []
    versions = {}
    for p in maps:
        m = re.search(r"_v(\d+)", p.name)
        if m and not PROTECTED_MAP.search(p.name):
            versions.setdefault(int(m.group(1)), []).append(p)
    keep = sorted(versions)[-KEEP_MAPS:]
    for v, files in versions.items():
        if v not in keep:
            out += [(f, f"старая карта v{v}") for f in files]
    for p in (REPO / "maps").glob("*.rbxl") if (REPO / "maps").exists() else []:
        if p.name.startswith(("Office_v", "Kontur_Office_v17")):
            out.append((p, "архивная карта"))
    for sub in ("models", "sources"):
        base = REPO / sub
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            ext = p.suffix.lower()
            in_checks = "checks" in p.parts or "preview" in p.parts
            if ext in (".blend", ".mp4", ".mov", ".gif", ".png", ".jpg") and (size_of(p) > 1_000_000 or in_checks):
                # самый свежий макет каждого модуля оставляем
                if sub == "models" and is_latest_in_module(p):
                    continue
                out.append((p, "тяжёлый макет или снимок проверки"))
    seen, unique = set(), []
    for p, why in out:
        if p not in seen:
            seen.add(p)
            unique.append((p, why))
    return unique


def is_latest_in_module(p: Path) -> bool:
    """models/<имя>-vNN: оставить папку с наибольшим NN среди одноимённых."""
    rel = p.relative_to(REPO / "models")
    m = re.match(r"(.+)-v(\d+)$", rel.parts[0])
    if not m:
        return True
    same = [int(re.match(r".+-v(\d+)$", d.name).group(1)) for d in (REPO / "models").iterdir()
            if d.is_dir() and re.match(rf"{re.escape(m.group(1))}-v\d+$", d.name)]
    return int(m.group(2)) == max(same)


def junk(apply: bool) -> int:
    freed = 0
    for pat in ("__pycache__",):
        for d in REPO.rglob(pat):
            if ".git" in d.parts or "venv" in d.parts:
                continue
            n = sum(size_of(f) for f in d.rglob("*") if f.is_file())
            freed += n
            if apply:
                shutil.rmtree(d, ignore_errors=True)
    for pat in ("*.blend1", ".DS_Store"):
        for f in REPO.rglob(pat):
            if ".git" in f.parts:
                continue
            freed += size_of(f)
            if apply:
                f.unlink(missing_ok=True)
    logs = Path.home() / "Library" / "Logs" / "Roblox"
    if logs.exists():
        limit = time.time() - 2 * 86400
        for f in logs.rglob("*"):
            try:
                if f.is_file() and f.stat().st_mtime < limit:
                    freed += f.stat().st_size
                    if apply:
                        f.unlink(missing_ok=True)
            except OSError:
                pass
    tmp = Path("/private/tmp/claude-501/ev")
    if tmp.exists():
        for f in tmp.rglob("*"):
            if f.is_file():
                freed += size_of(f)
                if apply:
                    f.unlink(missing_ok=True)
    return freed


def top_consumers() -> None:
    log("Крупнейшие потребители места, которые я НЕ трогаю (решите сами):")
    cache = Path.home() / "Library" / "Caches"
    rows = []
    if cache.exists():
        for d in cache.iterdir():
            if d.is_dir():
                r = subprocess.run(["du", "-sk", str(d)], capture_output=True, text=True)
                try:
                    rows.append((int(r.stdout.split()[0]) * 1024, d.name))
                except (ValueError, IndexError):
                    pass
    for n, name in sorted(rows, reverse=True)[:6]:
        log(f"  ~/Library/Caches/{name}: {n / GB:.1f} ГБ")


def main() -> int:
    global KEEP_MAPS
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--min-free-gb", type=float, default=5.0)
    ap.add_argument("--target-free-gb", type=float, default=7.0)
    ap.add_argument("--keep-maps", type=int, default=2, help="сколько последних номеров версий карт оставить")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args()
    KEEP_MAPS = a.keep_maps
    before = free_gb()
    if before >= a.min_free_gb:
        print(f"диск в порядке: свободно {before:.1f} ГБ (порог {a.min_free_gb} ГБ)")
        return 0
    log(f"МАЛО МЕСТА: свободно {before:.1f} ГБ < {a.min_free_gb} ГБ. Режим: {'ПРИМЕНИТЬ' if a.apply else 'пробный'}")

    # 1. безопасный мусор вне зависимости от GitHub
    freed = junk(a.apply)
    log(f"шаг 1 мусор и старые логи Roblox: {freed / 1e6:.0f} МБ")

    # 2. GitHub и удаление старых версий
    pushed = False if a.no_push else push_latest(a.apply)
    cands = delete_candidates()
    total = 0
    for p, why in cands:
        rel = str(p.relative_to(REPO))
        ok = pushed and is_safe_to_delete(rel)
        if not a.apply:
            log(f"[пробный] удалил бы: {rel} ({size_of(p) / 1e6:.1f} МБ, {why})")
            total += size_of(p)
            continue
        if not ok:
            continue
        total += size_of(p)
        p.unlink(missing_ok=True)
        if free_gb() >= a.target_free_gb:
            break
    log(f"шаг 2 старые версии: {'можно освободить' if not a.apply else 'удалено'} {total / 1e6:.0f} МБ"
        + ("" if pushed or not a.apply else ""))
    if a.apply and not pushed:
        log("push не подтверждён: отслеживаемые файлы НЕ удалялись (защита от потери данных)")

    after = free_gb()
    log(f"итог: свободно {before:.1f} → {after:.1f} ГБ")
    if after < a.min_free_gb:
        log("места всё ещё мало: проект столько не освобождает")
        top_consumers()
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
