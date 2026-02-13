# Memos API Usage Examples

Common workflows and advanced usage patterns for the Memos API.

## Quick Capture Workflow

**Scenario:** Capture thoughts quickly during work

```bash
# Capture a quick idea
python {baseDir}/scripts/memos_client.py create "#idea 💡 Integrate Memos with Claude Code"

# Later, review all ideas
python {baseDir}/scripts/memos_client.py tag idea
```

## Daily Planning Workflow

**Scenario:** Start of day planning

```bash
# Create daily plan
python {baseDir}/scripts/memos_client.py create "#daily $(date +%Y-%m-%d)

## Today's Focus
1. Complete feature X
2. Review PRs
3. Documentation updates"

# Mark as completed at end of day
python {baseDir}/scripts/memos_client.py update memos/XYZ123 "#daily $(date +%Y-%m-%d)

## Today's Focus ✅ Completed
1. Complete feature X ✅
2. Review PRs ✅
3. Documentation updates ✅"
```

## Research Notes Workflow

**Scenario:** Organizing research materials

```bash
# Create research note with multiple tags
python {baseDir}/scripts/memos_client.py create "#research #AI #paper

## Paper: Attention Is All You Need

**Key findings:**
- Self-attention mechanism
- Parallelization advantages
- SOTA results on translation tasks

**Next steps:** Experiment with transformer architecture"

# Find all research notes
python {baseDir}/scripts/memos_client.py tag research
```

## Meeting Notes Template

```bash
# Create meeting notes
python {baseDir}/scripts/memos_client.py create "#meeting #team

## Weekly Sync - $(date +%Y-%m-%d)

### Attendees
- Alice (PM)
- Bob (Dev)
- Charlie (Design)

### Discussion
1. Sprint progress review
2. Blocker identification
3. Next sprint planning

### Action Items
- [ ] Alice: Update product specs
- [ ] Bob: Fix authentication bug
- [ ] Charlie: Prepare mockups

### Next Meeting
$(date -d '+7 days' +%Y-%m-%d)"
```

## Book Reading Tracker

```bash
# Add reading note
python {baseDir}/scripts/memos_client.py create "#reading #fiction

## Book: The Great Gatsby

**Author:** F. Scott Fitzgerald
**Started:** 2026-02-13
**Status:** In progress (page 45/180)

### Notes
- Beautiful prose style
- Interesting commentary on American Dream
- Nick as unreliable narrator?

**Rating:** ⭐⭐⭐⭐⭐ (so far)"
```

## Batch Operations

### Import from File

Create a Python script to import multiple memos:

```python
# import_notes.py
import subprocess
from pathlib import Path

notes_file = Path("notes_to_import.txt")
notes = notes_file.read_text().split("---")

for note in notes:
    if note.strip():
        subprocess.run([
            "python", ".claude/skills/memos-api/scripts/memos_client.py",
            "create", note.strip()
        ])
```

### Tag Statistics

```python
# tag_stats.py
import subprocess
import json
import re

result = subprocess.run(
    ["python", ".claude/skills/memos-api/scripts/memos_client.py",
     "list", "--limit", "1000", "--json"],
    capture_output=True, text=True
)

memos = json.loads(result.stdout)
tags = {}

for memo in memos:
    content = memo.get('content', '')
    found_tags = re.findall(r'#(\w+)', content)
    for tag in found_tags:
        tags[tag] = tags.get(tag, 0) + 1

print("Tag statistics:")
for tag, count in sorted(tags.items(), key=lambda x: x[1], reverse=True):
    print(f"  #{tag}: {count}")
```

## JSON Output Integration

```bash
# Get memos as JSON for further processing
python {baseDir}/scripts/memos_client.py search "Python" --json > results.json

# Process with jq
python {baseDir}/scripts/memos_client.py list --json | jq '.[] | .name'
```

## Archiving Old Memos

```python
# archive_old.py
from datetime import datetime, timedelta
import subprocess

# Find memos older than 30 days
cutoff_date = datetime.now() - timedelta(days=30)

# Get all memos
result = subprocess.run(
    ["python", ".claude/skills/memos-api/scripts/memos_client.py",
     "list", "--limit", "1000", "--json"],
    capture_output=True, text=True
)

memos = json.loads(result.stdout)

for memo in memos:
    create_time = datetime.fromisoformat(memo['createTime'].replace('Z', '+00:00'))
    if create_time < cutoff_date:
        # Add #archive tag
        new_content = memo['content'] + "\n\n#archive"
        subprocess.run([
            "python", ".claude/skills/memos-api/scripts/memos_client.py",
            "update", memo['name'], new_content
        ])
        print(f"Archived: {memo['name']}")
```

## Common Tag Categories

| Tag | Usage |
|-----|-------|
| `#inbox` | Quick capture, unprocessed |
| `#todo` | Action items, tasks |
| `#reading` | Books, articles to read |
| `#meeting` | Meeting notes |
| `#idea` | Ideas, brainstorming |
| `#reference` | Reference material |
| `#archive` | Completed, archived items |
| `#daily` | Daily planning notes |
| `#project` | Project-specific notes |

## Integration with Other Tools

### With Markdown Editor

```bash
# Create memo from markdown file
cat note.md | python {baseDir}/scripts/memos_client.py create "$(cat -)"
```

### With Cron (Scheduled Tasks)

```bash
# Daily reminder (add to crontab: 0 9 * * *)
0 9 * * * echo "#daily Morning checklist: $(date +%Y-%m-%d)" | python ~/.claude/skills/memos-api/scripts/memos_client.py create "$(cat -)"
```

### With fzf (Fuzzy Finder)

```bash
# Interactive memo selector
memo_name=$(python {baseDir}/scripts/memos_client.py list --json | jq -r '.[].name' | fzf)
python {baseDir}/scripts/memos_client.py get "$memo_name"
```
