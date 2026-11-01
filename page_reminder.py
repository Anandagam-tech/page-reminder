"""
Scheduled "go check this page" reminders. At each configured time it sends a
push notification to your phone via ntfy.sh and opens the page in a new
browser tab on your computer.

    python page_reminder.py                    # run forever using config.json
    python page_reminder.py --config my.json   # use a different config file
    python page_reminder.py --test             # fire every reminder once, now
"""

import argparse
import datetime as dt
import json
import os
import platform
import subprocess
import sys
import time
import urllib.request
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
IS_WSL = sys.platform.startswith("linux") and "microsoft" in platform.uname().release.lower()


def log(msg):
    print(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def load_config(path):
    with open(path) as f:
        cfg = json.load(f)
    if not cfg.get("ntfy_topic") or not cfg.get("reminders"):
        sys.exit(f"{path} needs an 'ntfy_topic' and at least one entry in 'reminders'.")
    for r in cfg["reminders"]:
        for t in r["times"]:
            dt.time.fromisoformat(t)  # fail early on a typo like "9:00pm"
    return cfg


def notify(cfg, reminder):
    server = cfg.get("ntfy_server", "https://ntfy.sh").rstrip("/")
    headers = {"Title": reminder["name"], "Priority": reminder.get("priority", "high"), "Tags": "bell"}
    if reminder.get("url"):
        headers["Click"] = reminder["url"]  # tapping the notification opens the page on your phone
    try:
        req = urllib.request.Request(f"{server}/{cfg['ntfy_topic']}",
                                     data=reminder.get("message", reminder["name"]).encode(),
                                     headers=headers)
        urllib.request.urlopen(req, timeout=15)
        log(f"[{reminder['name']}] Phone alert sent.")
    except Exception as e:
        log(f"[{reminder['name']}] ntfy failed: {e}")


def open_url(url, browser):
    """Opens url in a new tab of `browser` (path to an executable), or the default browser."""
    try:
        if browser:
            # Passing a URL to an already-running browser opens it in a new tab.
            # From WSL, run Windows programs from a Windows directory to avoid a UNC-path warning.
            cwd = "/mnt/c" if IS_WSL and os.path.isdir("/mnt/c") else None
            subprocess.Popen([browser, url], cwd=cwd,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif IS_WSL:
            subprocess.Popen(["explorer.exe", url], cwd="/mnt/c")
        else:
            webbrowser.open_new_tab(url)
        log(f"Opened {url}")
    except OSError as e:
        log(f"Could not open browser: {e}")


def fire(cfg, reminder):
    notify(cfg, reminder)
    if reminder.get("url") and reminder.get("open_browser", True):
        open_url(reminder["url"], cfg.get("browser"))


def next_run(times, after):
    """The first of `times` ("HH:MM") strictly after `after`."""
    for days in (0, 1):
        day = after.date() + dt.timedelta(days=days)
        for t in sorted(times):
            slot = dt.datetime.combine(day, dt.time.fromisoformat(t))
            if slot > after:
                return slot


def main():
    ap = argparse.ArgumentParser(description="Scheduled ntfy.sh + browser-tab reminders.")
    ap.add_argument("--config", default=os.path.join(HERE, "config.json"), help="config file (default config.json)")
    ap.add_argument("--test", action="store_true", help="fire every reminder once now, then exit")
    args = ap.parse_args()

    cfg = load_config(args.config)
    reminders = cfg["reminders"]
    max_late = dt.timedelta(minutes=cfg.get("max_late_minutes", 60))

    if args.test:
        for r in reminders:
            fire(cfg, r)
        return

    now = dt.datetime.now()
    targets = [next_run(r["times"], now) for r in reminders]
    for r, t in zip(reminders, targets):
        log(f"[{r['name']}] at {', '.join(r['times'])} daily. Next: {t:%a %H:%M}")
    log("Running. Ctrl+C to stop.")

    try:
        while True:
            now = dt.datetime.now()
            for i, r in enumerate(reminders):
                if now >= targets[i]:
                    if now - targets[i] <= max_late:
                        fire(cfg, r)
                    else:
                        log(f"[{r['name']}] Missed {targets[i]:%a %H:%M} (computer was asleep); skipping.")
                    targets[i] = next_run(r["times"], now)
                    log(f"[{r['name']}] Next: {targets[i]:%a %H:%M}")
            time.sleep(30)  # short sleeps so it notices when the computer wakes up
    except KeyboardInterrupt:
        log("Stopped.")


if __name__ == "__main__":
    main()
