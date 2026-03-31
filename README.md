# twinbird

Manage multiple [NetBird](https://netbird.io) instances on a single machine with isolated configs, daemon sockets, and WireGuard interfaces.

## Install

### uv (recommended)

```bash
uv tool install twinbird
```

This installs `twinbird` in an isolated environment and adds it to your PATH automatically.

### pip

```bash
pip install twinbird
```

The `twinbird` command is added to your Python environment's `Scripts/` (Windows) or `bin/` (Linux/macOS) directory. This is typically already on PATH if you installed Python with the "Add to PATH" option, or if you're installing into an active virtual environment.

## Usage

```bash
# Start a named instance
twinbird up office --management-url https://mgmt.example.com --setup-key YOUR_KEY

# Check status
twinbird status office

# List all instances
twinbird list

# Stop an instance
twinbird down office
```

### Environment Variables

Instead of passing flags every time:

```bash
export TWINBIRD_MANAGEMENT_URL=https://mgmt.example.com
export TWINBIRD_SETUP_KEY=YOUR_KEY
twinbird up office
```

| Variable | Purpose |
|---|---|
| `TWINBIRD_MANAGEMENT_URL` | Default management URL |
| `TWINBIRD_SETUP_KEY` | Default setup key |
| `TWINBIRD_NETBIRD_BIN` | Path to netbird binary (default: `netbird` on PATH) |
| `TWINBIRD_CONFIG_DIR` | Override root config directory |

## How It Works

Each named instance gets:
- Its own config directory (`~/.config/twinbird/<name>/` on Linux, `%APPDATA%/twinbird/<name>/` on Windows)
- A unique daemon socket address (Unix socket on Linux/macOS, TCP port on Windows)
- A unique WireGuard interface name (`wt<N>` on Linux, `utun<N>` on macOS)

Twinbird starts a separate `netbird service run` daemon per instance, then connects with `netbird up` — all fully isolated from the primary NetBird installation.

## Requirements

- [NetBird](https://netbird.io) installed and on PATH
- Python 3.10+

## License

MIT
