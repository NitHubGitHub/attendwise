import requests
import gspread

from bs4 import BeautifulSoup
from datetime import datetime

import os
import json

from subjects import subjects

from oauth2client.service_account import (
    ServiceAccountCredentials
)

# ============================================
# ANALYZE ATTENDANCE
# ============================================

def analyze_attendance(email, password):

    # ============================================
    # GOOGLE SHEETS CONNECTION
    # ============================================

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    # ============================================
    # LOCAL / RENDER CREDS SUPPORT
    # ============================================

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

    page = session.get(
        url,
        timeout=15
    )

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
        data=payload,
        timeout=15
    )

    # ============================================
    # LOGIN FAILED
    # ============================================

    if "Home/Home" not in response.url:

        sheet.append_row([
            email,
            "Unknown",
            str(datetime.now()),
            "FAILED"
        ])

        return {
            "success": False,
            "message": "Login Failed"
        }

    # ============================================
    # EXTRACT STUDENT NAME
    # ============================================

    try:

        home_soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        name_div = home_soup.find(
            "div",
            class_="d-none d-xl-block ps-2"
        )

        if name_div:

            inner_div = name_div.find("div")

            if inner_div:

                name = inner_div.text.strip()

            else:

                name = "Unknown"

        else:

            name = "Unknown"

    except Exception:

        name = "Unknown"

    # ============================================
    # LOGIN SUCCESS
    # ============================================

    sheet.append_row([
        email,
        name,
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
        attendance_url,
        timeout=15
    )

    # ============================================
    # PARSE HTML
    # ============================================

    attendance_soup = BeautifulSoup(
        attendance.text,
        "html.parser"
    )

    table = attendance_soup.find("table")

    # ============================================
    # SAFETY CHECK
    # ============================================

    if table is None:

        return {
            "success": False,
            "message": "Attendance table not found"
        }

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
                # SUBJECT LOOKUP
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