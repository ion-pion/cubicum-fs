#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║  CUBICUM FS — Phase 0                        ║
║  Z7³ Toroidal Filesystem Layer               ║
║  Jahbalon Research · E pur si torque         ║
╚══════════════════════════════════════════════╝

Usage:
  python cubicum.py index <folder>    — index a folder into Z7³
  python cubicum.py get <x> <y> <z>  — get file at coordinate
  python cubicum.py ls                — list all indexed nodes
  python cubicum.py find <name>       — find file by name
  python cubicum.py neighbors <x> <y> <z> — show neighbor nodes
  python cubicum.py roots             — show the 8 corner roots
  python cubicum.py burn              — burn session (clear non-corners)
  python cubicum.py ash               — show what survived burn
  python cubicum.py stats             — show index statistics
"""

import os
import sys
import sqlite3
import hashlib
import time
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
DB_PATH = os.path.expanduser("~/.cubicum.db")
VERSION = "0.1.0"

# Z7³ modulus
Z7 = 7

# File type → Y axis mapping
TYPE_MAP = {
    # Audio/Video → 0,1,2
    'mp3':0,'wav':0,'ogg':0,'flac':0,'aac':0,
    'mp4':1,'mkv':1,'avi':1,'mov':1,'webm':1,
    'mid':2,'midi':2,'cubicum':2,'z7':2,
    # Text/Doc → 3,4
    'txt':3,'md':3,'rst':3,'csv':3,
    'pdf':4,'doc':4,'docx':4,'html':4,'htm':4,
    # Code/Binary → 5,6
    'py':5,'js':5,'ts':5,'c':5,'h':5,'ob':5,
    'sh':6,'bin':6,'exe':6,'apk':6,'so':6,
}

# Lifecycle → Z axis
def lifecycle(mtime: float) -> int:
    age_days = (time.time() - mtime) / 86400
    if age_days < 7:   return 0  # hot/draft
    if age_days < 30:  return 1
    if age_days < 90:  return 2
    if age_days < 180: return 3  # active
    if age_days < 365: return 4
    if age_days < 730: return 5  # archive
    return 6                     # deep archive

# ─────────────────────────────────────────────
#  Z7³ MATH
# ─────────────────────────────────────────────
def toro_dist_1d(a: int, b: int) -> int:
    """Toroidal distance on single axis."""
    d = abs(a - b)
    return min(d, Z7 - d)

def toro_dist(p1: tuple, p2: tuple) -> int:
    """Toroidal distance in Z7³."""
    return sum(toro_dist_1d(p1[i], p2[i]) for i in range(3))

CORNERS = [
    (0,0,0),(6,0,0),(0,6,0),(0,0,6),
    (6,6,0),(6,0,6),(0,6,6),(6,6,6)
]

CORNER_NAMES = ['α','β','γ','δ','ε','ζ','η','θ']

def nearest_root(coord: tuple) -> tuple:
    """Find nearest corner root to a coordinate."""
    best = min(CORNERS, key=lambda c: toro_dist(coord, c))
    idx = CORNERS.index(best)
    return best, CORNER_NAMES[idx], toro_dist(coord, best)

def node_type(coord: tuple) -> str:
    """Classify node: corner / edge / face / inner."""
    extremes = sum(1 for v in coord if v == 0 or v == 6)
    if extremes == 3: return 'CORNER'
    if extremes == 2: return 'EDGE'
    if extremes == 1: return 'FACE'
    return 'INNER'

def coord_from_file(filepath: str) -> tuple:
    """Compute Z7³ coordinate from file metadata."""
    p = Path(filepath)
    stat = p.stat()

    # X = project (hash of parent folder name mod 7)
    parent_hash = int(hashlib.md5(p.parent.name.encode()).hexdigest(), 16)
    x = parent_hash % Z7

    # Y = file type
    ext = p.suffix.lstrip('.').lower()
    y = TYPE_MAP.get(ext, 3)  # default: text/doc

    # Z = lifecycle from modification time
    z = lifecycle(stat.st_mtime)

    return (x, y, z)

def get_neighbors(coord: tuple) -> list:
    """Get all 6 direct neighbors (±1 on each axis, toroidal)."""
    x, y, z = coord
    return [
        ((x+1)%Z7, y, z), ((x-1)%Z7, y, z),
        (x, (y+1)%Z7, z), (x, (y-1)%Z7, z),
        (x, y, (z+1)%Z7), (x, y, (z-1)%Z7),
    ]

# ─────────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────────
def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            x INTEGER, y INTEGER, z INTEGER,
            path TEXT, name TEXT, ext TEXT,
            size INTEGER, mtime REAL,
            node_type TEXT, root_name TEXT,
            is_ash INTEGER DEFAULT 0,
            indexed_at REAL,
            PRIMARY KEY (x, y, z, path)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ash (
            x INTEGER, y INTEGER, z INTEGER,
            name TEXT, burned_at REAL,
            PRIMARY KEY (x, y, z, name)
        )
    """)
    conn.commit()
    return conn

# ─────────────────────────────────────────────
#  COLORS (ANSI)
# ─────────────────────────────────────────────
GOLD   = '\033[93m'
VIOLET = '\033[95m'
CYAN   = '\033[96m'
GREEN  = '\033[92m'
RED    = '\033[91m'
DIM    = '\033[2m'
BOLD   = '\033[1m'
RESET  = '\033[0m'

def gold(s):   return f"{GOLD}{s}{RESET}"
def violet(s): return f"{VIOLET}{s}{RESET}"
def cyan(s):   return f"{CYAN}{s}{RESET}"
def dim(s):    return f"{DIM}{s}{RESET}"
def bold(s):   return f"{BOLD}{s}{RESET}"
def red(s):    return f"{RED}{s}{RESET}"
def green(s):  return f"{GREEN}{s}{RESET}"

def coord_str(c): return gold(f"({c[0]},{c[1]},{c[2]})")

def header():
    print(f"""
{violet('╔══════════════════════════════════════════╗')}
{violet('║')} {gold('✦ CUBICUM FS')} {dim('· Z7³ · Phase 0 · v'+VERSION)}  {violet('║')}
{violet('║')} {dim('Jahbalon Research · E pur si torque')}    {violet('║')}
{violet('╚══════════════════════════════════════════╝')}""")

# ─────────────────────────────────────────────
#  COMMANDS
# ─────────────────────────────────────────────
def cmd_index(folder: str):
    """Index all files in a folder into Z7³."""
    folder = os.path.expanduser(folder)
    if not os.path.isdir(folder):
        print(red(f"Not a directory: {folder}"))
        return

    header()
    print(f"\n{violet('Indexing')} {cyan(folder)}\n")

    conn = db_connect()
    count = 0
    skipped = 0

    for root, dirs, files in os.walk(folder):
        # Skip hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for fname in files:
            if fname.startswith('.'): continue
            fpath = os.path.join(root, fname)
            try:
                coord = coord_from_file(fpath)
                stat = Path(fpath).stat()
                ntype = node_type(coord)
                root_coord, root_name, root_dist = nearest_root(coord)
                ext = Path(fpath).suffix.lstrip('.').lower()

                conn.execute("""
                    INSERT OR REPLACE INTO nodes
                    (x,y,z,path,name,ext,size,mtime,node_type,root_name,indexed_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    coord[0], coord[1], coord[2],
                    fpath, fname, ext,
                    stat.st_size, stat.st_mtime,
                    ntype, root_name,
                    time.time()
                ))
                count += 1

                # Show progress
                type_color = {'CORNER':gold,'EDGE':violet,'FACE':cyan,'INNER':dim}
                tc = type_color.get(ntype, dim)
                print(f"  {coord_str(coord)} {tc(ntype[:4]):<4} {root_name} "
                      f"{dim(fname[:40])}")

            except (PermissionError, OSError):
                skipped += 1

    conn.commit()
    conn.close()

    print(f"\n{green('✦ Indexed:')} {gold(str(count))} files  "
          f"{dim(f'({skipped} skipped)')}")
    print(f"{dim('DB: '+DB_PATH)}\n")


def cmd_get(x: int, y: int, z: int):
    """Get all files at coordinate (x,y,z)."""
    header()
    coord = (x, y, z)
    ntype = node_type(coord)
    root_coord, root_name, root_dist = nearest_root(coord)

    print(f"\n{violet('Node')} {coord_str(coord)}")
    print(f"  Type    : {gold(ntype)}")
    print(f"  Root    : {gold(root_name)} {dim(str(root_coord))} "
          f"distance {gold(str(root_dist))}")

    conn = db_connect()
    rows = conn.execute(
        "SELECT name, path, size, ext FROM nodes WHERE x=? AND y=? AND z=?",
        (x, y, z)
    ).fetchall()
    conn.close()

    if not rows:
        print(f"\n  {dim('No files at this coordinate.')}")
        print(f"  {dim('Neighbors:')}")
        for n in get_neighbors(coord):
            print(f"    {coord_str(n)}")
    else:
        print(f"\n  {gold(str(len(rows)))} file(s):\n")
        for name, path, size, ext in rows:
            sz = f"{size//1024}K" if size > 1024 else f"{size}B"
            print(f"  {cyan(name):<40} {dim(sz)}")
            print(f"    {dim(path)}\n")


def cmd_ls():
    """List all indexed nodes."""
    header()
    conn = db_connect()
    rows = conn.execute("""
        SELECT x, y, z, COUNT(*) as cnt, node_type, root_name
        FROM nodes
        GROUP BY x, y, z
        ORDER BY x, y, z
    """).fetchall()
    conn.close()

    if not rows:
        print(f"\n  {dim('Index is empty. Run: python cubicum.py index <folder>')}")
        return

    print(f"\n{'Coord':<14} {'Type':<8} {'Root':<4} {'Files'}")
    print(dim('─' * 40))
    type_color = {'CORNER':gold,'EDGE':violet,'FACE':cyan,'INNER':dim}
    for x,y,z,cnt,ntype,rname in rows:
        tc = type_color.get(ntype, dim)
        print(f"  {coord_str((x,y,z))}  {tc(ntype[:6]):<14} "
              f"{gold(rname):<6} {cyan(str(cnt))}")
    print(dim('─' * 40))
    print(f"  {gold(str(len(rows)))} nodes occupied\n")


def cmd_find(name: str):
    """Find files by name fragment."""
    header()
    conn = db_connect()
    rows = conn.execute(
        "SELECT x,y,z,name,path,size FROM nodes WHERE name LIKE ?",
        (f'%{name}%',)
    ).fetchall()
    conn.close()

    print(f"\n{violet('Search:')} {cyan(name)}\n")
    if not rows:
        print(f"  {dim('Nothing found.')}")
        return
    for x,y,z,fname,path,size in rows:
        sz = f"{size//1024}K" if size > 1024 else f"{size}B"
        print(f"  {coord_str((x,y,z))}  {cyan(fname):<36} {dim(sz)}")
        print(f"    {dim(path)}\n")


def cmd_neighbors(x: int, y: int, z: int):
    """Show neighbor nodes and their contents."""
    header()
    coord = (x,y,z)
    print(f"\n{violet('Neighbors of')} {coord_str(coord)}\n")

    conn = db_connect()
    for n in get_neighbors(coord):
        rows = conn.execute(
            "SELECT name FROM nodes WHERE x=? AND y=? AND z=?", n
        ).fetchall()
        dist = toro_dist(coord, n)
        ntype = node_type(n)
        files = f"{gold(str(len(rows)))} files" if rows else dim("empty")
        print(f"  {coord_str(n)} {dim(ntype[:4]):<8} dist={gold(str(dist))} {files}")
        for (fname,) in rows[:3]:
            print(f"    {dim('·')} {cyan(fname)}")
    conn.close()
    print()


def cmd_roots():
    """Show the 8 corner roots and their contents."""
    header()
    print(f"\n{gold('✦ The Eight Roots — Corner Nodes')}\n")

    conn = db_connect()
    for i, (c, name) in enumerate(zip(CORNERS, CORNER_NAMES)):
        rows = conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE x=? AND y=? AND z=?", c
        ).fetchone()
        ash_rows = conn.execute(
            "SELECT COUNT(*) FROM ash WHERE x=? AND y=? AND z=?", c
        ).fetchone()
        count = rows[0]
        ash_count = ash_rows[0]

        status = gold(f"{count} files") if count else dim("empty")
        ash_status = f"  {red('ash: '+str(ash_count))}" if ash_count else ""

        print(f"  {gold(name)} {dim(str(c))}  {status}{ash_status}")
    conn.close()
    print()


def cmd_burn():
    """Burn session — clear non-corner nodes, preserve ash at corners."""
    header()
    print(f"\n{red('🔥 BURN PROTOCOL INITIATED')}\n")

    conn = db_connect()

    # Save corner files to ash before burning
    corner_coords = [(c[0],c[1],c[2]) for c in CORNERS]
    for c in CORNERS:
        rows = conn.execute(
            "SELECT name FROM nodes WHERE x=? AND y=? AND z=?", c
        ).fetchall()
        for (fname,) in rows:
            conn.execute(
                "INSERT OR REPLACE INTO ash (x,y,z,name,burned_at) VALUES (?,?,?,?,?)",
                (c[0],c[1],c[2], fname, time.time())
            )

    # Count what will burn
    total = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    corners_count = conn.execute(
        f"SELECT COUNT(*) FROM nodes WHERE (x,y,z) IN "
        f"({','.join(['('+str(c[0])+','+str(c[1])+','+str(c[2])+')' for c in CORNERS])})"
    ).fetchone()[0]
    burn_count = total - corners_count

    # Burn by topology
    for ntype, label, color in [
        ('INNER', 'Inner nodes', red),
        ('FACE',  'Face nodes',  violet),
        ('EDGE',  'Edge nodes',  cyan),
    ]:
        n = conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE node_type=?", (ntype,)
        ).fetchone()[0]
        conn.execute("DELETE FROM nodes WHERE node_type=?", (ntype,))
        print(f"  🔥 {color(label):<20} {dim(str(n)+' burned')}")

    conn.commit()
    remaining = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    ash_total = conn.execute("SELECT COUNT(*) FROM ash").fetchone()[0]
    conn.close()

    print(f"\n  {gold('✦ Corners preserved:')} {gold(str(remaining))} nodes")
    print(f"  {gold('✦ Ash accumulated:')}  {gold(str(ash_total))} records")
    print(f"\n  {dim('The coordinates remain. The geometry survives.')}")
    print(f"  {dim('Salamandra knows where things were.')}\n")


def cmd_ash():
    """Show what survived burn — the ash at corners."""
    header()
    conn = db_connect()
    rows = conn.execute(
        "SELECT x,y,z,name,burned_at FROM ash ORDER BY burned_at DESC"
    ).fetchall()
    conn.close()

    print(f"\n{gold('✦ Ash — What Survived')}\n")
    if not rows:
        print(f"  {dim('No ash yet. Run burn first.')}")
        return
    for x,y,z,name,bat in rows:
        dt = datetime.fromtimestamp(bat).strftime('%Y-%m-%d %H:%M')
        print(f"  {coord_str((x,y,z))}  {cyan(name):<36} {dim(dt)}")
    print()


def cmd_stats():
    """Show index statistics."""
    header()
    conn = db_connect()

    total = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    by_type = conn.execute(
        "SELECT node_type, COUNT(*) FROM nodes GROUP BY node_type"
    ).fetchall()
    by_ext = conn.execute(
        "SELECT ext, COUNT(*) FROM nodes GROUP BY ext ORDER BY COUNT(*) DESC LIMIT 8"
    ).fetchall()
    occupied = conn.execute(
        "SELECT COUNT(DISTINCT x||','||y||','||z) FROM nodes"
    ).fetchone()[0]
    ash_count = conn.execute("SELECT COUNT(*) FROM ash").fetchone()[0]
    conn.close()

    print(f"\n{gold('✦ Cubicum Index Statistics')}\n")
    print(f"  Total files    : {gold(str(total))}")
    print(f"  Nodes occupied : {gold(str(occupied))} / 343")
    print(f"  Ash records    : {gold(str(ash_count))}")
    print(f"\n  {violet('By node type:')}")

    type_color = {'CORNER':gold,'EDGE':violet,'FACE':cyan,'INNER':dim}
    for ntype, cnt in by_type:
        tc = type_color.get(ntype, dim)
        bar = '█' * min(int(cnt / max(total,1) * 30), 30)
        print(f"    {tc(ntype):<8}  {gold(str(cnt)):<6} {dim(bar)}")

    print(f"\n  {violet('Top file types:')}")
    for ext, cnt in by_ext:
        print(f"    .{cyan(ext):<8} {gold(str(cnt))}")
    print()


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def usage():
    header()
    print(f"""
{violet('Commands:')}

  {gold('index')} <folder>         Index a folder into Z7³
  {gold('get')} <x> <y> <z>       Get files at coordinate
  {gold('ls')}                     List all occupied nodes
  {gold('find')} <name>            Search files by name
  {gold('neighbors')} <x> <y> <z> Show neighbor nodes
  {gold('roots')}                  Show the 8 corner roots
  {gold('burn')}                   Burn session (clear non-corners)
  {gold('ash')}                    Show what survived burn
  {gold('stats')}                  Index statistics

{violet('Examples:')}

  python cubicum.py index ~/storage/shared
  python cubicum.py index ~/documents
  python cubicum.py ls
  python cubicum.py get 3 1 5
  python cubicum.py neighbors 3 1 5
  python cubicum.py find notes
  python cubicum.py roots
  python cubicum.py burn
  python cubicum.py ash

{dim('DB stored at: '+DB_PATH)}
""")

def main():
    args = sys.argv[1:]
    if not args:
        usage()
        return

    cmd = args[0].lower()

    if cmd == 'index' and len(args) >= 2:
        cmd_index(args[1])
    elif cmd == 'get' and len(args) == 4:
        cmd_get(int(args[1]), int(args[2]), int(args[3]))
    elif cmd == 'ls':
        cmd_ls()
    elif cmd == 'find' and len(args) >= 2:
        cmd_find(args[1])
    elif cmd == 'neighbors' and len(args) == 4:
        cmd_neighbors(int(args[1]), int(args[2]), int(args[3]))
    elif cmd == 'roots':
        cmd_roots()
    elif cmd == 'burn':
        cmd_burn()
    elif cmd == 'ash':
        cmd_ash()
    elif cmd == 'stats':
        cmd_stats()
    else:
        usage()

if __name__ == '__main__':
    main()
