```python
import gspread
import json
import os

from datetime import datetime
from zoneinfo import ZoneInfo

from oauth2client.service_account import (
    ServiceAccountCredentials
)

# ============================================
# GOOGLE SHEETS CONNECTION
# ============================================

def get_spreadsheet():

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    if "GOOGLE_CREDS" in os.environ:

        google_creds_dict = json.loads(
            os.environ["GOOGLE_CREDS"]
        )

        creds = (
            ServiceAccountCredentials
            .from_json_keyfile_dict(
                google_creds_dict,
                scope
            )
        )

    else:

        creds = (
            ServiceAccountCredentials
            .from_json_keyfile_name(
                "google_credentials.json",
                scope
            )
        )

    client = gspread.authorize(creds)

    return client.open("Attendance Logs")


# ============================================
# SUBJECT MASTER
# ============================================

def ensure_subject_exists(code, name):

    spreadsheet = get_spreadsheet()

    subjects_sheet = spreadsheet.worksheet(
        "SubjectsMaster"
    )

    records = subjects_sheet.get_all_records()

    existing_codes = {
        row["Code"]
        for row in records
    }

    if code not in existing_codes:

        subjects_sheet.append_row([
            code,
            name
        ])


# ============================================
# SNAPSHOT CHECK
# ============================================

def snapshot_exists(
    roll,
    valid_until
):

    spreadsheet = get_spreadsheet()

    history_sheet = spreadsheet.worksheet(
        "AttendanceHistory"
    )

    rows = history_sheet.get_all_records()

    for row in rows:

        if (
            str(row.get("Roll", "")).strip()
            == str(roll).strip()
            and
            str(row.get("ValidUntil", "")).strip()
            == str(valid_until).strip()
        ):
            return True

    return False


# ============================================
# SAVE SNAPSHOT
# ============================================

def save_snapshot(data):

    spreadsheet = get_spreadsheet()

    history_sheet = spreadsheet.worksheet(
        "AttendanceHistory"
    )

    roll = data["roll"]
    name = data["name"]
    valid_until = data["valid_until"]
    subjects = data["results"]

    if snapshot_exists(
        roll,
        valid_until
    ):
        return

    # ----------------------------------------
    # Learn subjects automatically
    # ----------------------------------------

    for subject in subjects:

        ensure_subject_exists(
            subject["course_code"],
            subject["subject"]
        )

    # ----------------------------------------
    # Build row
    # ----------------------------------------

    headers = history_sheet.row_values(1)

    row_data = {
        "Roll": roll,
        "Name": name,
        "ValidUntil": valid_until,
        "SnapshotCreatedAt":
            datetime.now(
                ZoneInfo("Asia/Kolkata")
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
    }

    for subject in subjects:

        row_data[
            subject["course_code"]
        ] = subject["attendance"]

    row = []

    for header in headers:

        row.append(
            row_data.get(header, "")
        )

    history_sheet.append_row(row)
```
