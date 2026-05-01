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
