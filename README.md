# Portside Digital: portfolio

The site to send to clients: a 3D, real-data model of **Trinidad & Tobago** you fly over to see each build, then pricing, process and WhatsApp.

## What's in it

- **3D Trinidad & Tobago from real Earth data.** Elevation and sea-floor depth come from AWS Terrain Tiles, with Sentinel-2 satellite imagery draped on top. Heights are exaggerated ×3.2 so the Northern Range and Tobago's Main Ridge read from altitude.
- **Rendering** (Three.js):
  - Physically based terrain with a baked normal map and golden-hour sun shadows.
  - A sea whose colour follows the real bathymetry, with ripples, a sun glint, sky reflection and coastal foam.
  - Drifting cloud shadows, atmospheric haze and a physical sky.
- **Scroll story** (GSAP ScrollTrigger + Lenis). The camera descends from orbit and flies pin to pin, climbing over ridges between projects. Each project has a card with screenshots, features and a link to the live site.
- The seven concept builds: MAREA, Soda, Tamarind Table, Gloss Lab, Leeward House, Pulse Yard and Gilded Hour.
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

- `height.bin`
- `sat.jpg` and `sat-m.jpg`
- `normal.png`
- `data.png` (depth, land mask, elevation)

```bash
pip install numpy pillow scipy requests
python tools/build_terrain.py
```

## Credits

- Elevation and bathymetry: [AWS Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) (Mapzen/Tilezen; sources include SRTM, GMTED2010 and ETOPO1; [attribution](https://github.com/tilezen/joerd/blob/master/docs/attribution.md)).
- Imagery: [Sentinel-2 cloudless 2016](https://s2maps.eu) by EOX IT Services GmbH (contains modified Copernicus Sentinel data 2016), CC BY 4.0.
- Libraries: Three.js r170 (incl. the `Sky` addon), GSAP 3.13 (ScrollTrigger, SplitText), Lenis. Fonts: Sora, Inter, JetBrains Mono (SIL OFL).
- Every project shown is a concept build for a fictional business.
