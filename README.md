# NYC Running Events Finder - Claude Agent Edition

Automatically search for upcoming running races, fun runs, and marathons in the NYC metro area using Claude AI, then send a curated email summary every Friday.

## What Information is Collected

For each event found, Claude collects:
- Event name
- Date
- Location (city/venue)
- Distance(s) (e.g., "5K", "13.1 miles")
- Registration cost
- Registration close date
- Registration link

## File Structure

```
-Running-Events-Finder/
├── .github/
│   └── workflows/
│       └── weekly_events.yml          # GitHub Actions workflow (Friday 5 PM UTC)
├── run_agent.py                       # Claude agent wrapper script
├── AGENT_PROMPT.yaml                  # Claude agent configuration
├── README.md                          # This file
|-  requirekents.txt                    # Python dependencies
└── .gitignore                         # Prevents credentials from leaking
```
