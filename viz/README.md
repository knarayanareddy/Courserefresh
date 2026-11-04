# viz — Courserefresh web rendition

A React + Vite site presenting the Courserefresh course, recorded runs, lesson history, author console, and the three-minute narrated product film. The GitHub Pages build is self-contained apart from the downloadable MP4 asset.

## Published site

https://knarayanareddy.github.io/Courserefresh/

The `Deploy viz demo to GitHub Pages` workflow builds this project and publishes it for pushes to `main` or the active Arena feature branch. The Vite base path is configured for the repository URL.

## Build locally

```bash
cd viz && npm ci && npm run build
```

`dist/index.html` is the self-contained site shell; `dist/courserefresh-demo-3min.mp4` is the narrated film linked from the Product Film section.
