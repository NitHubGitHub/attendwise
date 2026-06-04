import gspread
import os
import json

from datetime import datetime

from oauth2client.service_account import (
    ServiceAccountCredentials
)

# ============================================
# SUBMIT FEEDBACK
# ============================================

def submit_feedback(
    roll_number,
    message
):

    # REMOVE EXTRA SPACES
    message = message.strip()

    # EMPTY MESSAGE CHECK
    if message == "":
        return False

    # LIMIT LENGTH
    if len(message) > 500:
        return False

    # ============================================
    # GOOGLE SHEETS CONNECTION
    # ============================================

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

    # ============================================
    # OPEN FEEDBACK SHEET
    # ============================================

    feedback_sheet = client.open(
        "Attendance Logs"
    ).worksheet("Anonymous Feedback")

    # ============================================
    # APPEND FEEDBACK
    # ============================================

    feedback_sheet.append_row([
    str(datetime.now()),
    roll_number,
    message
])

    return True