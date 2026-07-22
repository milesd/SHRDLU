# SHRDLU — Sixel Renderer

Isometric blocks-world visualization for SHRDLU drawn using DEC's **Sixel** graphics protocol (bitmap). Drawing commands are emitted as terminal escape
sequences; the same terminal window shows both the graphics and SHRDLU's
scrolling text dialogue.

## Requirements

| Dependency | Notes |
| --- | --- |
| A Sixel-capable terminal emulator | See [Terminal requirement](#terminal-requirement) below. |
| [CLISP](https://clisp.sourceforge.io/) 2.49 or later | See [Lisp implementation](#lisp-implementation) below. |

Like `REGIS` and unlike `CLX`, there is **no Lisp-level library
dependency** — `SIXEL` is pure ANSI Common Lisp emitting raw escape
sequences to `*standard-output*`. Everything needed is the terminal itself.

### Terminal requirement

A terminal emulator with Sixel support. Tested/targeted terminals include:

- **iTerm2** (macOS) — with Sixel enabled in Preferences → Profiles →
  Terminal
- **WezTerm** — Sixel support built in, no configuration needed
- **xterm**, needs `--enable-sixel-graphics` at
  compile time; most distro-packaged xterm builds either lack this or have
  it behind a runtime resource (`decGraphicsID`) — check yours, and rebuild
  from source if missing:
  ```sh
  ./configure --enable-sixel-graphics
  make
  ```

Sixel support is meaningfully more common today than ReGIS — several
mainstream terminal emulators ship it without a custom build, which is not
true of ReGIS. If you're setting up from scratch and don't already have a
preferred terminal, this is the easier of the two protocol-based renderers
to get running.

### Lisp implementation

This is built on a port of Terry Winograd's 1970 SHRDLU natural language / blocks world
program, targeting CLISP (Common Lisp). Originally written in Maclisp for a
PDP-10; this version was ported at the University of Missouri-Rolla (UMR)
around 2000 and carries the internal version tag `UMR-1.0`.

Developed and tested against **GNU CLISP 2.49.92**.

## How to run

From your Sixel-capable terminal of choice:

```sh
clisp -q LOADER
```

CLISP loads all source files,
initializes the blocks world, and prints `READY`. Type English sentences
one per line.

```
READY
WHAT BLOCKS ARE ON THE TABLE?
THE BLUE ONE ,THE GREEN CUBE ,THE LARGE RED ONE ,THE LARGE GREEN ONE
WHICH SUPPORTS THE RED PYRAMID ,AND THE RED CUBE .

READY
PICK UP A BIG RED BLOCK.
~MOVING HAND TO (100 340 500)~
~GRASPING BLOCK B7~
~MOVING HAND TO (600 1100 200)~
~LETTING GO~
OK .

READY
FIND A BLOCK WHICH IS TALLER THAN THE ONE YOU ARE HOLDING AND PUT IT INTO THE BOX.
~CHOOSING BLOCK B10~
...
OK .
```

The `~MOVING HAND TO ...~` lines are the physical simulator narrating the
robot arm, in addition to the isometric graphics.

The renderer splits the screen: the isometric view occupies the top rows and
SHRDLU's text I/O scrolls below it. On exit (Ctrl-C or `(ext:exit)`) the
terminal is restored cleanly.

**Tuning the layout** — if the image and text overlap, adjust `*text-row*`
to match your font size and call `(sixel-init)` to re-apply:

```lisp
(setq *text-row* 19)   ; increase if image overlaps text
(sixel-init)
```

---

## Rendering implementation

### Coordinate system

World space is `X 0-1100, Y 0-1100, Z 0-~1000`, with the viewer conceptually
at front-right-above. Isometric projection to screen space:

```
screen_x =  (wx - wy) * *iso-sx* + *iso-ox*
screen_y = -(wx + wy) * *iso-sy* - wz * *iso-sz* + *iso-oy*
```

Defaults: `*iso-sx*`=0.24, `*iso-sy*`=0.12, `*iso-sz*`=0.206,
`*iso-ox*`=300, `*iso-oy*`=355. Canvas is `*pw*`×`*ph*` pixels (default
600×360 — world content spans ~528px wide, leaving 36px margins; `*ph*`
must be a multiple of 6, the Sixel band height). Same underlying projection
approach as `CLX`/`REGIS`, tuned to different constants for this canvas
size. To change scale without breaking the layout, adjust the projection
constants and canvas height together:

| Variable | Role |
| -------- | ---- |
| `*ph*` | Canvas height in pixels (multiple of 6) |
| `*iso-oy*` | Should equal `*ph* - 5` |
| `*iso-sy*` | Depth scale (floor spread); scaling all three by the same factor scales the whole scene |
| `*iso-sz*` | Height scale (block tallness) |
| `*iso-sx*` | Width scale (left-right spread, doesn't affect `*ph*`) |

Constraint: `2200 * *iso-sy* + 400 * *iso-sz* ≈ *ph* - 10` keeps the far
corner of the world visible.

### Drawing pipeline

Unlike `CLX` (fillable polygons) and `REGIS` (fillable via hand-rolled
scanline), **this renderer is wireframe-only — there is no fill code path
at all.** Every shape (blocks, pyramids, the box, the floor grid) is drawn
as Bresenham line edges directly into a flat pixel buffer, which is then
encoded into Sixel bands and emitted as one escape sequence per frame
(`emit-sixel`). There's no `*wireframe*` toggle to flip, unlike `CLX`/
`REGIS` — this is simply how the renderer works.

**Color:** a palette of `(r g b)` triples, each channel 0–100 percent
(`*sixel-palette*`) — Sixel's native color-register model, conceptually
similar to `REGIS`'s HLS registers but specified directly in RGB rather
than hue/lightness/saturation.

### Depth sorting and the BOX

Blocks and pyramids go through a single painter's-algorithm sort, descending
by `wx1+wy1-wz1` (each object's own near corner). The `BOX` container is
injected into the *same* sort as two lump ops — "back" edges keyed to the
box's far corner (`wx2+wy2-wz1`, drawn early/underneath), "front" edges
keyed to its near corner (`wx1+wy1-wz1`, drawn late/on top) — so contents
placed inside the box stay visible against its wireframe walls.

Note: this exact two-lump-key pattern is what the `CLX` branch started
with too, and turned out to have a real bug there — a lump-keyed front wall
can end up drawn on top of an unrelated object sitting well outside the
box's footprint but overlapping it on screen, since the whole wall shares
one fixed depth regardless of what it's actually crossing. That was fixed
on `ui/clx-renderer` (see that branch's `README.md`) by drawing the box
unconditionally last instead of depth-sorting it. **The same underlying bug
likely exists here** — it hasn't been fixed on this branch as of this
writing. It may be less noticeable here than it was on `CLX`/`REGIS` since
this renderer is already wireframe-only (thin lines crossing thin lines is
less visually jarring than thin lines crossing filled color faces), but the
sort logic itself has the same flaw.

### Animation

`ANSWER` is wrapped to snapshot `ATABLE` before the planning pass so blocks
render at their pre-move positions during plan execution, not their
already-updated planned positions. Each `MOVETO` call interpolates the arm
over `*anim-frames*` steps (default 6, ~1.4s at 4fps — fewer frames than
`CLX`/`REGIS`'s default 12, presumably tuned for Sixel's larger per-frame
encode/transmit cost). When carrying a block, the arm follows an arc
peaking at `max(from-z, to-z, *carry-clearance*)` (default 700) so the
block clears obstacles regardless of what the planner computed. The
crane arm itself is a vertical cable from overhead (`wz`=750) down to
`HANDAT` with a small claw; the carried block rides below the arm tip
(arm-z minus block height). `UNGRASP` renders one final frame showing the
block at its placed position.

### Terminal layout

```
rows 1 .. (*text-row* - 2)  : Sixel image (not scrolling)
row  (*text-row* - 1)       : status line (fixed, separates image from text)
rows *text-row* .. bottom   : scrolling text area for SHRDLU I/O
```

Uses the alternate screen buffer (`ESC[?1049h`) so returning to the normal
buffer on exit leaves no trace. A scrolling text region is carved out below
the graphics via `DECSTBM`, starting at `*text-row*` (default 17 — tune to
your terminal's font size: `*text-row* ≈ ceil(*ph* / line_px) + 2`). Frames
are wrapped in synchronized-output escapes (`ESC[?2026h` / `ESC[?2026l`)
for tear-free updates. `(sixel-cleanup)` runs on CLISP's `ext:*exit-hooks*`
to restore the terminal cleanly, including on Ctrl-C.

Set `(setq *render-timing* t)` to print per-phase render timings to stderr.

## Tunable parameters

Set at runtime or edit defaults in `SIXEL`:

| Variable | Default | Effect |
| --- | --- | --- |
| `*anim-frames*` | 6 | Interpolation steps per `MOVETO` |
| `*carry-clearance*` | 700 | Minimum arc peak z when carrying a block |
| `*text-row*` | 17 | First row of the scrolling text area below the graphics |
| `*render-timing*` | `nil` | `t` to print per-phase ms to stderr |
| `*pw*` / `*ph*` | 600 / 360 | Canvas size in pixels (`*ph*` must be a multiple of 6) |
| `*iso-sx*` / `*iso-sy*` / `*iso-sz*` | 0.24 / 0.12 / 0.206 | Projection scale (width / floor depth / height) |

## Running without graphics (debug mode)

To explore SHRDLU interactively without rendering the block world, edit `LOADER`:

1. Comment out `(load "sixel")`
2. Change `(USERMODE)` to `(DEBUGMODE)`

Then run `clisp LOADER` as normal. In debug mode, SHRDLU pauses at an ERT
prompt (`>>>`) between sentences. At the prompt:

- Type any Lisp expression to evaluate it (e.g. `atable`, `*last-action*`)
- `T` or `P` — continue to next sentence
- `(setq some-var value)` — change state on the fly
- `GO` — throw back to the top-level catch loop

## Notes

- Use **"A RED BLOCK"** (indefinite), not **"THE RED BLOCK"** (definite) when
  multiple candidates exist. Definite reference to an ambiguous object gets
  "I DON'T KNOW WHICH ONE YOU MEAN."
- Don't type `OK` as input — SHRDLU doesn't recognize it. It expects natural
  language sentences.
- Redefinition warnings during startup (`redefining function LIS2FY ...`) are
  harmless.

## Further reading

- [Winograd's original 1972 paper](https://doi.org/10.1016/0010-0285(72)90002-3)
- [Kent Pitman's MacLisp manual](https://www.maclisp.info/pitmanual/) — reference for Maclisp→Common Lisp compatibility issues
- [Miles Davis's UMR Project notes](http://atarax.is/posts/shrdlu/)
- [SHRDLU resurrection](https://web.archive.org/web/20110608204231/http://www.semaphorecorp.com/misc/shrdlu.html) ([copy](http://atarax.is/SHRDLU_resurrection.html))
