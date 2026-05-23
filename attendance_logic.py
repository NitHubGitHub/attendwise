import requests
import mysql.connector
import gspread

from bs4 import BeautifulSoup
from datetime import datetime

from oauth2client.service_account import (
    ServiceAccountCredentials
)

def analyze_attendance(email, password):

    # ============================================
    # MYSQL CONNECTION
    # ============================================

    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="dbms@2026",
        database="attendance_system"
    )

    cursor = db.cursor(dictionary=True)

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

        cursor.close()
        db.close()

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

                # ============================================
                # SCRAPED VALUES
                # ============================================

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
                # GET MYSQL DATA
                # ============================================

                query = """
                SELECT credits, expected_total_hours
                FROM subjects
                WHERE course_code = %s
                """

                cursor.execute(
                    query,
                    (course_code,)
                )

                subject = cursor.fetchone()

                if subject is None:
                    continue

                credits = subject["credits"]

                # ============================================
                # SAFETY HOURS LOGIC
                # ============================================

                if credits == 4:

                    final_total_hours = 64

                elif credits == 3:

                    final_total_hours = 48

                elif credits == 2:

                    final_total_hours = 64

                else:

                    final_total_hours = (
                        subject[
                            "expected_total_hours"
                        ]
                    )

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
    # CLOSE MYSQL
    # ============================================

    cursor.close()
    db.close()

    # ============================================
    # RETURN RESULTS
    # ============================================

    return {

        "success": True,

        "results": results

    }