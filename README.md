# SHRDLU

A port of Terry Winograd's 1970 SHRDLU natural-language / blocks-world program,
targeting CLISP (Common Lisp). Originally written in Maclisp for a PDP-10; this
version was ported at the University of Missouri–Rolla (UMR) around 2000 and
carries the internal version tag `UMR-1.0`.

You tell SHRDLU to manipulate a tabletop world of blocks, pyramids, and a box
in plain English ("pick up a big red block", "find a block which is taller than
the one you are holding and put it into the box"); it parses the sentence,
plans the action with a Planner-style theorem prover, and narrates the robot
arm carrying it out.

## This branch: `main`

`main` is the **text-only base** — the language engine and blocks-world
simulator, no graphics. `LOADER` loads no renderer; the arm's actions are
narrated as text (`~MOVING HAND TO (100 340 500)~` etc.).

```sh
clisp -q LOADER
```

Type English sentences one per line. See [Running](#running) below.

## Rendering implementations
The visualizers live on their own branches rather than `main`, each adding one
renderer file plus a branch-local `README.md`. All share the same isometric
projection math and the same Planner world-update hooks (`MOVETO`/`GRASP`/
`UNGRASP` interception, `ANSWER`-wrapped `ATABLE` snapshot for animation) —
they differ only in the drawing backend and its dependencies.

| Branch | Renderer | Output target | Notes |
| --- | --- | --- | --- |
| [`ui/clx-renderer`](../../tree/ui/clx-renderer) | Isometric, own X11 window | X server (XQuartz / Xorg); [CLX](https://github.com/sharplispers/clx) via [Quicklisp](https://www.quicklisp.org/) | Only renderer independent of the terminal, it renders the block world in a new window. Fillable polygons or thick/thin wireframe. Full write-up: `CLX.md`. |
| [`ui/regis-renderer`](../../tree/ui/regis-renderer) | Isometric, in-terminal | ReGIS-capable terminal | DEC ReGIS vector protocol. Filled (scanline) or wireframe, 16-color HLS palette. Full write-up: `REGIS.md`. |
| [`ui/sixel-renderer`](../../tree/ui/sixel-renderer) | Isometric, in-terminal | Sixel-capable terminal | DEC Sixel bitmap protocol; works in iTerm2 / WezTerm / foot / mlterm / sixel-xterm. Wireframe-only, animated crane arm. Easiest of the terminal renderers to run. Full write-up: `SIXEL.md`. |
| [`ui/terminal-renderer`](../../tree/ui/terminal-renderer) | ASCII side-view (X-Z) | any terminal | Earliest/simplest renderer — the `RENDER` file, plain ASCII, no graphics protocol. |
| [`ui/inplace-redraw`](../../tree/ui/inplace-redraw) | ASCII side-view (X-Z) | any terminal | Extends `ui/terminal-renderer`: redraws in place via clear-screen instead of scrolling, adds a status line. |

Two lineages: the **ASCII text** renderers (`terminal-renderer` →
`inplace-redraw`, needing nothing but a terminal) and the **graphics**
renderers (`sixel` / `regis` / `clx`, all branched from this `main` tip). The
three graphics branches share the same isometric look; pick by what your
environment supports — CLX if you have X11, Sixel for most modern terminals,
ReGIS only if you've got a ReGIS-capable terminal.

To try one:

```sh
git switch ui/sixel-renderer   # or ui/clx-renderer, ui/regis-renderer, ...
# read that branch's README.md for its specific setup, then:
clisp -q LOADER
```

## Lisp implementation

Developed and tested against **GNU CLISP 2.49.92**, the original porting
target. **SBCL does not load this codebase** — it fails on `PROGMR`, which
declares `REST` (a symbol in the locked `COMMON-LISP` package) special;
CLISP tolerates this, SBCL's ANSI package locks reject it. Treat this as
CLISP-only until `REST` is renamed throughout `PROGMR` and the codebase is
audited for similar collisions. CCL and ECL are untested.

## Running

```sh
clisp -q LOADER
```

CLISP loads all source files, initializes the blocks world, and prints
`READY`. Type English sentences one per line:

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
```

### Notes

- Use **"A RED BLOCK"** (indefinite), not **"THE RED BLOCK"** (definite), when
  more than one candidate exists — a definite reference to an ambiguous object
  gets "I DON'T KNOW WHICH ONE YOU MEAN."
- Don't type `OK` as input — SHRDLU expects natural-language sentences, not
  acknowledgements.
- Redefinition warnings during startup (`redefining function LIS2FY ...`) are
  harmless — a few functions are defined in two files and the later one wins.

### Debug mode

To step between sentences, edit `LOADER`: change `(USERMODE)` to `(DEBUGMODE)`
(and, on a renderer branch, comment out the `(load "...")` renderer line).
In debug mode SHRDLU pauses at an ERT prompt (`>>>`) between sentences, where
you can evaluate any Lisp expression (`atable`, `*last-action*`), type `T`/`P`
to continue, or `GO` to throw back to the top-level loop.

## Further reading

- [Winograd's original 1972 paper](https://doi.org/10.1016/0010-0285(72)90002-3)
- [Kent Pitman's MacLisp manual](https://www.maclisp.info/pitmanual/) — reference for Maclisp→Common Lisp compatibility
- [Miles Davis's UMR project notes](http://atarax.is/posts/shrdlu/)
- [SHRDLU resurrection](https://web.archive.org/web/20110608204231/http://www.semaphorecorp.com/misc/shrdlu.html) ([copy](http://atarax.is/SHRDLU_resurrection.html))
