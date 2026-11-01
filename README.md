# page-reminder

Scheduled "go check this page" reminders. At the times you choose, it:

1. sends a push notification to your phone through [ntfy.sh](https://ntfy.sh). Tap it to open the page on your phone.
2. opens the page in a new tab of your browser on your computer.

It's for pages you keep checking by hand, like appointment slots, course waitlists, ticket drops or order status. It doesn't sign in or click anything for you. It just makes sure you remember to look.

Pure Python standard library, no dependencies. Works on Windows, macOS, Linux and WSL.

## Setup

1. Install the **ntfy** app ([Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / [iOS](https://apps.apple.com/app/ntfy/id1625396347)) and subscribe to a topic. Anyone who knows the topic name can read and send to it, so pick something long and hard to guess.
2. Copy the example config and edit it:
   ```bash
   cp config.example.json config.json
   ```
3. Send a test reminder, then start it:
   ```bash
   python page_reminder.py --test
   python page_reminder.py
   ```
   Leave it running. Press Ctrl+C to stop it.

`config.json` is in `.gitignore`, so your topic name stays off GitHub.

## Configuration

```json
{
  "ntfy_topic": "pick-a-long-random-topic-name",
  "ntfy_server": "https://ntfy.sh",
  "browser": "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
  "max_late_minutes": 60,
  "reminders": [
    {
      "name": "Check visa appointment dates",
      "message": "Sign in and look for an earlier appointment under Reschedule.",
      "url": "https://ais.usvisa-info.com/en-ca/niv/users/sign_in",
      "times": ["09:00", "13:00", "17:00", "21:00"]
    }
  ]
}
```

| Key | Meaning |
| --- | --- |
| `ntfy_topic` | Your ntfy topic. Required. |
| `ntfy_server` | Defaults to `https://ntfy.sh`. Change it if you self-host ntfy. |
| `browser` | Path to a browser executable. Leave it out to use your default browser. From WSL, use the `/mnt/c/...` path to a Windows browser. |
| `max_late_minutes` | If the computer was asleep at a reminder time and wakes up within this many minutes, the reminder still fires. Later than that, it's skipped. Default 60. |
| `reminders[].name` | Notification title. |
| `reminders[].message` | Notification body. |
| `reminders[].url` | Page to open. Also used as the tap action on your phone. |
| `reminders[].times` | Daily times, 24-hour `"HH:MM"`, local time. |
| `reminders[].priority` | ntfy priority: `min`, `low`, `default`, `high` (default) or `urgent`. |
| `reminders[].open_browser` | Set `false` to send only the phone alert. |

## Example: earlier US visa appointment

US visa appointment slots open up when people cancel, and catching one means checking the scheduling site often. The first reminder in `config.example.json` does that: four times a day it pings your phone and opens the sign-in page in Brave, so checking takes a few seconds.

Checking at different times of day helps, because cancelled slots are released at unpredictable times.

## Running it at startup

- **Windows:** press Win+R, run `shell:startup`, and add a shortcut to `pythonw.exe C:\path\to\page_reminder.py`.
- **macOS / Linux:** use a `launchd` agent, a `systemd --user` service, or `@reboot` in `crontab`.
- **WSL:** it runs as long as a WSL terminal is open. Windows shuts WSL down after the last terminal closes.
