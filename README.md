# AI Usage Monitor

A compact terminal monitor displaying real-time graphical progress bars for **Claude Code** and **Google Antigravity** quotas, context windows, and token usage.

Built specifically for narrow terminal splits, sidecars, and the [cmux](https://cmux.com) right-sidebar Dock.

![Usage](https://img.shields.io/badge/status-active-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

## Features

- **Graphical UTF-8 Progress Bars**: Instant visual status without cluttered text.
- **Claude Code Integration**:
  - Live 5-hour rate limit percentage & reset countdown
  - Weekly quota percentage
  - Active session context window usage
  - Cumulative input/output tokens & prompt cache hits
- **Google Antigravity Integration**:
  - Active session context window usage (against 1M window)
  - Multi-session token totals & cache read tracking
- **Dynamic Layout**: Automatically recalculates bar widths to fit narrow sidebars and panes without ugly text wrapping.

## Usage

Run directly:
```bash
python3 monitor.py
```

### cmux Dock Integration

Add to your `~/.config/cmux/dock.json`:
```json
{
  "controls": [
    {
      "id": "usage",
      "title": "AI Usage",
      "command": "python3 /path/to/monitor.py"
    }
  ]
}
```

## License

MIT
