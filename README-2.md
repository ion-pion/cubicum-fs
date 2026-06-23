# ✦ Cubicum FS

**A Z7³ Toroidal Filesystem Layer with Eight Roots**

> *Every tree has one root. Every cube has eight.*

[![Zenodo](https://img.shields.io/badge/Zenodo-Published-blue)](https://zenodo.org)
[![License](https://img.shields.io/badge/License-MIT-violet)]()
[![Phase](https://img.shields.io/badge/Phase-0%20%E2%80%94%20Proof%20of%20Concept-gold)]()

---

## What is Cubicum FS?

Cubicum FS is a filesystem abstraction layer built on the **Z7³ toroidal address space** — a 343-node lattice (7×7×7) where coordinates wrap continuously in all three dimensions.

Unlike conventional filesystems organised as single-rooted hierarchies, Cubicum FS uses **eight permanent roots** — the corners of the cube — as anchors. No file is ever more than **3 steps** from any root. The space has no periphery: on a torus, the edge folds back into the centre.

```
Conventional FS:        Cubicum FS:
                        
/                       α(0,0,0)  β(6,0,0)  γ(0,6,0)  δ(0,0,6)
├── home/               ε(6,6,0)  ζ(6,0,6)  η(0,6,6)  θ(6,6,6)
│   └── user/
│       └── docs/                 343 nodes. 8 roots.
│           └── file.txt          No hierarchy. Only position.
```

---

## How it works

Every file is assigned a coordinate **(x, y, z)** derived from its metadata:

| Axis | Meaning | Values |
|------|---------|--------|
| X | Project / context | hash(parent folder) mod 7 |
| Y | File type | 0–2: audio/video · 3–4: text/doc · 5–6: code/binary |
| Z | Lifecycle state | 0–2: draft · 3–4: active · 5–6: archive |

Files navigate by **toroidal distance** — not path strings.

---

## Quick Start

Zero dependencies. Python 3 only.

```bash
# Index a folder
python3 cubicum.py index ~/documents

# List all nodes
python3 cubicum.py ls

# Get files at coordinate
python3 cubicum.py get 3 1 5

# Find by name
python3 cubicum.py find notes

# Show the 8 roots
python3 cubicum.py roots

# Show neighbor nodes
python3 cubicum.py neighbors 3 1 5

# Burn session (clear non-corner nodes)
python3 cubicum.py burn

# Show what survived burn — the Ash
python3 cubicum.py ash

# Statistics
python3 cubicum.py stats
```

---

## Node Types

| Type | Count | Description |
|------|-------|-------------|
| CORNER | 8 | The eight roots. Permanent. Ash survives here. |
| EDGE | 60 | Near two roots simultaneously. |
| FACE | 150 | Working space. Session files. |
| INNER | 125 | Deep work. Burns completely at session end. |

---

## The Burn Protocol

At session end, Cubicum FS clears nodes by topology:

```
🔥 Inner nodes  (125) — burn completely
🔥 Face nodes   (150) — burn
🔥 Edge nodes   ( 60) — configurable
✦ Corner nodes (  8) — never burn → Ash
```

*The coordinates survive. The geometry survives.*  
*Salamandra knows where things were — not what they were.*

---

## Architecture

```
┌─────────────────────────────────┐
│         Applications            │  Layer 4 — see only (x,y,z)
├─────────────────────────────────┤
│       Cubicum Engine            │  Layer 3 — Z7³ index, routing, Burn
│    Z7³ · 343 nodes · 8 roots   │
├─────────────────────────────────┤
│        FS Adapters              │  Layer 2 — pluggable per filesystem
├────────┬────────┬───────┬───────┤
│  NTFS  │  ext4  │ APFS  │ F2FS  │  Layer 1 — untouched real filesystems
└────────┴────────┴───────┴───────┘
```

**Interoperability is geometric.**  
A file at (3,1,5) on Windows and (3,1,5) on Linux are the same node.  
No protocol negotiation. No mounting. Proximity in Z7³ IS the relationship.

---

## First Real-World Test

Tested on **Samsung Galaxy A15 · Android 14 · Termux · June 2026**

```
Total files indexed : 7,309
Nodes occupied      : 39 / 343  (11%)
Top file type       : .obn (2,498 — NOREBO Oberon modules)
```

The first file ever indexed in a Cubicum FS volume:  
`retele-mesh-constiinta-difuza.docx` → `(5,4,0) FACE ε`

---

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| 0 | ✅ Done | Python proof of concept. Index + query. Android tested. |
| 1 | 🔜 Next | FUSE driver. Mount as real volume. `cd /cubicum/3/1/5` |
| 2 | 📋 Planned | Cross-platform. Same Z7³ index on Windows + Linux + Android. |
| 3 | 📋 Planned | Burn automation. Session-end cleanup. Ash persistence. |
| 4 | 💡 Concept | 3D navigable interface. Visual cube. Touch navigation. |
| 5 | 🌀 Vision | Sanskrit-derived language as native Z7³ interface. |

---

## Research

Published on Zenodo:  
**Cubicum FS: A Z7³ Toroidal Filesystem Layer with Eight Roots**  
*Ion Pion + Claude Sonnet 4.6 · June 23, 2026*

Part of the **Cubicum ecosystem**:
- [Cubicum Synth](https://github.com/ion-pion/cubicum-synth) — Z7³ synthesizer
- [ILYRIUM cipher](https://github.com/ion-pion/ilyrium-cifer) — toroidal cryptography
- [Walkie-talkie Z7](https://github.com/ion-pion/walkie-talkie-z7) — Z7 communications
- [Oberon-Termux](https://github.com/ion-pion/oberon-termux) — Oberon on Android

---

## Six Faces of the Cube

| Face | Domain |
|------|--------|
| 1 | Files — Cubicum FS |
| 2 | Sound — Cubicum Synth |
| 3 | Weather — Cubicum Meteo |
| 4 | Communications — Walkie-talkie Z7 |
| 5 | Cryptography — ILYRIUM |
| 6 | ??? — open |

*Same interior. Six interfaces to the world.*

---

## License

MIT — open source, open science.

---

**Jahbalon Research · Iași, Romania · 2026**  
*E pur si torque.*
