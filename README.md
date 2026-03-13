# AC-T Chemotherapy Dashboard

Desktop app for tracking AC-T chemotherapy treatment progress.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python3 src/main.py
```

## Test Data

Generate 5 synthetic patients:
```bash
python3 generate_test_data.py
```

Clear all data and regenerate:
```bash
python3 generate_test_data.py --clear --patients 5
```

Or use the **Developer** menu in the app menu bar.

## Tests

```bash
pytest
```
