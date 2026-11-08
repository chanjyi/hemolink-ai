import os

# Tests log in many times from one "IP"; rate limits are switched on only inside tests/test_security.py.
os.environ.setdefault("HEMOLINK_RATE_LIMIT", "off")
os.environ.setdefault("HEMOLINK_SCHEDULER", "off")
