# PyOrganize

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zero dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](pyproject.toml)

A tiny, zero-dependency Python CLI that turns a chaotic folder into a tidy one.
Point it at your Downloads folder and watch everything sort itself into
`Images/`, `Documents/`, `Videos/` and friends — with a safety net.

## Features

- **One command** — organize any folder by file type
- **Dry run** — preview every move before anything happens
- **Undo** — one command restores the last organize operation
- **Custom rules** — define your own categories in a JSON file
- **Organize by date** — sort into `YYYY-MM` folders instead of by type
- **Collision-safe** — never overwrites; clashes become `photo (1).jpg`
- **Zero dependencies** — pure standard library

## Install

```bash
pip install .
# or, isolated (recommended):
pipx install .
```

## Usage

```bash
# Preview what would happen (always try this first)
pyorganize ~/Downloads --dry-run

# Actually organize
pyorganize ~/Downloads

# Oops — put everything back
pyorganize ~/Downloads --undo

# Organize by modified date instead of type
pyorganize ~/Screenshots --by date

# Include files inside subfolders
pyorganize ~/Downloads --recursive

# Use your own categories
pyorganize ~/Downloads --rules my-rules.json
```

Example dry-run output:

```
Would move 4 file(s):

  photo.jpg  ->  Images/
  song.mp3  ->  Audio/
  notes.txt  ->  Documents/
  setup.zip  ->  Archives/
```

## Custom rules

Create a JSON file mapping category names to extensions:

```json
{
  "Design": [".fig", ".psd", ".ai"],
  "Ebooks": [".epub", ".mobi"]
}
```

See [examples/rules.example.json](examples/rules.example.json). Custom rules are
merged over the built-ins — anything you don't override keeps working.

## How undo works

After organizing, a `.pyorganize-undo.json` log is left in the folder recording
every move. `--undo` plays it in reverse and removes category folders that are
left empty. The log deletes itself after a successful undo.

## Project structure

```
pyorganize/
├── src/pyorganize/
│   ├── organizer.py   # core engine: plan, apply, undo
│   └── cli.py         # argparse command-line interface
├── tests/             # pytest suite
└── examples/          # sample custom-rules file
```

## Development

```bash
pip install pytest
python -m pytest
```

## License

MIT — see [LICENSE](LICENSE).

---

Built by [Krrish](https://github.com/codewithkrrish)
