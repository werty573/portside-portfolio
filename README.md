# Portside Digital: portfolio

The site to send to clients: a 3D, real-data model of **Trinidad & Tobago** you fly over to see each build, then pricing, process and WhatsApp.

## What's in it

- **A cartoon 3D Trinidad & Tobago from real Earth data.** The real elevation and sea-floor depth (AWS Terrain Tiles) are turned into a low-poly toon map:
  - Flat-coloured height bands, a 4-step toon light ramp, and about 2,600 instanced trees.
  - Merged low-poly clouds.
  - A posterised sea whose bands follow the real bathymetry, with a white coastline outline and wave dashes.
  - It only loads about 0.75 MB of map data (`height.bin` + `data.png`), with no shadows, no environment map and no satellite texture, so it stays light on phones.
- **Scroll story** (GSAP ScrollTrigger + Lenis). The camera descends from orbit and flies pin to pin, climbing over ridges between projects. Each project has a card with screenshots, features and a link to the live site.
- The eleven concept builds: Tamarind Table, Verbena Clinic, MAREA, Gilded Hour, Swirl & Pop, Soda, Sereine Skin Studio, Gloss Lab, Pulse Yard, Meridian Watch Co. and Leeward House.
- Card screenshots live in `assets/work/` (`<key>-d.jpg` 1200×750, `<key>-p.jpg` 480×1039). `node tools/capture-work.mjs <key> <live-url>` captures both.
- Mobile layout with lighter assets (2K imagery, half-res mesh, no shadows). Respects `prefers-reduced-motion`.

## Run it

Serve the folder (the terrain loads with `fetch`, so `file://` won't work):

```bash
python -m http.server 8000
```

Check it (console errors, plus screenshots at 1440×900 and 390×844):

```bash
npm install
npx playwright install chromium
node tools/check.mjs shots
```

## Rebuild the terrain

`tools/build_terrain.py` downloads the tiles (cached in `tools/cache/`), stitches and crops them to the islands, masks out Venezuela's coast, merges land and sea floor, and writes `assets/tt/`:

- `height.bin` and `data.png` (depth, land mask, elevation), which the site uses
- `sat.jpg`, `sat-m.jpg` and `normal.png`, which are only needed for a photoreal version and aren't committed

```bash
pip install numpy pillow scipy requests
python tools/build_terrain.py
```

## Credits

- Elevation and bathymetry: [AWS Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) (Mapzen/Tilezen; sources include SRTM, GMTED2010 and ETOPO1; [attribution](https://github.com/tilezen/joerd/blob/master/docs/attribution.md)).
- Coastline tracing: [Sentinel-2 cloudless 2016](https://s2maps.eu) by EOX IT Services GmbH (contains modified Copernicus Sentinel data 2016), CC BY 4.0.
- Libraries: Three.js r170 (incl. `BufferGeometryUtils`), GSAP 3.13 (ScrollTrigger, SplitText), Lenis. Fonts: Sora, Inter, JetBrains Mono (SIL OFL).
- Every project shown is a concept build for a fictional business.
