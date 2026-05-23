import requests
import gspread

from bs4 import BeautifulSoup
from datetime import datetime

from oauth2client.service_account import (
    ServiceAccountCredentials
)

# ============================================
# SUBJECT DATABASE (REPLACES MYSQL)
# ============================================

subjects = {

    # SEM 1
    "23IZ101": {"credits": 4, "hours": 64},
    "23IZ102": {"credits": 3, "hours": 48},
    "23IZ103": {"credits": 3, "hours": 48},
    "23IZ104": {"credits": 4, "hours": 64},
    "23IZ105": {"credits": 4, "hours": 64},
    "23IZ110": {"credits": 2, "hours": 64},
    "23IZ111": {"credits": 2, "hours": 64},
    "23IG065": {"credits": 4, "hours": 192},

    # SEM 2
    "23IZ201": {"credits": 4, "hours": 64},
    "23IZ202": {"credits": 4, "hours": 64},
    "23IZ203": {"credits": 4, "hours": 64},
    "23IZ204": {"credits": 3, "hours": 48},
    "23IZ211": {"credits": 2, "hours": 64},
    "23IZ212": {"credits": 2, "hours": 64},
    "23IZ213": {"credits": 0, "hours": 32},
    "23IG066": {"credits": 4, "hours": 192},
    "23IH072": {"credits": 3, "hours": 48},

    # SEM 3
    "23IZ301": {"credits": 4, "hours": 64},
    "23IZ302": {"credits": 4, "hours": 64},
    "23IZ303": {"credits": 3, "hours": 48},
    "23IZ304": {"credits": 4, "hours": 64},
    "23IZ305": {"credits": 4, "hours": 64},
    "23IZ310": {"credits": 2, "hours": 64},
    "23IZ311": {"credits": 2, "hours": 64},
    "23IH073": {"credits": 3, "hours": 48},
    "23IG067": {"credits": 4, "hours": 192},

    # SEM 4
    "23IZ401": {"credits": 4, "hours": 64},
    "23IZ402": {"credits": 3, "hours": 48},
    "23IZ403": {"credits": 4, "hours": 64},
    "23IZ404": {"credits": 4, "hours": 64},
    "23IZ405": {"credits": 4, "hours": 64},
    "23IZ410": {"credits": 2, "hours": 64},
    "23IZ411": {"credits": 2, "hours": 64},
    "23IZ413": {"credits": 1, "hours": 32},
    "23IG068": {"credits": 4, "hours": 192},
    "23IH074": {"credits": 2, "hours": 96},

    # SEM 5
    "23IZ501": {"credits": 3, "hours": 48},
    "23IZ502": {"credits": 4, "hours": 64},
    "23IZ503": {"credits": 4, "hours": 64},
    "23IZ504": {"credits": 3, "hours": 48},
    "23IZ510": {"credits": 2, "hours": 64},
    "23IZ511": {"credits": 2, "hours": 64},
    "23IG069": {"credits": 4, "hours": 192},

    # SEM 6
    "23IZ601": {"credits": 3, "hours": 48},
    "23IZ602": {"credits": 4, "hours": 64},
    "23IZ603": {"credits": 4, "hours": 64},
    "23IZ610": {"credits": 2, "hours": 64},
    "23Z611": {"credits": 1, "hours": 32},
    "23IG070": {"credits": 4, "hours": 192}
}


def analyze_attendance(email, password):

    # ============================================
    # GOOGLE SHEETS CONNECTION
    # ============================================

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = (
        ServiceAccountCredentials
        .from_json_keyfile_name(
            "google_credentials.json",
            scope
        )
    )

    client = gspread.authorize(creds)

    sheet = client.open(
        "Attendance Logs"
    ).sheet1

    # ============================================
    # CREATE SESSION
    # ============================================

    session = requests.Session()

    # ============================================
    # OPEN LOGIN PAGE
    # ============================================

    url = "https://ecampus.psgias.ac.in/"

    page = session.get(url)

    # ============================================
    # EXTRACT TOKEN
    # ============================================

    soup = BeautifulSoup(
        page.text,
        "html.parser"
    )

    token = soup.find(
        "input",
        {"name": "__RequestVerificationToken"}
    )["value"]

    # ============================================
    # LOGIN PAYLOAD
    # ============================================

    payload = {
        "email": email,
        "password": password,
        "__RequestVerificationToken": token
    }

    # ============================================
    # LOGIN REQUEST
    # ============================================

    login_url = (
        "https://ecampus.psgias.ac.in/"
        "Login/UserLoginTest"
    )

    response = session.post(
        login_url,
        data=payload
    )

    # ============================================
    # LOGIN FAILED
    # ============================================

    if "Home/Home" not in response.url:

        sheet.append_row([
            email,
            str(datetime.now()),
            "FAILED"
        ])

        return {
            "success": False,
            "message": "Login Failed"
        }

    # ============================================
    # LOGIN SUCCESS
    # ============================================

    sheet.append_row([
        email,
        str(datetime.now()),
        "SUCCESS"
    ])

    # ============================================
    # FETCH ATTENDANCE PAGE
    # ============================================

    attendance_url = (
        "https://ecampus.psgias.ac.in/"
        "AttpercCons/AttPercCons"
    )

    attendance = session.get(
        attendance_url
    )

    # ============================================
    # PARSE HTML
    # ============================================

    attendance_soup = BeautifulSoup(
        attendance.text,
        "html.parser"
    )

    table = attendance_soup.find("table")

    rows = table.find_all("tr")

    # ============================================
    # FINAL RESULTS LIST
    # ============================================

    results = []

    # ============================================
    # PROCESS EACH SUBJECT
    # ============================================

    for row in rows[1:]:

        cols = row.find_all("td")

        if len(cols) > 0:

            try:

                course_code = cols[0].text.strip()

                course_name = cols[1].text.strip()

                current_total_hours = int(
                    cols[2].text.strip()
                )

                absent_hours = int(
                    cols[6].text.strip()
                )

                current_attendance = float(
                    cols[8].text.strip()
                )

                # ============================================
                # SUBJECT LOOKUP FROM DICTIONARY
                # ============================================

                subject = subjects.get(course_code)

                if subject is None:
                    continue

                credits = subject["credits"]

                final_total_hours = subject["hours"]

                # ============================================
                # SAFE LEAVE CALCULATIONS
                # ============================================

                max_absent_75 = int(
                    final_total_hours * 0.25
                )

                safe_75 = max(
                    0,
                    max_absent_75 - absent_hours
                )

                max_absent_80 = int(
                    final_total_hours * 0.20
                )

                safe_80 = max(
                    0,
                    max_absent_80 - absent_hours
                )

                max_absent_90 = int(
                    final_total_hours * 0.10
                )

                safe_90 = max(
                    0,
                    max_absent_90 - absent_hours
                )

                # ============================================
                # ADD RESULTS
                # ============================================

                results.append({

                    "course_code": course_code,

                    "subject": course_name,

                    "attendance": current_attendance,

                    "credits": credits,

                    "total_hours": current_total_hours,

                    "absents": absent_hours,

                    "safe75": safe_75,

                    "safe80": safe_80,

                    "safe90": safe_90

                })

            except Exception as e:

                print("ERROR:", e)

    # ============================================
    # RETURN RESULTS
    # ============================================

    return {

        "success": True,

        "results": results

    }