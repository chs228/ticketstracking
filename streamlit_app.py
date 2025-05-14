import streamlit as st
import pandas as pd
import re
import io
import base64
import os
import random
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import pyrebase
import uuid
import json
from fpdf import FPDF
import plotly.express as px
import plotly.graph_objects as go

# Firebase configuration
firebase_config = {
  apiKey: "AIzaSyBTsa0pgK0R6aDOxPe_c_MBdKR4XaHPGGA",
  authDomain: "tracking-c62bb.firebaseapp.com",
  databaseURL: "https://tracking-c62bb-default-rtdb.firebaseio.com",
  projectId: "tracking-c62bb",
  storageBucket: "tracking-c62bb.firebasestorage.app",
  messagingSenderId: "977902624059",
  appId: "1:977902624059:web:165e120df5463bde332b1e",
  measurementId: "G-PNHDJF45Z6"
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

# Task priority and status options
PRIORITY_OPTIONS = ["Low", "Medium", "High", "Critical"]
STATUS_OPTIONS = ["To Do", "In Progress", "On Hold", "Done"]
ISSUE_TYPES = ["Bug", "Feature", "Enhancement", "Documentation", "Other"]

# Colors for different priorities and statuses
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
        
        .priority-low {
            background-color: #28a745;
        }
        
        .priority-medium {
            background-color: #ffc107;
            color: #212529;
        }
        
        .priority-high {
            background-color: #fd7e14;
        }
        
        .priority-critical {
            background-color: #dc3545;
        }
        
        .status-todo {
            background-color: #6c757d;
        }
        
        .status-progress {
            background-color: #007bff;
        }
        
        .status-hold {
            background-color: #6f42c1;
        }
        
        .status-done {
            background-color: #28a745;
        }
        
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
        
        .profile-stats {
            display: flex;
            justify-content: space-around;
            margin-top: 1rem;
        }
        
        .profile-stat {
            text-align: center;
        }
        
        .profile-stat-value {
            font-size: 1.5rem;
            font-weight: 600;
            color: #3366ff;
        }
        
        .profile-stat-label {
            font-size: 0.8rem;
            color: #6c757d;
        }
        
        /* Animation for loader */
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

# Function to send email
def send_email(recipient_email, subject, body, attachment_path=None):
    """Send email with optional attachment"""
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

# Export functions
def generate_task_report_pdf(tasks, user_info, team_members):
    """Generate a PDF report of tasks"""
    pdf = FPDF()
    pdf.add_page()
    
    # Set font
    pdf.set_font("Arial", "B", 16)
    
    # Title
    pdf.cell(0, 10, "Task Management Report", ln=True, align="C")
    pdf.ln(5)
    
    # Date
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(0, 10, f"Generated by: {user_info.get('name', 'Unknown')}", ln=True)
    pdf.ln(10)
    
    # Summary
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Task Summary", ln=True)
    pdf.set_font("Arial", "", 12)
    
    # Count tasks by status
    status_counts = {status: 0 for status in STATUS_OPTIONS}
    for task in tasks:
        status = task.get('status', 'To Do')
        status_counts[status] += 1
    
    for status, count in status_counts.items():
        pdf.cell(0, 10, f"{status}: {count} tasks", ln=True)
    
    pdf.ln(5)
    
    # Tasks details
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Task Details", ln=True)
    
    # Headers
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, "Task Name", border=1)
    pdf.cell(30, 10, "Priority", border=1)
    pdf.cell(30, 10, "Status", border=1)
    pdf.cell(40, 10, "Assignee", border=1)
    pdf.cell(30, 10, "Due Date", border=1, ln=True)
    
    # Data rows
    pdf.set_font("Arial", "", 12)
    for task in tasks:
        assignee_username = "Unassigned"
        for member in team_members:
            if member.get('id') == task.get('assignee'):
                assignee_username = member.get('username', 'Unknown')
                break
        
        # Ensure text fits in cells
        task_name = task.get('title', 'Unnamed Task')
        if len(task_name) > 20:
            task_name = task_name[:17] + "..."
        
        pdf.cell(60, 10, task_name, border=1)
        pdf.cell(30, 10, task.get('priority', 'Medium'), border=1)
        pdf.cell(30, 10, task.get('status', 'To Do'), border=1)
        pdf.cell(40, 10, assignee_username, border=1)
        due_date = task.get('due_date', '')
        pdf.cell(30, 10, due_date, border=1, ln=True)
    
    # Save PDF
    report_path = f"task_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(report_path)
    return report_path

def generate_eod_report(tasks, user_info, team_members):
    """Generate an HTML EOD report"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Filter tasks updated today
    updated_today = [task for task in tasks if task.get('last_updated', '').startswith(today)]
    
    # Count tasks by status
    status_counts = {status: 0 for status in STATUS_OPTIONS}
    for task in tasks:
        status = task.get('status', 'To Do')
        status_counts[status] += 1
    
    # Get tasks due soon
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    due_soon = [task for task in tasks if task.get('due_date', '') in (today, tomorrow) and task.get('status', '') != 'Done']
    
    # Start building HTML
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
            
            <h2>Project Status Summary</h2>
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
    """
    
    # Today's updates
    if updated_today:
        html += """
            <h2>Today's Updates</h2>
            <table>
                <tr>
                    <th>Task</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Assignee</th>
                </tr>
        """
        
        for task in updated_today:
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
                    <td>{assignee_username}</td>
                </tr>
            """
        
        html += "</table>"
    else:
        html += "<h2>Today's Updates</h2><p>No tasks were updated today.</p>"
    
    # Due soon
    if due_soon:
        html += """
            <h2>Tasks Due Soon</h2>
            <table>
                <tr>
                    <th>Task</th>
                    <th>Due Date</th>
                    <th>Priority</th>
                    <th>Assignee</th>
                </tr>
        """
        
        for task in due_soon:
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
                    <td>{assignee_username}</td>
                </tr>
            """
        
        html += "</table>"
    else:
        html += "<h2>Tasks Due Soon</h2><p>No tasks are due soon.</p>"
    
    # Close HTML
    html += """
            <div class="footer">
                <p>This is an automated report from the Task Management System.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

# User management functions
def extract_username_from_email(email):
    """Extract username from email address (before @)"""
    if email and '@' in email:
        return email.split('@')[0]
    return "user"

def get_user_info(user_id):
    """Get user info from database"""
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
    """Get all team members for a project"""
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
    """Get projects where user is a member"""
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
    """Get all tasks for a project"""
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
        
        # Sort tasks by priority and due date
        task_list.sort(key=lambda x: (
            PRIORITY_OPTIONS.index(x.get("priority", "Medium")),
            x.get("due_date", "9999-12-31")
        ))
        
        return task_list
    except Exception as e:
        st.error(f"Error getting project tasks: {e}")
        return []

# Firebase login
def login():
    """Handle user login and authentication"""
    if "user" not in st.session_state or not st.session_state.user:
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
                            st.session_state.user = user
                            st.session_state.user_id = user['localId']
                            
                            # Get user info or create if new
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
                            st.success("Logged in successfully!")
                            st.rerun()
                        except Exception as e:
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
                                st.session_state.user = user
                                st.session_state.user_id = user['localId']
                                
                                # Create user in database
                                username = extract_username_from_email(email)
                                user_info = {
                                    "name": username.capitalize(),
                                    "email": email,
                                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                db.child("users").child(user['localId']).set(user_info)
                                st.session_state.user_info = user_info
                                
                                st.success("Account created and logged in!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Sign up failed: {e}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Footer
            st.markdown('<div class="footer">Task Management System © 2025</div>', unsafe_allow_html=True)
        
        return False
    return True

# Task management functions
def create_task(project_id, task_data):
    """Create a new task in the database"""
    if not db:
        return False
    
    try:
        task_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task_id = db.child("tasks").child(project_id).push(task_data)
        return True
    except Exception as e:
        st.error(f"Error creating task: {e}")
        return False

def update_task(project_id, task_id, task_data):
    """Update an existing task"""
    if not db:
        return False
    
    try:
        task_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.child("tasks").child(project_id).child(task_id).update(task_data)
        return True
    except Exception as e:
        st.error(f"Error updating task: {e}")
        return False

def delete_task(project_id, task_id):
    """Delete a task"""
    if not db:
        return False
    
    try:
        db.child("tasks").child(project_id).child(task_id).remove()
        return True
    except Exception as e:
        st.error(f"Error deleting task: {e}")
        return False

def create_project(project_data, user_id):
    """Create a new project and add creator as admin"""
    if not db:
        return None
    
    try:
        project_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        project_data["created_by"] = user_id
        
        project_id = db.child("projects").push(project_data)
        
        # Add creator as admin
        db.child("project_members").child(project_id["name"]).child(user_id).set("admin")
        
        return project_id["name"]
    except Exception as e:
        st.error(f"Error creating project: {e}")
        return None

def add_project_member(project_id, email, role="member"):
    """Add a team member to a project by email"""
    if not db:
        return False
    
    try:
        # Find user by email
        users = db.child("users").get().val()
        if not users:
            return False
        
        user_id = None
        for uid, user_data in users.items():
            if user_data.get("email") == email:
                user_id = uid
                break
        
        if not user_id:
            return False
        
        # Add user to project
        db.child("project_members").child(project_id).child(user_id).set(role)
        return True
    except Exception as e:
        st.error(f"Error adding project member: {e}")
        return False

def remove_project_member(project_id, user_id):
    """Remove a team member from a project"""
    if not db:
        return False
    
    try:
        db.child("project_members").child(project_id).child(user_id).remove()
        return True
    except Exception as e:
        st.error(f"Error removing project member: {e}")
        return False

# Session state initialization
if "active_project" not in st.session_state:
    st.session_state.active_project = None
if "active_task" not in st.session_state:
    st.session_state.active_task = None
if "show_create_task" not in st.session_state:
    st.session_state.show_create_task = False
if "show_create_project" not in st.session_state:
    st.session_state.show_create_project = False
if "filter_status" not in st.session_state:
    st.session_state.filter_status = "All"
if "filter_priority" not in st.session_state:
    st.session_state.filter_priority = "All"
if "filter_assignee" not in st.session_state:
    st.session_state.filter_assignee = "All"

# Main app
# Main app
def main():
    load_css()
    
    if not login():
        return
    
    # Get user information
    user_id = st.session_state.user_id
    user_info = st.session_state.user_info
    
    # App header
    st.markdown('<h1 class="main-header">Task Management System</h1>', unsafe_allow_html=True)
    
    # Sidebar for navigation
    with st.sidebar:
        st.markdown(f"""
        <div class="profile-container">
            <div class="profile-name">{user_info.get('name', 'User')}</div>
            <div class="profile-email">{user_info.get('email', '')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        nav_selection = st.radio("Navigation", 
                                ["Dashboard", "Projects", "Tasks", "Team", "Reports", "Settings"])
        
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.user_id = None
            st.session_state.user_info = None
            st.session_state.active_project = None
            st.rerun()
    
    # Navigation handling
    if nav_selection == "Dashboard":
        show_dashboard(user_id, user_info)
    elif nav_selection == "Projects":
        show_projects(user_id, user_info)
    elif nav_selection == "Tasks":
        show_tasks(user_id, user_info)
    elif nav_selection == "Team":
        show_team(user_id, user_info)
    elif nav_selection == "Reports":
        show_reports(user_id, user_info)
    elif nav_selection == "Settings":
        show_settings(user_id, user_info)
    
    # Footer
    st.markdown('<div class="footer">Task Management System © 2025</div>', unsafe_allow_html=True)

# Run the app
if __name__ == "__main__":
    main()
