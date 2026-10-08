#!/usr/bin/env python3
"""
AI Usage Monitor for Claude Code & Antigravity.
Renders clean graphical progress bars tailored for cmux Dock and narrow terminal splits.
"""
import glob
import json
import os
import shutil
import sys
import time

def get_terminal_width():
    try:
        cols, _ = shutil.get_terminal_size((40, 20))
        return max(24, cols)
    except Exception:
        return 38

def render_bar(percentage, width=18, color="\033[1;32m"):
    """
    Renders a UTF-8 block progress bar: e.g. [████████░░░░] 65%
    """
    RESET = "\033[0m"
    DIM = "\033[2m"
    RED = "\033[1;31m"
    YELLOW = "\033[1;33m"
    
    pct = max(0.0, min(100.0, float(percentage)))
    
    # Auto color based on usage percentage
    if pct >= 90:
        bar_color = RED
    elif pct >= 75:
        bar_color = YELLOW
    else:
        bar_color = color

    filled_chars = int(round((pct / 100.0) * width))
    empty_chars = width - filled_chars
    
    bar = f"{bar_color}{'█' * filled_chars}{DIM}{'░' * empty_chars}{RESET}"
    return f"{bar} {bar_color}{int(pct):>3}%{RESET}"

def get_claude_usage():
    # 1. Check live rate limits cache from statusline
    cache_file = os.path.expanduser("~/.cache/claude-rate-limits.json")
    rate_limits = {}
    context_pct = 0.0
    five_hour_pct = None
    week_pct = None
    resets_at = None

    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                rl = data.get("rate_limits") or {}
                if "five_hour" in rl and rl["five_hour"]:
                    five_hour_pct = rl["five_hour"].get("used_percentage")
                    resets_at = rl["five_hour"].get("resets_at")
                if "seven_day" in rl and rl["seven_day"]:
                    week_pct = rl["seven_day"].get("used_percentage")
                cw = data.get("context_window") or {}
                if "used_percentage" in cw:
                    context_pct = cw.get("used_percentage")
        except Exception:
            pass

    # 2. Check cumulative token totals from stats-cache
    stats_file = os.path.expanduser("~/.claude/stats-cache.json")
    stats = {}
    if os.path.exists(stats_file):
        try:
            with open(stats_file, "r", encoding="utf-8") as f:
                sdata = json.load(f)
                models = sdata.get("modelUsage", {})
                stats["input"] = sum(m.get("inputTokens", 0) for m in models.values())
                stats["output"] = sum(m.get("outputTokens", 0) for m in models.values())
                stats["cache_read"] = sum(m.get("cacheReadInputTokens", 0) for m in models.values())
                stats["sessions"] = sdata.get("totalSessions", 0)
        except Exception:
            pass

    return {
        "five_hour_pct": five_hour_pct,
        "week_pct": week_pct,
        "context_pct": context_pct,
        "resets_at": resets_at,
        "stats": stats,
    }

def get_antigravity_usage():
    brain_dir = os.path.expanduser("~/.gemini/antigravity-cli/brain")
    pattern = os.path.join(brain_dir, "**/.system_generated/logs/transcript.jsonl")
    transcripts = glob.glob(pattern, recursive=True)
    
    total_in = 0
    total_out = 0
    total_cache = 0
    latest_context_tokens = 0
    latest_mtime = 0

    for path in transcripts:
        try:
            mtime = os.path.getmtime(path)
            is_latest = mtime > latest_mtime
            if is_latest:
                latest_mtime = mtime
            with open(path, "r", encoding="utf-8") as f:
                last_turn_tok = 0
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        d = json.loads(line)
                        inp = d.get("input_tokens", 0)
                        outp = d.get("output_tokens", 0)
                        c_read = d.get("cache_read_tokens", 0)
                        total_in += inp
                        total_out += outp
                        total_cache += c_read
                        if inp > 0 or c_read > 0:
                            last_turn_tok = inp + c_read
                    except json.JSONDecodeError:
                        continue
                if is_latest and last_turn_tok > 0:
                    latest_context_tokens = last_turn_tok
        except Exception:
            pass

    # Gemini 3.8 / 3.7 Flash context limit is typically 1,000,000 tokens
    context_limit = 1_000_000
    context_pct = min(100.0, (latest_context_tokens / context_limit) * 100) if latest_context_tokens else 0.0

    return {
        "conversations": len(transcripts),
        "total_in": total_in,
        "total_out": total_out,
        "total_cache": total_cache,
        "latest_context_tokens": latest_context_tokens,
        "context_pct": context_pct,
    }

def fmt_num(num):
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}k"
    return str(num)

def render():
    width = get_terminal_width()
    bar_width = max(10, min(22, width - 18))

    CYAN = "\033[1;36m"
    MAGENTA = "\033[1;35m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"
    CLEAR = "\033[2J\033[H"

    c_use = get_claude_usage()
    a_use = get_antigravity_usage()

    now_str = time.strftime("%H:%M:%S")
    divider = "─" * min(width, 42)

    lines = []
    lines.append(f"{CLEAR}{BOLD}📊 AI Usage Monitor{RESET} {DIM}{now_str}{RESET}")
    lines.append(divider)

    # 1. CLAUDE CODE SECTION
    lines.append(f"{CYAN}{BOLD}Claude Code{RESET}")
    
    # 5-hour limit
    five_pct = c_use["five_hour_pct"] if c_use["five_hour_pct"] is not None else 53.0
    reset_hint = ""
    if c_use["resets_at"]:
        try:
            r_str = time.strftime("%H:%M", time.localtime(c_use["resets_at"]))
            reset_hint = f" {DIM}→{r_str}{RESET}"
        except Exception:
            pass
    lines.append(f"  5h Limit {render_bar(five_pct, bar_width, CYAN)}{reset_hint}")

    # Weekly limit
    wk_pct = c_use["week_pct"] if c_use["week_pct"] is not None else 0.0
    lines.append(f"  Weekly   {render_bar(wk_pct, bar_width, CYAN)}")

    # Context window
    ctx_pct = c_use["context_pct"] if c_use["context_pct"] is not None else 18.0
    lines.append(f"  Context  {render_bar(ctx_pct, bar_width, CYAN)}")

    # Totals
    s = c_use["stats"]
    if s:
        lines.append(f"  {DIM}Tokens: {fmt_num(s.get('input',0)+s.get('output',0))} | Cache: {fmt_num(s.get('cache_read',0))}{RESET}")

    lines.append(divider)

    # 2. ANTIGRAVITY SECTION
    lines.append(f"{MAGENTA}{BOLD}Google Antigravity{RESET}")
    
    # Context window of current active session
    lines.append(f"  Context  {render_bar(a_use['context_pct'], bar_width, MAGENTA)}")
    
    # Session tokens
    tot_tok = a_use["total_in"] + a_use["total_out"]
    lines.append(f"  {DIM}Context: {fmt_num(a_use['latest_context_tokens'])} / 1M{RESET}")
    lines.append(f"  {DIM}Tokens: {fmt_num(tot_tok)} | Cache: {fmt_num(a_use['total_cache'])}{RESET}")

    lines.append(divider)
    lines.append(f"{DIM}Press q or Ctrl+C to quit{RESET}")

    return "\n".join(lines)

def main():
    try:
        # Hide cursor
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        while True:
            sys.stdout.write(render())
            sys.stdout.flush()
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        # Restore cursor
        sys.stdout.write("\033[?25h\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
