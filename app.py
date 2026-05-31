from flask import (
    Flask,
    render_template_string,
    request,
    session
)

from attendance_logic import analyze_attendance
from feedback import submit_feedback
from history import get_student_history

app = Flask(__name__)

# ============================================
# SECRET KEY
# ============================================

app.secret_key = "attendwise-secret-key"

# ============================================
# HOME PAGE
# ============================================

@app.route("/")
def home():

    with open(
    "templates/index.html",
    "r",
    encoding="utf-8"
	     ) as f:

           return f.read()

@app.route("/history")
def history():

    roll = session.get(
        "roll_number"
    )

    history_rows = (
        get_student_history(roll)
    )

    html = """

    <html>

    <head>

        <title>
            Attendance History
        </title>

        <style>

            body{
                background:#111827;
                color:white;
                font-family:Arial;
                padding:40px;
            }

            .record-btn{

                display:block;

                width:300px;

                margin:15px auto;

                padding:18px;

                background:#2563EB;

                color:white;

                text-decoration:none;

                text-align:center;

                border-radius:12px;

                font-size:18px;
            }

        </style>

    </head>

    <body>

        <h1
        style="text-align:center;"
        >
            Attendance History
        </h1>

    """
    for i, row in enumerate(history_rows):

        valid_until = row.get(
            "ValidUntil",
            "Unknown"
        )

        html += f"""

        <a
        href="/history/{i}"
        class="record-btn"
        >

        📅 {valid_until}

        </a>

        """
    html += """

    </body>

    </html>

    """

    return html

@app.route("/history/<int:index>")

# ============================================
# ANALYZE ATTENDANCE
# ============================================

@app.route("/analyze", methods=["POST"])
def analyze():

    email = request.form.get("email")

    password = request.form.get("password")

    data = analyze_attendance(email, password)

    # ============================================
    # LOGIN FAILED
    # ============================================

    if data["success"] == False:

        return """
        <body style="
            background:#111827;
            color:white;
            font-family:Arial;
            text-align:center;
            padding-top:100px;
        ">
            <h1>Login Failed</h1>

            <h2>
            Invalid Roll Number or Password
            </h2>

            <a href="/" style="
                color:#3B82F6;
                font-size:20px;
            ">
                Go Back
            </a>
        </body>
        """

    # ============================================
    # STORE ROLL NUMBER IN SESSION
    # ============================================

    session["roll_number"] = email

    # ============================================
    # SUCCESS
    # ============================================

    results = data["results"]

    html = """

    <!DOCTYPE html>

    <html>

    <head>

        <title>Attendance Dashboard</title>

        <style>

            *{
                margin:0;
                padding:0;
                box-sizing:border-box;
                font-family:Arial, Helvetica, sans-serif;
            }

            body{
                background:#111827;
                color:white;
                padding:40px;
            }

            .container{
                max-width:1400px;
                margin:auto;
            }

            .title{
                text-align:center;
                margin-bottom:50px;
            }

            .title h1{
                font-size:42px;
                margin-bottom:10px;
            }

            .title p{
                color:#9CA3AF;
                font-size:18px;
            }

            .grid{
                display:grid;
                grid-template-columns:
                repeat(auto-fit, minmax(330px, 1fr));

                gap:25px;
            }

            .card{
                background:#1F2937;
                padding:25px;
                border-radius:20px;

                box-shadow:
                0px 10px 30px rgba(0,0,0,0.3);
            }

            .subject{
                font-size:24px;
                margin-bottom:12px;
            }

            .course-code{
                color:#9CA3AF;
                margin-bottom:15px;
            }

            .attendance{
                font-size:20px;
                margin-bottom:20px;
            }

            .progress-container{
                width:100%;
                height:14px;
                background:#374151;
                border-radius:20px;
                overflow:hidden;
                margin-bottom:25px;
            }

            .progress-bar{
                height:100%;
                border-radius:20px;
            }

            .safe-box{
                display:flex;
                justify-content:space-between;

                background:#374151;

                padding:14px;
                border-radius:12px;

                margin-bottom:12px;
            }

            .green{
                color:#10B981;
                font-weight:bold;
            }

            .yellow{
                color:#FBBF24;
                font-weight:bold;
            }

            .red{
                color:#EF4444;
                font-weight:bold;
            }

            .details{
                margin-top:20px;
                color:#D1D5DB;
                line-height:1.8;
            }

            .back-btn{

                display:inline-block;

                margin-top:40px;

                padding:15px 25px;

                background:#2563EB;

                color:white;

                text-decoration:none;

                border-radius:12px;
            }

            .back-btn:hover{
                background:#1D4ED8;
            }

        </style>

    </head>

    <body>

        <div class="container">

            <div class="title">

                <h1>Attendance Dashboard</h1>

                <p>
                    Live attendance analytics and safe bunk predictions
                </p>

            </div>

            <div class="title">

    <h1>Attendance Dashboard</h1>

    <p>
        Live attendance analytics and safe bunk predictions
    </p>

    </div>

    <div style="text-align:center; margin-bottom:35px;">

        <a href="/history"
        style="
        display:inline-block;
        background:#2563EB;
        color:white;
        text-decoration:none;
        padding:15px 30px;
        border-radius:12px;
        font-size:18px;
        font-weight:bold;
        ">

        📚 View Previous Attendance Records

        </a>

    </div>

    <div class="grid">

	

            <div class="grid">

    """

    # ============================================
    # GENERATE SUBJECT CARDS
    # ============================================

    for subject in results:

        attendance = subject["attendance"]

        # PROGRESS BAR COLOR

        if attendance >= 90:
            bar_color = "#10B981"

        elif attendance >= 75:
            bar_color = "#FBBF24"

        else:
            bar_color = "#EF4444"

        html += f"""

        <div class="card">

            <div class="subject">
                {subject['subject']}
            </div>

            <div class="course-code">
                {subject['course_code']}
            </div>

            <div class="attendance">
                Attendance:
                <b>{attendance}%</b>
            </div>

            <div class="progress-container">

                <div
                    class="progress-bar"

                    style="
                        width:{attendance}%;
                        background:{bar_color};
                    "
                ></div>

            </div>

            <div class="safe-box">

                <span>
                    Safe Leaves for 75%
                </span>

                <span class="green">
                    {subject['safe75']}
                </span>

            </div>

            <div class="safe-box">

                <span>
                    Safe Leaves for 80%
                </span>

                <span class="yellow">
                    {subject['safe80']}
                </span>

            </div>

            <div class="safe-box">

                <span>
                    Safe Leaves for 90%
                </span>

                <span class="red">
                    {subject['safe90']}
                </span>

            </div>

            <div class="details">

                Credits:
                {subject['credits']}
                <br>

                Current Absents:
                {subject['absents']}
                <br>

                Total Hours:
                {subject['total_hours']}

            </div>

        </div>

        """

    # ============================================
    # END HTML
    # ============================================

    html += """

            </div>

            <a href="/" class="back-btn">
                Analyze Another Student
            </a>

        </div>

    </body>

    </html>

    """

    return render_template_string(html)

# ============================================
# FEEDBACK ROUTE
# ============================================

@app.route("/feedback", methods=["POST"])
def feedback():

    message = request.form.get("message")

    roll_number = session.get(
        "roll_number",
        "Anonymous"
    )

    success = submit_feedback(
        roll_number,
        message
    )

    return {
        "success": success
    }

# ============================================
# RUN FLASK
# ============================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )