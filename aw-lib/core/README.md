# aw-core

Python core library for ActivityWatch.

## Components

- **aw_core** - Core utilities, models, configuration
- **aw_datastore** - Data storage abstraction
- **aw_query** - Query language implementation
- **aw_transform** - Data transformation utilities

## Usage

This library is typically installed via PyPI:

```bash
pip install aw-core
```

For local development, install from this directory:

```bash
cd aw-lib/core
poetry install
```

## Dependencies

Watchers depend on `aw-core` via PyPI. This local copy is useful for:
- Developing `aw-core` itself
- Testing changes before publishing
- Custom modifications
