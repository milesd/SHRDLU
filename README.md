# SHRDLU

A port of Terry Winograd's 1970 SHRDLU natural language / blocks world program,
targeting CLISP (Common Lisp). Originally written in Maclisp for a PDP-10; this
version was ported at the University of Missouri-Rolla (UMR) around 2000 and
carries the internal version tag `UMR-1.0`.

## Requirements

- [CLISP](https://clisp.sourceforge.io/) 2.49 or later (ARM64 macOS: `brew install clisp`)

## Running

From the repo root:

```sh
clisp LOADER
```

CLISP loads all source files, initializes the blocks world, and prints `READY`.
Type English sentences one per line.

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

The `~MOVING HAND TO ...~` lines are the physical simulator narrating the robot
arm. There is no graphical display — text mode only.

## Sixel graphics

An isometric renderer is available on the `ui/smooth-animation` branch (merged
from `ui/sixel-renderer`). It requires a Sixel-capable terminal: iTerm2 with
Sixel enabled, WezTerm, xterm launched as `xterm -ti vt340`, foot, or mlterm.

```sh
clisp LOADER       # loads SIXEL automatically; run as normal
```

The renderer splits the screen: the isometric view occupies the top ~15 lines
and SHRDLU's text I/O scrolls below it. On exit (Ctrl-C or `(ext:exit)`) the
terminal is restored cleanly.

**Tuning the layout** — if the image and text overlap, adjust `*text-row*` to
match your font size and call `(sixel-init)` to re-apply:

```lisp
(setq *text-row* 19)   ; increase if image overlaps text
(sixel-init)
```

The canvas is 1600×360 px by default. To change scale, adjust the projection
constants and canvas height together (all must stay consistent):

| Variable | Role |
| -------- | ---- |
| `*ph*` | Canvas height in pixels (multiple of 6) |
| `*iso-oy*` | Should equal `*ph* - 5` |
| `*iso-sy*` | Depth scale (floor spread); 1.5× all three = 1.5× bigger |
| `*iso-sz*` | Height scale (block tallness) |
| `*iso-sx*` | Width scale (left-right spread, doesn't affect `*ph*`) |

Constraint: `2200 * *iso-sy* + 400 * *iso-sz* ≈ *ph* - 10` keeps the far
corner of the world visible.

## Running without graphics (debug mode)

To explore SHRDLU interactively without the Sixel renderer, edit `LOADER`:

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
