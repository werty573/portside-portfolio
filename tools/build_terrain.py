"""
Builds the Trinidad & Tobago terrain assets for the portfolio's 3D hero.

Sources (both open data, downloaded once and cached in tools/cache/):
  - Elevation + bathymetry: AWS Terrain Tiles (Terrarium encoding), https://registry.opendata.aws/terrain-tiles/
    (sources include SRTM, GMTED2010, ETOPO1 and others; see https://github.com/tilezen/joerd/blob/master/docs/attribution.md)
  - Imagery: Sentinel-2 cloudless 2016 by EOX IT Services GmbH, https://s2maps.eu, CC BY 4.0
    (contains modified Copernicus Sentinel data 2016)

Outputs (assets/tt/):
  height.bin   Int16 metres, 512x512, row-major from north-west (land + sea floor)
  sat.jpg      4096x4096 satellite colour; sat-m.jpg 2048x2048 for phones
  normal.png   2048x2048 tangent-space normals baked from the full-res DEM (with the scene's vertical exaggeration)
  data.png     1024x1024: R = sea depth (0..255 = 0..-600 m), G = land mask (soft), B = elevation (0..255 = 0..940 m)
  meta.json    bbox, sizes, max height
python tools/build_terrain.py
"""
import io, json, math, os, time
import numpy as np
import requests
from PIL import Image, ImageFilter
from scipy.ndimage import gaussian_filter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, 'tools', 'cache')
OUT = os.path.join(ROOT, 'assets', 'tt')
os.makedirs(CACHE, exist_ok=True); os.makedirs(OUT, exist_ok=True)

W, E, S, N = -61.93, -60.47, 10.02, 11.38          # Trinidad + Tobago, with a little sea around them
EXAG = 3.2                                           # vertical exaggeration used by the scene (must match index.html)
UA = {'User-Agent': 'portside-portfolio-terrain-build/1.0 (one-off download)'}

def lon2x(lon, z): return (lon + 180) / 360 * 2 ** z
def lat2y(lat, z):
    r = math.radians(lat)
    return (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 2 ** z

def fetch(url, path):
    if os.path.exists(path): return open(path, 'rb').read()
    for attempt in range(4):
        try:
            r = requests.get(url, headers=UA, timeout=30)
            if r.status_code == 200:
                open(path, 'wb').write(r.content); time.sleep(.05); return r.content
        except requests.RequestException:
            pass
        time.sleep(1 + attempt)
    raise RuntimeError('failed ' + url)

def mosaic(z, url_fmt, kind, mode):
    x0, x1 = int(lon2x(W, z)), int(lon2x(E, z))
    y0, y1 = int(lat2y(N, z)), int(lat2y(S, z))
    tile = 256
    img = Image.new(mode, ((x1 - x0 + 1) * tile, (y1 - y0 + 1) * tile))
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            data = fetch(url_fmt.format(z=z, x=tx, y=ty), os.path.join(CACHE, f'{kind}_{z}_{tx}_{ty}.{"png" if kind == "dem" else "jpg"}'))
            img.paste(Image.open(io.BytesIO(data)).convert(mode), ((tx - x0) * tile, (ty - y0) * tile))
    # crop to the exact bbox (in mercator pixel space — over 1.4° the distortion is negligible)
    l = (lon2x(W, z) - x0) * tile; r = (lon2x(E, z) - x0) * tile
    t = (lat2y(N, z) - y0) * tile; b = (lat2y(S, z) - y0) * tile
    return img.crop((round(l), round(t), round(r), round(b)))

print('elevation tiles…')
dem_img = mosaic(11, 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png', 'dem', 'RGB')
a = np.asarray(dem_img).astype(np.float64)
dem = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
H, Wd = dem.shape
print('  dem', Wd, 'x', H, 'range', dem.min().round(), dem.max().round())

# keep only Trinidad & Tobago: Venezuela's Paria peninsula pokes into the north-west corner
lons = W + (np.arange(Wd) + .5) / Wd * (E - W)
lats = N - (np.arange(H) + .5) / H * (N - S)
LON, LAT = np.meshgrid(lons, lats)
venezuela = (LON < -61.84) & (LAT > 10.55)
dem[venezuela & (dem > -5)] = np.minimum(dem[venezuela & (dem > -5)], -15)
dem[(LAT < 10.06) & (LON < -61.6) & (dem > 0)] = -8   # stray slivers of the Orinoco delta along the south edge

def resize(arr, size, resample=Image.BILINEAR):
    return np.asarray(Image.fromarray(arr.astype(np.float32), mode='F').resize(size, resample))

# Bathymetry: at zoom 11 most sea tiles carry no depth (0 m), so take the sea floor from zoom 8 (ETOPO-based) and smooth it
print('bathymetry tiles…')
bimg = mosaic(8, 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png', 'dem', 'RGB')
ba = np.asarray(bimg).astype(np.float64)
bathy = ba[..., 0] * 256 + ba[..., 1] + ba[..., 2] / 256 - 32768
bathy = np.asarray(Image.fromarray(np.clip(bathy, -4000, 50).astype(np.float32), mode='F').resize((Wd, H), Image.BICUBIC))
bathy = gaussian_filter(bathy, 6)
print('  bathy range', bathy.min().round(), bathy.max().round())

# Land mask: elevation above ~1 m, OR satellite pixels that aren't water (catches the Caroni / Nariva wetlands at ~0 m)
satL = mosaic(12, 'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg', 'sat', 'RGB').resize((Wd, H), Image.BILINEAR)
sv = np.asarray(satL).astype(np.float32) / 255
bright = sv.mean(axis=2)
# vegetation / built land: clearly greener than blue (turbid Gulf water is about equal), and not below sea level
sat_land = (bright > .1) & (sv[..., 1] > sv[..., 2] * 1.1) & (sv[..., 0] < sv[..., 1] * 1.15)
land = (dem > 1.0) | (sat_land & (dem > -.5))
land &= ~venezuela
# tidy: drop specks, fill pinholes
lm = Image.fromarray((land * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
land = np.asarray(lm) > 127
# keep real islands only: drop specks and anything touching the map edge (Venezuelan slivers)
from scipy.ndimage import label
lab, n = label(land)
for k in range(1, n + 1):
    comp = lab == k
    edge = comp[0].any() or comp[-1].any() or comp[:, 0].any() or comp[:, -1].any()
    if comp.sum() < 40 or (edge and comp.sum() < 20000): land[comp] = False
dem = np.where(land, np.maximum(dem, 1.0), np.minimum(bathy, -2.0))
dem[venezuela] = np.minimum(dem[venezuela], -15)
print('  merged range', dem.min().round(), dem.max().round(), 'land %', round(land.mean() * 100, 1))

# geometry heights (512²)
h512 = resize(dem, (512, 512))
h512.round().clip(-32768, 32767).astype('<i2').tofile(os.path.join(OUT, 'height.bin'))

# baked normals (2048²) from the full-res DEM with the scene's exaggeration
km_per_px_x = (E - W) * 111.32 * math.cos(math.radians((N + S) / 2)) / Wd
km_per_px_y = (N - S) * 110.57 / H
d2 = resize(np.maximum(dem, -40), (2048, 2048), Image.BICUBIC)
sx = km_per_px_x * Wd / 2048 * 1000; sy = km_per_px_y * H / 2048 * 1000
gx = np.gradient(d2, axis=1) / sx * EXAG; gy = np.gradient(d2, axis=0) / sy * EXAG
n = np.dstack([-gx, gy, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * .5 + .5) * 255).round().astype(np.uint8)).save(os.path.join(OUT, 'normal.png'), optimize=True)

# data texture: sea depth, soft land mask, elevation
d1 = resize(dem, (1024, 1024), Image.BICUBIC)
depth = np.clip(-d1 / 600, 0, 1) ** .55                     # spread the shallow shelf out
land = np.clip((d1 - .2) / 1.2, 0, 1)
elev = np.clip(d1 / 940, 0, 1)
data = np.dstack([depth, land, elev])
Image.fromarray((data * 255).round().astype(np.uint8)).save(os.path.join(OUT, 'data.png'), optimize=True)

print('satellite tiles…')
sat = mosaic(12, 'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg', 'sat', 'RGB')
print('  sat', sat.size)
sat4 = sat.resize((4096, 4096), Image.LANCZOS)
# a gentle grade: lift the greens out of Sentinel's haze, warm the light
s = np.asarray(sat4).astype(np.float32) / 255
s = np.clip((s - .025) * 1.12, 0, 1) ** .94
s[..., 0] *= 1.03; s[..., 2] *= .97
sat4 = Image.fromarray((np.clip(s, 0, 1) * 255).round().astype(np.uint8))
sat4.save(os.path.join(OUT, 'sat.jpg'), quality=84, optimize=True, progressive=True)
sat4.resize((2048, 2048), Image.LANCZOS).save(os.path.join(OUT, 'sat-m.jpg'), quality=82, optimize=True, progressive=True)

json.dump({'bbox': [W, S, E, N], 'km': [round(km_per_px_x * Wd, 2), round(km_per_px_y * H, 2)], 'exag': EXAG,
           'maxH': float(dem.max().round()), 'minH': float(dem.min().round()), 'grid': 512},
          open(os.path.join(OUT, 'meta.json'), 'w'), indent=1)
print('done', json.load(open(os.path.join(OUT, 'meta.json'))))
