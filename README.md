# U.S. Soccer Course Checker

Automatically checks for available in-person U.S. Soccer grassroots 4v4/7v7 coaching courses.

## Features

- Queries the official U.S. Soccer Learning Center API
- Tracks previously seen courses
- Flags new courses when they become available
- Scheduled to run daily at 8am PT

## Setup

```bash
python3 ussoccer_course_check.py
```

### Environment Variables

- `USSOCCER_STATES`: Comma-separated state codes (default: `CA`)
  - Example: `USSOCCER_STATES=CA,TX,NY python3 ussoccer_course_check.py`
  - Use `ALL` to check all states: `USSOCCER_STATES=ALL python3 ussoccer_course_check.py`

## Output

The script prints available courses and marks new ones with `NEW`. Course data is cached locally.
