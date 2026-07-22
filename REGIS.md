# SHRDLU — ReGIS Renderer

Isometric blocks-world visualization for SHRDLU, drawn using DEC's
**ReGIS** (Remote Graphics Instruction Set) — the vector graphics protocol
used by DEC's VT2xx/VT3xx terminal line, most notably the VT340. Drawing
commands are emitted as terminal escape sequences; the same terminal window
shows both the graphics and SHRDLU's scrolling text dialogue.

## Requirements

| Dependency | Notes |
| --- | --- |
| A ReGIS-capable terminal emulator | See [Terminal requirement](#terminal-requirement) below. |
| [CLISP](https://clisp.sourceforge.io/) 2.49 or later | See [Lisp implementation](#lisp-implementation) below. |

Unlike the `CLX` renderer, there is **no Lisp-level library dependency** —
`REGIS` is pure ANSI Common Lisp emitting raw escape sequences to
`*standard-output*`. Everything needed is the terminal itself.

### Terminal requirement

ReGIS support is rare among modern terminal emulators. This was developed
and tested against **xterm built with `--enable-regis-graphics`**, launched
with `-ti vt340` (sets the terminal-ID so xterm identifies itself as a
VT340-class device, which is what enables ReGIS handling on the DCS
sequences this renderer emits).

**A stock/distro-packaged xterm will not have this enabled.** Debian/Ubuntu
`apt install xterm`, Homebrew's `xterm` formula, and the XQuartz-bundled
`/opt/X11/bin/xterm` are all built without ReGIS support by default. You
need to build xterm from source yourself:

```sh
./configure --enable-regis-graphics --enable-sixel-graphics
make
```

(`--enable-sixel-graphics` is included above since the `SIXEL` renderer
branch's terminal — built the same way — can share one xterm binary; it's
not required for ReGIS alone.) Launch with:

```sh
xterm -ti vt340
```

Aside from xterm, real DEC terminals or emulators that specifically claim
VT340 ReGIS compatibility should work too, but hasn't been tested (alas, I 
only have a VT220).

### Lisp implementation

This is built on a port of Terry Winograd's 1970 SHRDLU natural language / blocks world
program, targeting CLISP (Common Lisp). Originally written in Maclisp for a
PDP-10; this version was ported at the University of Missouri-Rolla (UMR)
around 2000 and carries the internal version tag `UMR-1.0`.

Developed and tested against **GNU CLISP 2.49.92**.

## How to run

Assuming you are running this in a terminal with ReGIS support:

```sh
clisp -q LOADER
```

Both the ReGIS graphics and SHRDLU's text dialogue appear in the same xterm 
window.

---

## Rendering implementation

### Coordinate system

World space is `X 0-1100, Y 0-1100, Z 0-~1000`, with the viewer conceptually
at small `wx`/`wy`. Isometric projection to screen space:

```
screen_x =  (wx - wy) * *iso-sx* + *iso-ox*
screen_y = -(wx + wy) * *iso-sy* - wz * *iso-sz* + *iso-oy*
```

Defaults: `*iso-sx*`=0.32, `*iso-sy*`=0.12, `*iso-sz*`=0.27,
`*iso-ox*`=400, `*iso-oy*`=410. Canvas is `*rgw*`×`*rgh*` (800×420,
VT340-default width) restricted via ReGIS's `S(A...)` screen-addressing
command. `S(E)` erases only that image region each frame, so the scrolling
text area below it is untouched. Same projection math as `CLX`/`SIXEL` —
only the drawing backend differs.

### Drawing pipeline

All drawing commands for a frame are accumulated into a string stream and
emitted as a **single ReGIS DCS (Device Control String) block**, wrapped in
synchronized-update escapes (`ESC[?2026h` / `ESC[?2026l`) to prevent
tearing/flicker as the terminal parses and renders the block.

Solid faces use a hand-rolled **scanline fill** (`P` position + `V` vector
draw commands per row — ReGIS has no native filled-polygon primitive, unlike
CLX's `xlib:draw-lines :fill-p t`). Setting `*wireframe*` to `t` replaces
fills with plain polygon outlines instead.

**Color:** a 16-entry HLS (hue/lightness/saturation) palette, matching the
VT340's hard register limit — you cannot allocate arbitrary RGB colors the
way `CLX` does via `xlib:alloc-color`. Also note the VT340's hue convention
is rotated 120° from the standard: `H=0` is blue, `H=120` is red, `H=240` is
green.

### Depth sorting and the BOX

Blocks and pyramids go through a single painter's-algorithm sort, descending
by `wx1+wy1-wz1` (each object's own near corner). The `BOX` container is
injected into the *same* sort as two lump ops — "back" edges keyed to the
box's far corner (drawn early, before/under interior contents), "front"
edges keyed to its near corner (drawn late, on top) — so contents placed
inside the box stay visible against its wireframe walls.

Note: this two-lump approach is what the `CLX` branch started with too, and
turned out to have a real bug there — a lump-keyed front wall can end up
drawn on top of an unrelated object sitting well outside the box's
footprint but overlapping it on screen, since the whole wall shares one
fixed depth regardless of what it's actually crossing. That was fixed on
`ui/clx-renderer` (see that branch's `README.md`) by dropping fills
entirely in favor of thick-vs-thin wireframe lines and drawing the box
unconditionally last. **The same underlying bug likely exists here** — it
hasn't been fixed on this branch as of this writing.

### Animation

`MOVETO`/`GRASP`/`UNGRASP` are intercepted to drive per-frame interpolation:
`*anim-frames*` (default 12) steps per move, `*frame-delay*` (default
0.06s, ~16fps) between frames. When carrying a block, the arm follows an
arc peaking at `max(from-z, to-z, *carry-clearance*)` (default 700).
`ANSWER` is wrapped to snapshot `ATABLE` before the planning pass so blocks
render at their pre-move positions during plan execution.

### Terminal layout

Uses the alternate screen buffer (`ESC[?1049h`) so returning to the normal
buffer on exit leaves no trace. A scrolling text region is carved out below
the graphics via `DECSTBM` (`*text-row*`, default 30, is the first row of
that region — tune to your terminal's font size: `*rgh* / line_px + 2`). A
status line sits at `*text-row*-1`. `(regis-cleanup)` runs on CLISP's
`ext:*exit-hooks*` to restore the terminal cleanly, including on Ctrl-C.

## Tunable parameters

Set at runtime or edit defaults in `REGIS`:

| Variable | Default | Effect |
| --- | --- | --- |
| `*anim-frames*` | 12 | Interpolation steps per `MOVETO` |
| `*frame-delay*` | 0.06 | Seconds between animation frames |
| `*carry-clearance*` | 700 | Minimum arc peak z when carrying a block |
| `*rail-z*` | 1850 | Arm rail z-height; above canvas top gives "arm from the sky" |
| `*text-row*` | 30 | First row of the scrolling text area below the graphics |
| `*wireframe*` | `nil` | `t` for outline-only rendering instead of filled faces |
| `*rgw*` / `*rgh*` | 800 / 420 | Graphics canvas size in pixels |

## Running without graphics (debug mode)

To explore SHRDLU interactively without rendering the block world, edit `LOADER`:

1. Comment out `(load "regis")`
2. Change `(USERMODE)` to `(DEBUGMODE)`

Then run `clisp LOADER` as normal. In debug mode, SHRDLU pauses at an ERT
prompt (`>>>`) between sentences. At the prompt:

- Type any Lisp expression to evaluate it (e.g. `atable`, `*last-action*`)
- `T` or `P` — continue to next sentence
- `(setq some-var value)` — change state on the fly
- `GO` — throw back to the top-level catch loop