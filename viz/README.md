# viz — the presentation layer

A React + Vite app that presents the real Courserefresh artifacts: the 10-slide
teacher-overload narrative, the recorded run views, the course with its real
version histories, and the author console with the verbatim hero-run digest.

This is a **demo view over the real artifacts** — the shipped console is
`app/serve.py` (one page, no scripts). Every number in this app is either
receipt-backed or explicitly labeled (`unmeasured`, or the dots slide's
"visual metaphor, not measured figures").

## Regenenerate the data from the repo's own artifacts

```bash
python3 viz/scripts/gen-mockdata.py   # rewrites viz/src/data/mockData.ts
```

## Build

```bash
cd viz && npm install && npm run build   # single-file output -> viz/dist/index.html
```

`dist/index.html` is the shipped demo artifact — a self-contained single file
that opens without a server.
