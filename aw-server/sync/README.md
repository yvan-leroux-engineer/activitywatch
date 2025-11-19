# aw-sync

Synchronization tool for ActivityWatch.

## Overview

`aw-sync` enables syncing ActivityWatch data between devices by syncing local buckets with a special folder, which can then be synchronized using rsync/Syncthing/Dropbox/GDrive/etc.

## Features

- Syncs buckets between devices via a shared folder
- Works with any file sync tool (Syncthing, Dropbox, etc.)
- Pulls and pushes events every 5 minutes

## Usage

```bash
aw-sync
```

For more options:

```bash
aw-sync --help
```

## Setup

1. Start `aw-sync` on each device
2. Set up file syncing for the sync directory (`~/ActivityWatchSync` by default)
3. Events will automatically sync between devices

## Limitations

- Only syncs afk and window buckets by default
- Doesn't sync settings
- Doesn't support Android yet
- Mirrors events to all devices (can create duplicates)

## Development

To run from source:

```bash
cd aw-server/sync
cargo run --bin aw-sync
```

