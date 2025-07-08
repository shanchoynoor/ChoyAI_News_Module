#!/usr/bin/env python3
# Very basic timezone test

import pytz
from datetime import datetime

print("Starting test...")

# Get timezone for Etc/GMT-6 (which is UTC+6)
tz = pytz.timezone('Etc/GMT-6')
now = datetime.utcnow()
now = pytz.timezone('UTC').localize(now)
local = now.astimezone(tz)

# Print timezone info
print(f"Timezone: Etc/GMT-6")
print(f"Abbreviation: {local.strftime('%Z')}")
print(f"Offset hours: {int(local.utcoffset().total_seconds() // 3600)}")

# Compare with Asia/Dhaka
dhaka = pytz.timezone('Asia/Dhaka')
dhaka_local = now.astimezone(dhaka)
print(f"\nTimezone: Asia/Dhaka")
print(f"Abbreviation: {dhaka_local.strftime('%Z')}")
print(f"Offset hours: {int(dhaka_local.utcoffset().total_seconds() // 3600)}")

print("Test complete.")
