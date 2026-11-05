# Courserefresh product film

A Remotion-built product film for Courserefresh. Eight React scenes follow a source change from discovery through policy, lesson and quiz updates, learner support, author controls, and the morning digest. The finished composition is 1920 × 1080 at 24 fps, with narration only and no background music. Its visual system uses a bright, editorial palette, translucent liquid-glass surfaces, controlled prismatic light, and short glass-pane wipes with a prismatic light edge between chapters.

## Render

```sh
npm ci
npm run render:video
```

The three-minute MP4 is written to `output/courserefresh-demo-3min.mp4` and copied into `viz/public/` for the GitHub Pages build. The selected narration and source text live in `public/audio/` and `src/remotion/narration.ts`.

Rendering uses the pinned Chromium and FFmpeg packages in this project. The reusable Remotion composition is `CourserefreshDemo`; `npm run studio` starts the scene editor.
