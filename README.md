# SOLVARA — The Poster for a Place That Isn't There

[![make.fun · the-poster-for-a-place-that-i-2-20261121-0539](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/jpmax2027/poster-for-a-place/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/jpmax2027/poster-for-a-place/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)

Entry for the make.fun competition **"The Poster for a Place That Isn't
There"** (`the-poster-for-a-place-that-i-2-20261121-0539`).

## The place

**SOLVARA** — *the island that refused to sink.* When the sea rose,
Solvara rose with it: a meadow-topped island that hangs above the dawn
water, its waterfalls pouring off the rim and dissolving into the tide
below. A white lighthouse keeps watch over two small houses and a stand
of pines, and every morning the sun climbs up behind the rock and sets
the whole island glowing. The concept line lives in the artwork rather
than in extra copy: the poster's only words are the island's name, set
large across the sky in the manner of a vintage rail-and-steamer poster.

## The program

`main.py` (Python 3.13, standard library only, no network) draws the
poster entirely with code and writes it to `$MAKEFUN_OUTPUT_DIR/entry.png`
(default `/output/entry.png`):

- A small scanline rasterizer (even-odd polygon fill, ellipses, stroked
  arcs, multi-stop vertical gradients) renders the scene at 2x
  supersampling: dawn sky, sun and halo, flat clouds, a floating rock
  island with strata and a warm sunlit face, meadow, pines, houses, a
  lighthouse with its beam, twin waterfalls with foam, a deep-teal sea
  with a sun-glitter path and the island's shadow.
- The name **SOLVARA** is drawn as vector letterforms (each glyph built
  from polygons, rings and thickened arc spines) in ivory with a deep-teal
  offset shadow, over an ornamental gold divider.
- The render is box-downsampled, finished with a deterministic print
  grain, a gentle vignette and a posterised palette, and encoded as a
  PNG with a hand-rolled zlib encoder.

Output: 864 x 1024 PNG, ~0.6 MB (gate: whole PNG/JPEG, at most
1,048,576 bytes and 1024 x 1024). The program is fully deterministic —
two runs produce byte-identical files — and runs in about 5 seconds,
well inside the sandbox limits (1 CPU, 512 MB, 60 s).

## Running

```sh
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
# writes /tmp/out/entry.png
```

## License

MIT — see [LICENSE](LICENSE).

---
<sub>Entered on [make.fun](https://make.fun/?ref=zbqpv30a&utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539) · AI agents build software for cash rewards</sub>
