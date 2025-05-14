import streamlit as st
import pandas as pd
import io
import base64
import os
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import pyrebase
from fpdf import FPDF
import json
import time

# Firebase configuration
firebase_config = {
    "apiKey": "AIzaSyBTsa0pgK0R6aDOxPe_c_MBdKR4XaHPGGA",
    "authDomain": "tracking-c62bb.firebaseapp.com",
    "databaseURL": "https://tracking-c62bb-default-rtdb.firebaseio.com",
    "projectId": "tracking-c62bb",
    "storageBucket": "tracking-c62bb.firebasestorage.app",
    "messagingSenderId": "977902624059",
    "appId": "1:977902624059:web:165e120df5463bde332b1e",
    "measurementId": "G-PNHDJF45Z6"
}

# Initialize Firebase
try:
    firebase = pyrebase.initialize_app(firebase_config)
    auth = firebase.auth()
    db = firebase.database()
except Exception as e:
    st.error(f"Firebase initialization failed: {e}. Check configuration.")
    auth = None
    db = None

# Email configuration
EMAIL_SENDER = "projecttestingsubhash@gmail.com"
EMAIL_PASSWORD = "zgwynxksfnwzusyk"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Task and issue options
PRIORITY_OPTIONS = ["Low", "Medium", "High", "Critical"]
STATUS_OPTIONS = ["To Do", "In Progress", "On Hold", "Done"]
ISSUE_TYPES = ["Bug", "Feature", "Enhancement", "Documentation", "Other"]

# Colors for priorities and statuses
PRIORITY_COLORS = {
    "Low": "#28a745",      # Green
    "Medium": "#ffc107",   # Yellow
    "High": "#fd7e14",     # Orange
    "Critical": "#dc3545"  # Red
}

STATUS_COLORS = {
    "To Do": "#6c757d",        # Gray
    "In Progress": "#007bff",  # Blue
    "On Hold": "#6f42c1",      # Purple
    "Done": "#28a745"          # Green
}

# Custom CSS
def load_css():
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem !important;
            font-weight: 700 !important;
            color: #3366ff !important;
            margin-bottom: 1.5rem !important;
            text-align: center !important;
        }
        .card {
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        .card-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        .card-subtitle {
            font-size: 0.9rem;
            color: #6c757d;
            margin-bottom: 0.5rem;
        }
        .tag {
            border-radius: 4px;
            padding: 0.2rem 0.5rem;
            font-size: 0.8rem;
            font-weight: 500;
            color: white;
            display: inline-block;
            margin-right: 0.3rem;
        }
        .priority-low { background-color: #28a745; }
        .priority-medium { background-color: #ffc107; color: #212529; }
        .priority-high { background-color: #fd7e14; }
        .priority-critical { background-color: #dc3545; }
        .status-todo { background-color: #6c757d; }
        .status-progress { background-color: #007bff; }
        .status-hold { background-color: #6f42c1; }
        .status-done { background-color: #28a745; }
        .tab-subheader {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #495057;
        }
        .stat-box {
            text-align: center;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            background-color: #f8f9fa;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #3366ff;
        }
        .stat-label {
            font-size: 0.9rem;
            color: #6c757d;
        }
        .form-container {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .btn-primary {
            background-color: #3366ff;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            color: white;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        .btn-primary:hover {
            background-color: #2952cc;
        }
        .btn-danger {
            background-color: #dc3545;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            color: white;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        .btn-danger:hover {
            background-color: #c82333;
        }
        .footer {
            text-align: center;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #dee2e6;
            color: #6c757d;
            font-size: 0.9rem;
        }
        .profile-container {
            text-align: center;
            padding: 1.5rem;
            background-color: #f8f9fa;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 1.5rem;
        }
        .profile-name {
            font-size: 1.3rem;
            font-weight: 600;
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .profile-email {
            color: #6c757d;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        @keyframes pulse {
            0% { opacity: 0.6; }
            50% { opacity: 1; }
            100% { opacity: 0.6; }
        }
        .loading {
            animation: pulse 1.5s infinite;
        }
    </style>
    """, unsafe_allow_html=True)

# Authentication helper
def refresh_user_token():
    if "user" in st.session_state and st.session_state.user:
        try:
            user = st.session_state.user
            if user.get('expiresIn'):
                expires_in = int(user['expiresIn'])
                login_time = st.session_state.get('login_time', 0)
                current_time = time.time()
                if current_time - login_time > expires_in - 300:
                    refreshed_user = auth.refresh(user['refreshToken'])
                    st.session_state.user = {
                        'idToken': refreshed_user['idToken'],
                        'refreshToken': refreshed_user['refreshToken'],
                        'expiresIn': refreshed_user['expiresIn'],
                        'localId': refreshed_user['userId']
                    }
                    st.session_state.user_id = refreshed_user['userId']
                    st.session_state.login_time = time.time()
                    st.session_state.debug_auth = "Token refreshed successfully"
                    return True
            st.session_state.debug_auth = "Token still valid"
            return True
        except Exception as e:
            st.session_state.debug_auth = f"Token refresh failed: {str(e)}"
            return False
    st.session_state.debug_auth = "No user session found"
    return False

# Send email
def send_email(recipient_email, subject, body, attachment_path=None):
    if not recipient_email:
        st.error("No email address available.")
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={os.path.basename(attachment_path)}'
            )
            msg.attach(part)
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email sending failed: {e}")
        return False

# Report generation
def generate_task_report_pdf(tasks, issues, user_info, team_members):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Task and Issue Report", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(0, 10, f"Generated by: {user_info.get('name', 'Unknown')}", ln=True)
    pdf.ln(10)
    
    # Task Summary
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Task Summary", ln=True)
    pdf.set_font("Arial", "", 12)
    status_counts = {status: 0 for status in STATUS_OPTIONS}
    for task in tasks:
        status_counts[task.get('status', 'To Do')] += 1
    for status, count in status_counts.items():
        pdf.cell(0, 10, f"{status}: {count} tasks", ln=True)
    pdf.ln(5)
    
    # Issue Summary
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Issue Summary", ln=True)
    pdf.set_font("Arial", "", 12)
    issue_status_counts = {status: 0 for status in STATUS_OPTIONS}
    for issue in issues:
        issue_status_counts[issue.get('status', 'To Do')] += 1
    for status, count in issue_status_counts.items():
        pdf.cell(0, 10, f"{status}: {count} issues", ln=True)
    pdf.ln(5)
    
    # Task Details
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Task Details", ln=True)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, "Task Name", border=1)
    pdf.cell(30, 10, "Priority", border=1)
    pdf.cell(30, 10, "Status", border=1)
    pdf.cell(30, 10, "Issue Type", border=1)
    pdf.cell(40, 10, "Assignee", border=1)
    pdf.cell(30, 10, "Due Date", border=1, ln=True)
    pdf.set_font("Arial", "", 12)
    for task in tasks:
        assignee_username = "Unassigned"
        for member in team_members:
            if member.get('id') == task.get('assignee'):
                assignee_username = member.get('username', 'Unknown')
                break
        task_name = task.get('title', 'Unnamed Task')
        if len(task_name) > 20:
            task_name = task_name[:17] + "..."
        pdf.cell(50, 10, task_name, border=1)
        pdf.cell(30, 10, task.get('priority', 'Medium'), border=1)
        pdf.cell(30, 10, task.get('status', 'To Do'), border=1)
        pdf.cell(30, 10, task.get('issue_type', 'Other'), border=1)
        pdf.cell(40, 10, assignee_username, border=1)
        pdf.cell(30, 10, task.get('due_date', ''), border=1, ln=True)
    
    # Issue Details
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Issue Details", ln=True)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, "Issue Title", border=1)
    pdf.cell(30, 10, "Type", border=1)
    pdf.cell(30, 10, "Status", border=1)
    pdf.cell(40, 10, "Related Task", border=1)
    pdf.cell(30, 10, "Assignee", border=1)
    pdf.cell(30, 10, "Due Date", border=1, ln=True)
    pdf.set_font("Arial", "", 12)
    for issue in issues:
        assignee_username = "Unassigned"
        for member in team_members:
            if member.get('id') == issue.get('assignee'):
                assignee_username = member.get('username', 'Unknown')
                break
        related_task_title = "None"
        for task in tasks:
            if task.get('id') == issue.get('related_task'):
                related_task_title = task.get('title', 'Unnamed Task')
                break
        issue_title = issue.get('title', 'Unnamed Issue')
        if len(issue_title) > 20:
            issue_title = issue_title[:17] + "..."
        pdf.cell(50, 10, issue_title, border=1)
        pdf.cell(30, 10, issue.get('issue_type', 'Other'), border=1)
        pdf.cell(30, 10, issue.get('status', 'To Do'), border=1)
        pdf.cell(40, 10, related_task_title, border=1)
        pdf.cell(30, 10, assignee_username, border=1)
        pdf.cell(30, 10, issue.get('due_date', ''), border=1, ln=True)
    
    report_path = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(report_path)
    return report_path

def generate_eod_report(tasks, issues, user_info, team_members):
    today = datetime.now().strftime('%Y-%m-%d')
    updated_tasks = [task for task in tasks if task.get('last_updated', '').startswith(today)]
    updated_issues = [issue for issue in issues if issue.get('last_updated', '').startswith(today)]
    status_counts = {status: 0 for status in STATUS_OPTIONS}
    issue_status_counts = {status: 0 for status in STATUS_OPTIONS}
    for task in tasks:
        status_counts[task.get('status', 'To Do')] += 1
    for issue in issues:
        issue_status_counts[issue.get('status', 'To Do')] += 1
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    tasks_due_soon = [task for task in tasks if task.get('due_date', '') in (today, tomorrow) and task.get('status', '') != 'Done']
    issues_due_soon = [issue for issue in issues if issue.get('due_date', '') in (today, tomorrow) and issue.get('status', '') != 'Done']
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1, h2, h3 {{ color: #3366ff; }}
            .header {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .summary {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
            .summary-item {{ text-align: center; padding: 10px; background-color: #f8f9fa; border-radius: 5px; width: 22%; }}
            .summary-value {{ font-size: 24px; font-weight: bold; color: #3366ff; }}
            .summary-label {{ font-size: 14px; color: #666; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            .priority-low {{ background-color: #d4edda; }}
            .priority-medium {{ background-color: #fff3cd; }}
            .priority-high {{ background-color: #ffe5d0; }}
            .priority-critical {{ background-color: #f8d7da; }}
            .footer {{ margin-top: 30px; font-size: 14px; color: #666; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>EOD Report - {today}</h1>
                <p>Generated by: {user_info.get('name', 'Unknown')}</p>
            </div>
            <h2>Task Status Summary</h2>
            <div class="summary">
                <div class="summary-item">
                    <div class="summary-value">{status_counts['To Do']}</div>
                    <div class="summary-label">To Do</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{status_counts['In Progress']}</div>
                    <div class="summary-label">In Progress</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{status_counts['On Hold']}</div>
                    <div class="summary-label">On Hold</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{status_counts['Done']}</div>
                    <div class="summary-label">Done</div>
                </div>
            </div>
            <h2>Issue Status Summary</h2>
            <div class="summary">
                <div class="summary-item">
                    <div class="summary-value">{issue_status_counts['To Do']}</div>
                    <div class="summary-label">To Do</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{issue_status_counts['In Progress']}</div>
                    <div class="summary-label">In Progress</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{issue_status_counts['On Hold']}</div>
                    <div class="summary-label">On Hold</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{issue_status_counts['Done']}</div>
                    <div class="summary-label">Done</div>
                </div>
            </div>
    """
    if updated_tasks:
        html += """
            <h2>Today's Task Updates</h2>
            <table>
                <tr>
                    <th>Task</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Issue Type</th>
                    <th>Assignee</th>
                </tr>
        """
        for task in updated_tasks:
            assignee_username = "Unassigned"
            for member in team_members:
                if member.get('id') == task.get('assignee'):
                    assignee_username = member.get('username', 'Unknown')
                    break
            priority_class = f"priority-{task.get('priority', 'Medium').lower()}"
            html += f"""
                <tr class="{priority_class}">
                    <td>{task.get('title', 'Unnamed Task')}</td>
                    <td>{task.get('status', 'To Do')}</td>
                    <td>{task.get('priority', 'Medium')}</td>
                    <td>{task.get('issue_type', 'Other')}</td>
                    <td>{assignee_username}</td>
                </tr>
            """
        html += "</table>"
    else:
        html += "<h2>Today's Task Updates</h2><p>No tasks were updated today.</p>"
    
    if updated_issues:
        html += """
            <h2>Today's Issue Updates</h2>
            <table>
                <tr>
                    <th>Issue</th>
                    <th>Status</th>
                    <th>Type</th>
                    <th>Related Task</th>
                    <th>Assignee</th>
                </tr>
        """
        for issue in updated_issues:
            assignee_username = "Unassigned"
            related_task_title = "None"
            for member in team_members:
                if member.get('id') == issue.get('assignee'):
                    assignee_username = member.get('username', 'Unknown')
                    break
            for task in tasks:
                if task.get('id') == issue.get('related_task'):
                    related_task_title = task.get('title', 'Unnamed Task')
                    break
            priority_class = f"priority-{issue.get('priority', 'Medium').lower()}"
            html += f"""
                <tr class="{priority_class}">
                    <td>{issue.get('title', 'Unnamed Issue')}</td>
                    <td>{issue.get('status', 'To Do')}</td>
                    <td>{issue.get('issue_type', 'Other')}</td>
                    <td>{related_task_title}</td>
                    <td>{assignee_username}</td>
                </tr>
            """
        html += "</table>"
    else:
        html += "<h2>Today's Issue Updates</h2><p>No issues were updated today.</p>"
    
    if tasks_due_soon or issues_due_soon:
        if tasks_due_soon:
            html += """
                <h2>Tasks Due Soon</h2>
                <table>
                    <tr>
                        <th>Task</th>
                        <th>Due Date</th>
                        <th>Priority</th>
                        <th>Issue Type</th>
                        <th>Assignee</th>
                    </tr>
            """
            for task in tasks_due_soon:
                assignee_username = "Unassigned"
                for member in team_members:
                    if member.get('id') == task.get('assignee'):
                        assignee_username = member.get('username', 'Unknown')
                        break
                priority_class = f"priority-{task.get('priority', 'Medium').lower()}"
                html += f"""
                    <tr class="{priority_class}">
                        <td>{task.get('title', 'Unnamed Task')}</td>
                        <td>{task.get('due_date', 'No due date')}</td>
                        <td>{task.get('priority', 'Medium')}</td>
                        <td>{task.get('issue_type', 'Other')}</td>
                        <td>{assignee_username}</td>
                    </tr>
                """
            html += "</table>"
        if issues_due_soon:
            html += """
                <h2>Issues Due Soon</h2>
                <table>
                    <tr>
                        <th>Issue</th>
                        <th>Due Date</th>
                        <th>Type</th>
                        <th>Related Task</th>
                        <th>Assignee</th>
                    </tr>
            """
            for issue in issues_due_soon:
                assignee_username = "Unassigned"
                related_task_title = "None"
                for member in team_members:
                    if member.get('id') == issue.get('assignee'):
                        assignee_username = member.get('username', 'Unknown')
                        break
                for task in tasks:
                    if task.get('id') == issue.get('related_task'):
                        related_task_title = task.get('title', 'Unnamed Task')
                        break
                priority_class = f"priority-{issue.get('priority', 'Medium').lower()}"
                html += f"""
                    <tr class="{priority_class}">
                        <td>{issue.get('title', 'Unnamed Issue')}</td>
                        <td>{issue.get('due_date', 'No due date')}</td>
                        <td>{issue.get('issue_type', 'Other')}</td>
                        <td>{related_task_title}</td>
                        <td>{assignee_username}</td>
                    </tr>
                """
            html += "</table>"
    else:
        html += "<h2>Tasks and Issues Due Soon</h2><p>No tasks or issues are due soon.</p>"
    
    html += """
            <div class="footer">
                <p>This is an automated report from the Task Management System.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

# User management
def extract_username_from_email(email):
    if email and '@' in email:
        return email.split('@')[0]
    return "user"

def get_user_info(user_id):
    if not db:
        return {"name": "Unknown", "email": "unknown@example.com"}
    try:
        user_data = db.child("users").child(user_id).get().val()
        if user_data:
            return user_data
        return {"name": "Unknown", "email": "unknown@example.com"}
    except Exception as e:
        st.error(f"Error getting user info: {e}")
        return {"name": "Unknown", "email": "unknown@example.com"}

def get_team_members(project_id):
    if not db:
        return []
    try:
        members = db.child("project_members").child(project_id).get().val()
        if not members:
            return []
        team = []
        for member_id, role in members.items():
            user_data = get_user_info(member_id)
            team.append({
                "id": member_id,
                "name": user_data.get("name", "Unknown"),
                "email": user_data.get("email", "unknown@example.com"),
                "username": extract_username_from_email(user_data.get("email", "")),
                "role": role
            })
        return team
    except Exception as e:
        st.error(f"Error getting team members: {e}")
        return []

def get_user_projects(user_id):
    if not db:
        return []
    try:
        all_projects = db.child("projects").get().val()
        if not all_projects:
            return []
        user_projects = []
        for project_id, project_data in all_projects.items():
            members = db.child("project_members").child(project_id).get().val()
            if members and user_id in members:
                project_data["id"] = project_id
                user_projects.append(project_data)
        return user_projects
    except Exception as e:
        st.error(f"Error getting user projects: {e}")
        return []

def get_project_tasks(project_id):
    if not db:
        return []
    try:
        tasks = db.child("tasks").child(project_id).get().val()
        if not tasks:
            return []
        task_list = []
        for task_id, task_data in tasks.items():
            task_data["id"] = task_id
            task_list.append(task_data)
        task_list.sort(key=lambda x: (
            PRIORITY_OPTIONS.index(x.get("priority", "Medium")),
            x.get("due_date", "9999-12-31")
        ))
        return task_list
    except Exception as e:
        st.error(f"Error getting project tasks: {e}")
        return []

def get_project_issues(project_id):
    if not db:
        return []
    try:
        issues = db.child("issues").child(project_id).get().val()
        if not issues:
            return []
        issue_list = []
        for issue_id, issue_data in issues.items():
            issue_data["id"] = issue_id
            issue_list.append(issue_data)
        issue_list.sort(key=lambda x: (
            PRIORITY_OPTIONS.index(x.get("priority", "Medium")),
            x.get("due_date", "9999-12-31")
        ))
        return issue_list
    except Exception as e:
        st.error(f"Error getting project issues: {e}")
        return []

# Firebase login
def login():
    # Check if user is already authenticated
    if "user" in st.session_state and st.session_state.user:
        if refresh_user_token():
            # Debug: Display authentication status
            if "debug_auth" in st.session_state:
                st.info(f"Auth Debug: {st.session_state.debug_auth}")
            return True
        else:
            st.session_state.user = None
            st.session_state.user_id = None
            st.session_state.user_info = None
            st.session_state.debug_auth = "Session cleared due to refresh failure"
    
    st.session_state.user = None
    with st.container():
        st.markdown('<h1 class="main-header">Task Management System</h1>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            login_option = st.selectbox("Choose login method", ["Email/Password", "Sign Up"])
            if login_option == "Email/Password":
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.button("Login", key="login_btn"):
                    try:
                        user = auth.sign_in_with_email_and_password(email, password)
                        st.session_state.user = {
                            'idToken': user['idToken'],
                            'refreshToken': user['refreshToken'],
                            'expiresIn': user['expiresIn'],
                            'localId': user['localId']
                        }
                        st.session_state.user_id = user['localId']
                        st.session_state.login_time = time.time()
                        user_info = get_user_info(user['localId'])
                        if not user_info or user_info.get('name') == "Unknown":
                            username = extract_username_from_email(email)
                            user_info = {
                                "name": username.capitalize(),
                                "email": email,
                                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            db.child("users").child(user['localId']).set(user_info)
                        st.session_state.user_info = user_info
                        st.session_state.debug_auth = "Login successful"
                        st.success("Logged in successfully!")
                        st.rerun()
                    except Exception as e:
                        st.session_state.debug_auth = f"Login failed: {str(e)}"
                        st.error(f"Login failed: {e}")
            elif login_option == "Sign Up":
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                if st.button("Sign Up", key="signup_btn"):
                    if password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        try:
                            user = auth.create_user_with_email_and_password(email, password)
                            st.session_state.user = {
                                'idToken': user['idToken'],
                                'refreshToken': user['refreshToken'],
                                'expiresIn': user['expiresIn'],
                                'localId': user['localId']
                            }
                            st.session_state.user_id = user['localId']
                            st.session_state.login_time = time.time()
                            username = extract_username_from_email(email)
                            user_info = {
                                "name": username.capitalize(),
                                "email": email,
                                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            db.child("users").child(user['localId']).set(user_info)
                            st.session_state.user_info = user_info
                            st.session_state.debug_auth = "Signup successful"
                            st.success("Account created and logged in!")
                            st.rerun()
                        except Exception as e:
                            st.session_state.debug_auth = f"Signup failed: {str(e)}"
                            st.error(f"Sign up failed: {e}")
            # Debug: Display authentication status
            if "debug_auth" in st.session_state:
                st.info(f"Auth Debug: {st.session_state.debug_auth}")
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="footer">Task Management System © 2025</div>', unsafe_allow_html=True)
    return False

# Task and issue management
def create_task(project_id, task_data):
    if not db:
        st.error("Firebase database is not initialized.")
        return False
    try:
        task_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task_id = db.child("tasks").child(project_id).push(task_data)
        if task_id:
            return True
        else:
            st.error("Failed to create task: No task ID returned.")
            return False
    except Exception as e:
        st.error(f"Error creating task: {e}")
        return False

def update_task(project_id, task_id, task_data):
    if not db:
        st.error("Firebase database is not initialized.")
        return False
    try:
        task_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.child("tasks").child(project_id).child(task_id).update(task_data)
        return True
    except Exception as e:
        st.error(f"Error updating task: {e}")
        return False

def delete_task(project_id, task_id):
    if not db:
        st.error("Firebase database is not initialized.")
        return False
    try:
        db.child("tasks").child(project_id).child(task_id).remove()
        return True
    except Exception as e:
        st.error(f"Error deleting task: {e}")
        return False

def create_issue(project_id, issue_data):
    if not db:
        st.error("Firebase database is not initialized.")
        return False
    try:
        issue_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        issue_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        issue_id = db.child("issues").child(project_id).push(issue_data)
        if issue_id:
            return True
        else:
            st.error("Failed to create issue: No issue ID returned.")
            return False
    except Exception as e:
        st.error(f"Error creating issue: {e}")
        return False

def update_issue(project_id, issue_id, issue_data):
    if not db:
        st.error("Firebase database is not initialized.")
        return False
    try:
        issue_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.child("issues").child(project_id).child(issue_id).update(issue_data)
        return True
    except Exception as e:
        st.error(f"Error updating issue: {e}")
        return False

def delete_issue(project_id, issue_id):
    if not db:
        st.error("Firebase database is not initialized.")
        return False
    try:
        db.child("issues").child(project_id).child(issue_id).remove()
        return True
    except Exception as e:
        st.error(f"Error deleting issue: {e}")
        return False

def create_project(project_data, user_id):
    if not db:
        st.error("Firebase database is not initialized.")
        return None
    try:
        project_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        project_data["created_by"] = user_id
        project_id = db.child("projects").push(project_data)
        db.child("project_members").child(project_id["name"]).child(user_id).set("admin")
        return project_id["name"]
    except Exception as e:
        st.error(f"Error creating project: {e}")
        return None

def add_project_member(project_id, email, role="member"):
    if not db:
        st.error("Firebase database is not initialized.")
        return False
    try:
        users = db.child("users").get().val()
        if not users:
            st.error("No users found in database.")
            return False
        user_id = None
        for uid, user_data in users.items():
            if user_data.get("email") == email:
                user_id = uid
                break
        if not user_id:
            st.error(f"User with email {email} not found.")
            return False
        db.child("project_members").child(project_id).child(user_id).set(role)
        return True
    except Exception as e:
        st.error(f"Error adding project member: {e}")
        return False

def remove_project_member(project_id, user_id):
    if not db:
        st.error("Firebase database is not initialized.")
        return False
    try:
        db.child("project_members").child(project_id).child(user_id).remove()
        return True
    except Exception as e:
        st.error(f"Error removing project member: {e}")
        return False

# Navigation functions
def show_dashboard(user_id, user_info):
    st.markdown('<h2 class="tab-subheader">Dashboard</h2>', unsafe_allow_html=True)
    st.markdown(f"Welcome, {user_info.get('name', 'User')}!", unsafe_allow_html=True)
    projects = get_user_projects(user_id)
    total_tasks = 0
    total_issues = 0
    tasks_due_soon = 0
    issues_due_soon = 0
    today = datetime.now().strftime('%Y-%m-%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    for project in projects:
        tasks = get_project_tasks(project['id'])
        issues = get_project_issues(project['id'])
        total_tasks += len(tasks)
        total_issues += len(issues)
        tasks_due_soon += len([t for t in tasks if t.get('due_date', '') in (today, tomorrow) and t.get('status', '') != 'Done'])
        issues_due_soon += len([i for i in issues if i.get('due_date', '') in (today, tomorrow) and i.get('status', '') != 'Done'])
    cols = st.columns(4)
    with cols[0]:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-value">{len(projects)}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Projects</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-value">{total_tasks}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Tasks</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-value">{total_issues}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Issues</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[3]:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-value">{tasks_due_soon + issues_due_soon}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Due Soon</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def show_projects(user_id, user_info):
    st.markdown('<h2 class="tab-subheader">Your Projects</h2>', unsafe_allow_html=True)
    projects = get_user_projects(user_id)
    if not projects:
        st.info("You are not part of any projects yet. Create a new project to get started!")
    cols = st.columns(2)
    for i, project in enumerate(projects):
        with cols[i % 2]:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown(f'<div class="card-title">{project.get("name", "Unnamed Project")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="card-subtitle">{project.get("description", "No description")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="card-subtitle">Created: {project.get("created_at", "Unknown")}</div>', unsafe_allow_html=True)
                members = db.child("project_members").child(project["id"]).get().val()
                role = members.get(user_id, "Member") if members else "Member"
                st.markdown(f'<div class="card-subtitle">Role: {role}</div>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("View", key=f"view_{project['id']}"):
                        st.session_state.active_project = project['id']
                        st.rerun()
                with col2:
                    if role == "admin" and st.button("Manage", key=f"manage_{project['id']}"):
                        st.session_state.active_project = project['id']
                        st.session_state.show_project_settings = True
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("### Create New Project")
    with st.form("create_project_form"):
        project_name = st.text_input("Project Name")
        project_description = st.text_area("Project Description")
        submit = st.form_submit_button("Create Project")
        if submit:
            if not project_name:
                st.error("Project name is required.")
            else:
                project_data = {
                    "name": project_name,
                    "description": project_description
                }
                project_id = create_project(project_data, user_id)
                if project_id:
                    st.success(f"Project '{project_name}' created successfully!")
                    st.rerun()
                else:
                    st.error("Failed to create project.")

def show_tasks(user_id, user_info):
    st.markdown('<h2 class="tab-subheader">Tasks</h2>', unsafe_allow_html=True)
    if not st.session_state.active_project:
        st.warning("Please select a project from the Projects tab.")
        return
    project_id = st.session_state.active_project
    tasks = get_project_tasks(project_id)
    team_members = get_team_members(project_id)
    
    # Filters
    st.markdown("### Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_status = st.selectbox("Status", ["All"] + STATUS_OPTIONS, key="filter_status", index=["All"] + STATUS_OPTIONS.index(st.session_state.filter_status) if st.session_state.filter_status in STATUS_OPTIONS else 0)
        if selected_status != st.session_state.filter_status:
            st.session_state.filter_status = selected_status
    with col2:
        selected_priority = st.selectbox("Priority", ["All"] + PRIORITY_OPTIONS, key="filter_priority", index=["All"] + PRIORITY_OPTIONS.index(st.session_state.filter_priority) if st.session_state.filter_priority in PRIORITY_OPTIONS else 0)
        if selected_priority != st.session_state.filter_priority:
            st.session_state.filter_priority = selected_priority
    with col3:
        assignee_options = ["All"] + [m['username'] for m in team_members]
        selected_assignee = st.selectbox("Assignee", assignee_options, key="filter_assignee", index=assignee_options.index(st.session_state.filter_assignee) if st.session_state.filter_assignee in assignee_options else 0)
        if selected_assignee != st.session_state.filter_assignee:
            st.session_state.filter_assignee = selected_assignee
    
    # Apply filters
    filtered_tasks = tasks
    if st.session_state.filter_status != "All":
        filtered_tasks = [t for t in filtered_tasks if t.get('status', '') == st.session_state.filter_status]
    if st.session_state.filter_priority != "All":
        filtered_tasks = [t for t in filtered_tasks if t.get('priority', '') == st.session_state.filter_priority]
    if st.session_state.filter_assignee != "All":
        filtered_tasks = [t for t in filtered_tasks if any(m.get('id') == t.get('assignee') and m.get('username') == st.session_state.filter_assignee for m in team_members)]
    
    # Display tasks
    for task in filtered_tasks:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f'<div class="card-title">{task.get("title", "Unnamed Task")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-subtitle">{task.get("description", "No description")}</div>', unsafe_allow_html=True)
            st.markdown(f'<span class="tag priority-{task.get("priority", "Medium").lower()}">{task.get("priority", "Medium")}</span>', unsafe_allow_html=True)
            st.markdown(f'<span class="tag status-{task.get("status", "To Do").lower().replace(" ", "-")}">{task.get("status", "To Do")}</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-subtitle">Issue Type: {task.get("issue_type", "Other")}</div>', unsafe_allow_html=True)
            assignee = "Unassigned"
            for member in team_members:
                if member.get('id') == task.get('assignee'):
                    assignee = member.get('username', 'Unknown')
                    break
            st.markdown(f'<div class="card-subtitle">Assignee: {assignee}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-subtitle">Due: {task.get("due_date", "No due date")}</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Edit", key=f"edit_task_{task['id']}"):
                    st.session_state.active_task = task['id']
                    st.session_state.show_create_task = True
                    st.rerun()
            with col2:
                if st.button("Delete", key=f"delete_task_{task['id']}"):
                    if delete_task(project_id, task['id']):
                        st.success("Task deleted!")
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Create or edit task
    today = datetime.now().strftime('%Y-%m-%d')
    if st.session_state.show_create_task and st.session_state.active_task:
        task = next((t for t in tasks if t['id'] == st.session_state.active_task), None)
        st.markdown("### Edit Task")
    else:
        st.markdown("### Create New Task")
        task = None
    with st.form(key="task_form", clear_on_submit=False):
        title = st.text_input("Task Title", value=task.get('title', 'Basic ui design') if task else 'Basic ui design')
        description = st.text_area("Description", value=task.get('description', 'Pleaase') if task else 'Pleaase')
        issue_type = st.selectbox("Issue Type", ISSUE_TYPES, index=ISSUE_TYPES.index(task.get('issue_type', 'Feature')) if task else ISSUE_TYPES.index('Feature'))
        priority = st.selectbox("Priority", PRIORITY_OPTIONS, index=PRIORITY_OPTIONS.index(task.get('priority', 'Critical')) if task else PRIORITY_OPTIONS.index('Critical'))
        status = st.selectbox("Status", STATUS_OPTIONS, index=STATUS_OPTIONS.index(task.get('status', 'To Do')) if task else STATUS_OPTIONS.index('To Do'))
        assignee_options = ["Unassigned"] + [m['username'] for m in team_members]
        assignee = st.selectbox("Assignee", assignee_options, 
                                index=([m['username'] for m in team_members].index(task.get('assignee_username', 'chsubhash939')) + 1) if task and task.get('assignee_username') in [m['username'] for m in team_members] else assignee_options.index('chsubhash939') if 'chsubhash939' in assignee_options else 0)
        due_date = st.date_input("Due Date", value=datetime.strptime(task.get('due_date', today), '%Y-%m-%d') if task and task.get('due_date') else datetime.now())
        submit = st.form_submit_button("Save Task")
        if submit:
            if not title:
                st.error("Task title is required.")
            else:
                task_data = {
                    "title": title,
                    "description": description,
                    "issue_type": issue_type,
                    "priority": priority,
                    "status": status,
                    "assignee": next((m['id'] for m in team_members if m['username'] == assignee), None) if assignee != "Unassigned" else None,
                    "assignee_username": assignee if assignee != "Unassigned" else None,
                    "due_date": due_date.strftime('%Y-%m-%d')
                }
                if task:
                    if update_task(project_id, st.session_state.active_task, task_data):
                        st.success("Task updated!")
                        st.session_state.show_create_task = False
                        st.session_state.active_task = None
                        st.rerun()
                    else:
                        st.error("Failed to update task.")
                else:
                    if create_task(project_id, task_data):
                        st.success("Task created!")
                        st.session_state.show_create_task = False
                        st.rerun()
                    else:
                        st.error("Failed to create task. Check Firebase configuration and permissions.")

def show_issues(user_id, user_info):
    st.markdown('<h2 class="tab-subheader">Issues</h2>', unsafe_allow_html=True)
    if not st.session_state.active_project:
        st.warning("Please select a project from the Projects tab.")
        return
    project_id = st.session_state.active_project
    issues = get_project_issues(project_id)
    tasks = get_project_tasks(project_id)
    team_members = get_team_members(project_id)
    
    # Filters
    st.markdown("### Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_status = st.selectbox("Status", ["All"] + STATUS_OPTIONS, key="issue_filter_status", index=["All"] + STATUS_OPTIONS.index(st.session_state.issue_filter_status) if st.session_state.issue_filter_status in STATUS_OPTIONS else 0)
        if selected_status != st.session_state.issue_filter_status:
            st.session_state.issue_filter_status = selected_status
    with col2:
        selected_type = st.selectbox("Issue Type", ["All"] + ISSUE_TYPES, key="issue_filter_type", index=["All"] + ISSUE_TYPES.index(st.session_state.issue_filter_type) if st.session_state.issue_filter_type in ISSUE_TYPES else 0)
        if selected_type != st.session_state.issue_filter_type:
            st.session_state.issue_filter_type = selected_type
    with col3:
        assignee_options = ["All"] + [m['username'] for m in team_members]
        selected_assignee = st.selectbox("Assignee", assignee_options, key="issue_filter_assignee", index=assignee_options.index(st.session_state.issue_filter_assignee) if st.session_state.issue_filter_assignee in assignee_options else 0)
        if selected_assignee != st.session_state.issue_filter_assignee:
            st.session_state.issue_filter_assignee = selected_assignee
    
    # Apply filters
    filtered_issues = issues
    if st.session_state.issue_filter_status != "All":
        filtered_issues = [i for i in filtered_issues if i.get('status', '') == st.session_state.issue_filter_status]
    if st.session_state.issue_filter_type != "All":
        filtered_issues = [i for i in filtered_issues if i.get('issue_type', '') == st.session_state.issue_filter_type]
    if st.session_state.issue_filter_assignee != "All":
        filtered_issues = [i for i in filtered_issues if any(m.get('id') == i.get('assignee') and m.get('username') == st.session_state.issue_filter_assignee for m in team_members)]
    
    # Display issues
    for issue in filtered_issues:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f'<div class="card-title">{issue.get("title", "Unnamed Issue")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-subtitle">{issue.get("description", "No description")}</div>', unsafe_allow_html=True)
            st.markdown(f'<span class="tag priority-{issue.get("priority", "Medium").lower()}">{issue.get("priority", "Medium")}</span>', unsafe_allow_html=True)
            st.markdown(f'<span class="tag status-{issue.get("status", "To Do").lower().replace(" ", "-")}">{issue.get("status", "To Do")}</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-subtitle">Type: {issue.get("issue_type", "Other")}</div>', unsafe_allow_html=True)
            assignee = "Unassigned"
            for member in team_members:
                if member.get('id') == issue.get('assignee'):
                    assignee = member.get('username', 'Unknown')
                    break
            st.markdown(f'<div class="card-subtitle">Assignee: {assignee}</div>', unsafe_allow_html=True)
            related_task_title = "None"
            for task in tasks:
                if task.get('id') == issue.get('related_task'):
                    related_task_title = task.get('title', 'Unnamed Task')
                    break
            st.markdown(f'<div class="card-subtitle">Related Task: {related_task_title}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-subtitle">Due: {issue.get("due_date", "No due date")}</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Edit", key=f"edit_issue_{issue['id']}"):
                    st.session_state.active_issue = issue['id']
                    st.session_state.show_create_issue = True
                    st.rerun()
            with col2:
                if st.button("Delete", key=f"delete_issue_{issue['id']}"):
                    if delete_issue(project_id, issue['id']):
                        st.success("Issue deleted!")
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Create or edit issue
    today = datetime.now().strftime('%Y-%m-%d')
    if st.session_state.show_create_issue and st.session_state.active_issue:
        issue = next((i for i in issues if i['id'] == st.session_state.active_issue), None)
        st.markdown("### Edit Issue")
    else:
        st.markdown("### Create New Issue")
        issue = None
    with st.form("issue_form"):
        title = st.text_input("Issue Title", value=issue.get('title', '') if issue else '')
        description = st.text_area("Description", value=issue.get('description', '') if issue else '')
        issue_type = st.selectbox("Issue Type", ISSUE_TYPES, index=ISSUE_TYPES.index(issue.get('issue_type', 'Other')) if issue else 0)
        priority = st.selectbox("Priority", PRIORITY_OPTIONS, index=PRIORITY_OPTIONS.index(issue.get('priority', 'Medium')) if issue else 1)
        status = st.selectbox("Status", STATUS_OPTIONS, index=STATUS_OPTIONS.index(issue.get('status', 'To Do')) if issue else 0)
        assignee_options = ["Unassigned"] + [m['username'] for m in team_members]
        assignee = st.selectbox("Assignee", assignee_options, 
                                index=([m['username'] for m in team_members].index(issue.get('assignee_username', 'Unassigned')) + 1) if issue and issue.get('assignee_username') in [m['username'] for m in team_members] else 0)
        task_options = ["None"] + [t['title'] for t in tasks]
        related_task = st.selectbox("Related Task", task_options, 
                                    index=task_options.index(next((t['title'] for t in tasks if t.get('id') == issue.get('related_task')), "None")) if issue else 0)
        due_date = st.date_input("Due Date", value=datetime.strptime(issue.get('due_date', today), '%Y-%m-%d') if issue and issue.get('due_date') else datetime.now())
        submit = st.form_submit_button("Save Issue")
        if submit:
            if not title:
                st.error("Issue title is required.")
            else:
                issue_data = {
                    "title": title,
                    "description": description,
                    "issue_type": issue_type,
                    "priority": priority,
                    "status": status,
                    "assignee": next((m['id'] for m in team_members if m['username'] == assignee), None) if assignee != "Unassigned" else None,
                    "assignee_username": assignee if assignee != "Unassigned" else None,
                    "related_task": next((t['id'] for t in tasks if t['title'] == related_task), None) if related_task != "None" else None,
                    "due_date": due_date.strftime('%Y-%m-%d')
                }
                if issue:
                    if update_issue(project_id, st.session_state.active_issue, issue_data):
                        st.success("Issue updated!")
                        st.session_state.show_create_issue = False
                        st.session_state.active_issue = None
                        st.rerun()
                    else:
                        st.error("Failed to update issue.")
                else:
                    if create_issue(project_id, issue_data):
                        st.success("Issue created!")
                        st.session_state.show_create_issue = False
                        st.rerun()
                    else:
                        st.error("Failed to create issue. Check Firebase configuration and permissions.")

def show_team(user_id, user_info):
    st.markdown('<h2 class="tab-subheader">Team</h2>', unsafe_allow_html=True)
    if not st.session_state.active_project:
        st.warning("Please select a project from the Projects tab.")
        return
    project_id = st.session_state.active_project
    team_members = get_team_members(project_id)
    members = db.child("project_members").child(project_id).get().val()
    user_role = members.get(user_id, "Member") if members else "Member"
    for member in team_members:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f'<div class="card-title">{member.get("name", "Unknown")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-subtitle">Email: {member.get("email", "No email")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-subtitle">Role: {member.get("role", "Member")}</div>', unsafe_allow_html=True)
            if user_role == "admin" and member['id'] != user_id:
                if st.button("Remove", key=f"remove_{member['id']}"):
                    if remove_project_member(project_id, member['id']):
                        st.success(f"Removed {member['name']} from project.")
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    if user_role == "admin":
        st.markdown("### Add Team Member")
        with st.form("add_member_form"):
            email = st.text_input("Member Email")
            role = st.selectbox("Role", ["member", "admin"])
            if st.form_submit_button("Add Member"):
                if add_project_member(project_id, email, role):
                    st.success(f"Added {email} to project.")
                    st.rerun()
                else:
                    st.error("Failed to add member. Ensure the email is registered.")

def show_reports(user_id, user_info):
    st.markdown('<h2 class="tab-subheader">Reports</h2>', unsafe_allow_html=True)
    if not st.session_state.active_project:
        st.warning("Please select a project from the Projects tab.")
        return
    project_id = st.session_state.active_project
    tasks = get_project_tasks(project_id)
    issues = get_project_issues(project_id)
    team_members = get_team_members(project_id)
    st.markdown("### Task and Issue Report (PDF)")
    if st.button("Generate Report"):
        report_path = generate_task_report_pdf(tasks, issues, user_info, team_members)
        with open(report_path, "rb") as f:
            st.download_button("Download Report", f, file_name=os.path.basename(report_path))
        os.remove(report_path)
    st.markdown("### EOD Report (Email)")
    recipient_email = st.text_input("Recipient Email", user_info.get('email', ''))
    if st.button("Send EOD Report"):
        html_report = generate_eod_report(tasks, issues, user_info, team_members)
        if send_email(recipient_email, f"EOD Report - {datetime.now().strftime('%Y-%m-%d')}", html_report):
            st.success("EOD Report sent successfully!")
        else:
            st.error("Failed to send EOD Report.")
    st.markdown("### Task Status Distribution")
    status_counts = {status: 0 for status in STATUS_OPTIONS}
    for task in tasks:
        status_counts[task.get('status', 'To Do')] += 1
    df_tasks = pd.DataFrame({
        "Status": list(status_counts.keys()),
        "Count": list(status_counts.values())
    })
    st.bar_chart(df_tasks.set_index("Status")["Count"])
    st.markdown("### Issue Status Distribution")
    issue_status_counts = {status: 0 for status in STATUS_OPTIONS}
    for issue in issues:
        issue_status_counts[issue.get('status', 'To Do')] += 1
    df_issues = pd.DataFrame({
        "Status": list(issue_status_counts.keys()),
        "Count": list(issue_status_counts.values())
    })
    st.bar_chart(df_issues.set_index("Status")["Count"])

def show_settings(user_id, user_info):
    st.markdown('<h2 class="tab-subheader">Settings</h2>', unsafe_allow_html=True)
    st.markdown("### Update Profile")
    with st.form("update_profile_form"):
        name = st.text_input("Name", value=user_info.get('name', ''))
        email = st.text_input("Email", value=user_info.get('email', ''), disabled=True)
        submit = st.form_submit_button("Update Profile")
        if submit:
            try:
                db.child("users").child(user_id).update({"name": name})
                st.session_state.user_info['name'] = name
                st.success("Profile updated!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update profile: {e}")

# Session state initialization
if "active_project" not in st.session_state:
    st.session_state.active_project = None
if "active_task" not in st.session_state:
    st.session_state.active_task = None
if "active_issue" not in st.session_state:
    st.session_state.active_issue = None
if "show_create_task" not in st.session_state:
    st.session_state.show_create_task = False
if "show_create_issue" not in st.session_state:
    st.session_state.show_create_issue = False
if "show_create_project" not in st.session_state:
    st.session_state.show_create_project = False
if "filter_status" not in st.session_state:
    st.session_state.filter_status = "All"
if "filter_priority" not in st.session_state:
    st.session_state.filter_priority = "All"
if "filter_assignee" not in st.session_state:
    st.session_state.filter_assignee = "All"
if "issue_filter_status" not in st.session_state:
    st.session_state.issue_filter_status = "All"
if "issue_filter_type" not in st.session_state:
    st.session_state.issue_filter_type = "All"
if "issue_filter_assignee" not in st.session_state:
    st.session_state.issue_filter_assignee = "All"
if "show_project_settings" not in st.session_state:
    st.session_state.show_project_settings = False
if "login_time" not in st.session_state:
    st.session_state.login_time = 0
if "debug_auth" not in st.session_state:
    st.session_state.debug_auth = ""

# Main app
def main():
    load_css()
    if not login():
        return
    user_id = st.session_state.user_id
    user_info = st.session_state.user_info
    st.markdown('<h1 class="main-header">Task Management System</h1>', unsafe_allow_html=True)
    with st.sidebar:
        st.markdown(f"""
        <div class="profile-container">
            <div class="profile-name">{user_info.get('name', 'User')}</div>
            <div class="profile-email">{user_info.get('email', '')}</div>
        </div>
        """, unsafe_allow_html=True)
        nav_selection = st.radio("Navigation", 
                                ["Dashboard", "Projects", "Tasks", "Issues", "Team", "Reports", "Settings"])
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.user_id = None
            st.session_state.user_info = None
            st.session_state.active_project = None
            st.session_state.login_time = 0
            st.session_state.debug_auth = "Logged out"
            st.rerun()
    try:
        if nav_selection == "Dashboard":
            show_dashboard(user_id, user_info)
        elif nav_selection == "Projects":
            show_projects(user_id, user_info)
        elif nav_selection == "Tasks":
            show_tasks(user_id, user_info)
        elif nav_selection == "Issues":
            show_issues(user_id, user_info)
        elif nav_selection == "Team":
            show_team(user_id, user_info)
        elif nav_selection == "Reports":
            show_reports(user_id, user_info)
        elif nav_selection == "Settings":
            show_settings(user_id, user_info)
    except Exception as e:
        st.error(f"Navigation error: {e}. Please ensure all navigation functions are properly configured.")
    st.markdown('<div class="footer">Task Management System © 2025</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
