Parses `illuminate_events_*.json` file to generate a list of event definitions in a readable format.

Text output is in markdown format. Pipe output to a `.md` file to view formatting.

Text can be copy/pated into a confluence page.

## How to run
Prerequisites:
* Python 3.9
* Place illumiate_events_ json files in same directory as python script.

Usage:

```
python3 parse_ged.py > out.md
```

