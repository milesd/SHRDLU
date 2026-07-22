# SHRDLU — CLX Renderer

Isometric blocks-world visualization for SHRDLU using the [CLX](https://github.com/sharplispers/clx) Common Lisp
library. SHRDLU's text dialog stays in whatever terminal launches `clisp`, the
blocks world is rendered in a separate window.

## Requirements

| Dependency | Notes |
| --- | --- | 
| An X server |  In theory, any Xorg or Xwayland. Tested under macOS and [XQuartz](https://www.xquartz.org/). |
| [CLX](https://github.com/sharplispers/clx) | sharplispers's fork of crhodes' fork of danb's fork of the CLX library
| [Quicklisp](https://www.quicklisp.org/) | One way to install CLX. `CLX` calls `(ql:quickload :clx)` on first load, which fetches the library over the network once and caches it under `~/quicklisp/` — no network needed on later runs. |
| CLISP | Developed and tested against **GNU CLISP 2.49.92** | See [Lisp implementation](#lisp-implementation) below. |

Unlike the `SIXEL` and `REGIS` renderers, no custom-built terminal emulator is required, but of course X11 is.
SHRDLU's dialog will be in the terminal you launch `clisp` from, and it opens its own
window to draw the blocks world. `DISPLAY` needs to be set (XQuartz sets it automatically once
running; on Linux it's normally already set by your session).

### Lisp implementation

This is built on a port of Terry Winograd's 1970 SHRDLU natural language / blocks world
program, targeting CLISP (Common Lisp). Originally written in Maclisp for a
PDP-10; this version was ported at the University of Missouri-Rolla (UMR)
around 2000 and carries the internal version tag `UMR-1.0`.

Developed and tested against **GNU CLISP 2.49.92**.

## How to run

Assuming an X server is running and `DISPLAY` is set:

```sh
clisp -q -i LOADER
```

A window titled "SHRDLU" opens once `LOADER` reaches `(load "clx")`; text
dialogue continues in the terminal you launched `clisp` from. Quitting
either the Lisp process or the X window (via its close button) tears down
the X connection cleanly (see [Window lifecycle](#window-lifecycle)).

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
`*iso-ox*`=400, `*iso-oy*`=410, on an 800×420 (`*clx-w*`/`*clx-h*`) canvas.
Same projection math as `REGIS` and `SIXEL` — only the drawing backend
differs.

### Drawing pipeline

Each frame draws into an off-screen `xlib:pixmap`, then `xlib:copy-area`
blits it to the window in one call (`clx-flip`) — double buffering with no
tearing, no synchronized-update escapes needed (unlike `REGIS`'s terminal
DCS approach).

**Outline-only by default** (`*wireframe*` defaults to `t`). Block and
pyramid edges draw at `*clx-block-line-width*` (2px); the box wireframe and
floor grid draw at `*clx-thin-line-width*` (0 — the X server's thinnest
"cosmetic" line). This line-weight contrast is what keeps objects readable
against the container/table lines they visually cross, without needing
correct 3D occlusion between them. Set `*wireframe*` to `nil` to switch back
to solid filled faces (`xlib:draw-lines ... :fill-p t :shape :convex` — no
manual scanline rasterization needed, unlike `REGIS`).

**Color:** direct RGB via `xlib:alloc-color` against the default colormap
(`*clx-base-rgb*`; three brightness shades per block color for
top/left/right faces when filled) — no 16-color register limit or
HLS hue-rotation quirk like `REGIS`'s VT340 palette.

### Depth sorting and the BOX

Blocks and pyramids go through a single painter's-algorithm sort, descending
by `wx1+wy1-wz1` (each object's own near corner) — same convention as
`REGIS`/`SIXEL`.

The `BOX` container is handled separately: it's drawn as a full 12-edge
wireframe, unconditionally *after* everything else, always on top. This
wasn't the original design — two earlier approaches were tried and replaced:

1. Two lump draw ops (all "back" edges keyed to the box's far corner, all
   "front" edges keyed to its near corner) — put every front edge at one
   fixed depth, so the wireframe could draw on top of an unrelated object
   regardless of that object's true position.
2. One op per edge, each keyed off its own midpoint (the same
   per-primitive-position convention every other object uses) — more
   accurate, but a container's own walls sit both nearer and farther than
   its own contents depending on which wall and which content, so no single
   per-edge key got every case right either.

Since the box is never solid-filled, drawing it last and unconditionally is
simpler and just as correct in practice: thin wireframe lines crossing in
front of a nearer object is a minor visual nit, not real occlusion
breakage — and this sidesteps the whole depth-sort problem.

### Animation

`MOVETO`/`GRASP`/`UNGRASP` are intercepted (wrapping the original `MOVER`
functions) to drive per-frame interpolation: `*anim-frames*` (default 12)
steps per move, `*frame-delay*` (default 0.06s, ~16fps) between frames. When
carrying a block, the arm follows an arc peaking at
`max(from-z, to-z, *carry-clearance*)` (default 700) — a flat
`max`, not scaled down for short horizontal carries, so a block picked up
and set down nearby (e.g. into an adjacent box) still clears obstacles in
its path. `ANSWER` is wrapped to snapshot `ATABLE` before the planning pass
so blocks render at their pre-move positions during plan execution, not
their already-updated planned positions.

### Window lifecycle

`render-world` drains pending X events (`clx-pump-events`) before drawing
each frame — handles `Expose` (redraw on window damage/uncover) and the
window manager's close button (`WM_DELETE_WINDOW`, tears down the display
connection via `clx-cleanup`). `clx-cleanup` also runs on CLISP's
`ext:*exit-hooks*` (guarded by `find-symbol`/`find-package`, so it's a
harmless no-op under implementations without that hook — though the X
connection won't be closed as cleanly there), so Ctrl-C and `(quit)` both
close the X connection properly under CLISP.

## Tunable parameters

Set at runtime or edit defaults in `CLX`:

| Variable | Default | Effect |
| --- | --- | --- |
| `*anim-frames*` | 12 | Interpolation steps per `MOVETO` |
| `*frame-delay*` | 0.06 | Seconds between animation frames |
| `*carry-clearance*` | 700 | Minimum arc peak z when carrying a block |
| `*rail-z*` | 1850 | Arm rail z-height; above canvas top gives "arm from the sky" |
| `*wireframe*` | `t` | `nil` for solid filled faces instead of outlines |
| `*clx-block-line-width*` | 2 | Wireframe line thickness for blocks/pyramids |
| `*clx-thin-line-width*` | 0 | Wireframe line thickness for box/floor grid |
| `*clx-w*` / `*clx-h*` | 800 / 420 | Window size in pixels |

## Running without graphics (debug mode)

To explore SHRDLU interactively without rendering the block world, edit `LOADER`:

1. Comment out `(load "clx")`
2. Change `(USERMODE)` to `(DEBUGMODE)`

Then run `clisp LOADER` as normal. In debug mode, SHRDLU pauses at an ERT
prompt (`>>>`) between sentences. At the prompt:

- Type any Lisp expression to evaluate it (e.g. `atable`, `*last-action*`)
- `T` or `P` — continue to next sentence
- `(setq some-var value)` — change state on the fly
- `GO` — throw back to the top-level catch loop