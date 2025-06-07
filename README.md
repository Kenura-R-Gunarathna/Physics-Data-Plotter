# Physics Data Plotter (PDP)

## How to use

[<img src="./.github/videos/physics-data-preview-demo.gif" alt="Physics Data Preview (PDP) app demo." />](https://www.youtube.com/watch?v=XUqTVnGHaLI)

Youtube: https://www.youtube.com/watch?v=XUqTVnGHaLI

## Features

1. Sync data with working excel worksheet
2. Plot 2 variable function data
3. Chart Simulation using [Implot](https://github.com/epezent/implot)
4. Output as matplotlib.pyplot charts

## Install libraries

### Install from `pyproject.toml`

```bash
uv pip install .
```

### Install from `uv.lock` file

```bash
uv pip install --require-hashes -r uv.lock
```

### Run

```bash
python main.py
```

### Make Executable

```bash
pyinstaller PDP.spec
```
