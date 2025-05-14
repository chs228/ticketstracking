import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import datetime
import pandas as pd
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid
import re

# Initialize Firebase if not already initialized
if not firebase_admin._apps:
    # In a real app, store these credentials securely and use environment variables
    # For local testing, create a service account key file from Firebase console
    cred = {
        "type": "service_account",
        "project_id": "task-management-system-xxxxx",
        # Add other required fields for your Firebase service account
    }
    
    # Initialize Firebase with credentials
    try:
        cred_obj = credentials.Certificate(cred)
        firebase_admin.initialize_app(cred_obj)
    except:
        # For development purposes - this will help you initialize without actual credentials
        st.warning("Running in demo mode: Firebase not connected. For production, add valid credentials.")

# Page configuration
st.set_page_config(
    page_title="Task Management System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS to make the app beautiful
st.markdown("""
<style>
    /* Global font and styling */
    * {
        font-family: 'Roboto', sans-serif;
    }
    
    /* Header styling */
    .main-header {
        color: #3366ff;
        font-weight: bold;
        font-size: 2.5em;
        margin-bottom: 20px;
        text-align: center;
    }
    
    /* Subheader styling */
    .sub-header {
        color: #0047ab;
        font-weight: 500;
        font-size: 1.5em;
        margin-bottom: 15px;
    }
    
    /* Card styling */
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #3366ff;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 24px;
        font-weight: 500;
    }
    
    .stButton>button:hover {
        background-color: #254EDB;
    }
    
    /* Status colors */
    .status-todo {
        background-color: #FFE0E0;
        padding: 3px 10px;
        border-radius: 15px;
        font-weight: 500;
    }
    
    .status-in-progress {
        background-color: #FFF4CC;
        padding: 3px 10px;
        border-radius: 15px;
        font-weight: 500;
    }
    
    .status-done {
        background-color: #CCFFCC;
        padding: 3px 10px;
        border-radius: 15px;
        font-weight: 500;
    }
    
    /* Task list styling */
    .task-list {
        margin-top: 20px;
    }
    
    /* Form styling */
    .stTextInput>div>div>input, .stSelectbox>div>div>select {
        border-radius: 5px;
    }
    
    /* Adjust dataframe styling */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    .dataframe th {
        background-color: #3366ff;
        color: white;
    }
    
    .dataframe tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    
    /* Priority coloring */
    .priority-high {
        color: #ff4d4d;
        font-weight: bold;
    }
    
    .priority-medium {
        color: #ff9933;
        font-weight: bold;
    }
    
    .priority-low {
        color: #33cc33;
        font-weight: bold;
    }
    
    /* Dashboard metrics */
    .metric-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 20px;
    }
    
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        width: 23%;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .metric-title {
        font-size: 0.9em;
        color: #666;
    }
    
    .metric-value {
        font-size: 1.8em;
        font-weight: bold;
        color: #3366ff;
    }
</style>
""", unsafe_allow_html=True)

# Create a demo database if not connected to Firebase
class DemoDatabase:
    def __init__(self):
        self.tasks = {}
        self.users = {
            "demo_user@example.com": {
                "password": "password123",
                "username": "demo_user",
                "user_id": "demo_uid_12345"
            }
        }
        # Add some sample tasks
        sample_tasks = [
            {
                "task_id": str(uuid.uuid4()),
                "title": "Create website mockup",
                "description": "Design initial website mockups for client review",
                "status": "In Progress",
                "priority": "High",
                "assignee": "demo_user",
                "due_date": (datetime.datetime.now() + datetime.timedelta(days=3)).strftime("%Y-%m-%d"),
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d"),
                "created_by": "demo_user"
            },
            {
                "task_id": str(uuid.uuid4()),
                "title": "Fix login bug",
                "description": "Users are experiencing issues with the login system",
                "status": "To Do",
                "priority": "Medium",
                "assignee": "demo_user",
                "due_date": (datetime.datetime.now() + datetime.timedelta(days=5)).strftime("%Y-%m-%d"),
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d"),
                "created_by": "demo_user"
            },
            {
                "task_id": str(uuid.uuid4()),
                "title": "Update documentation",
                "description": "Update API documentation with new endpoints",
                "status": "Done",
                "priority": "Low",
                "assignee": "demo_user",
                "due_date": (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d"),
                "created_by": "demo_user"
            }
        ]
        
        for task in sample_tasks:
            self.tasks[task["task_id"]] = task
    
    def collection(self, name):
        return self
    
    def document(self, doc_id):
        return self
    
    def get(self):
        class MockDocSnapshot:
            def __init__(self, data, id):
                self.data_dict = data
                self.id = id
                
            def to_dict(self):
                return self.data_dict
                
            def id(self):
                return self.id
        
        class MockQuerySnapshot:
            def __init__(self, docs):
                self.docs = docs
                
        doc_snapshots = []
        for task_id, task_data in self.tasks.items():
            doc_snapshots.append(MockDocSnapshot(task_data, task_id))
            
        return MockQuerySnapshot(doc_snapshots)
    
    def set(self, data):
        if "task_id" in data:
            self.tasks[data["task_id"]] = data
        return True
    
    def add(self, data):
        task_id = str(uuid.uuid4())
        data["task_id"] = task_id
        self.tasks[task_id] = data
        return task_id
    
    def update(self, data):
        task_id = data.get("task_id")
        if task_id in self.tasks:
            self.tasks[task_id].update(data)
        return True
    
    def delete(self):
        # This would delete the document but we're not implementing it fully for the demo
        return True
    
    def where(self, field, op, value):
        # Basic filtering
        filtered_db = DemoDatabase()
        filtered_db.tasks = {}
        
        for task_id, task in self.tasks.items():
            if field in task:
                if op == "==" and task[field] == value:
                    filtered_db.tasks[task_id] = task
                elif op == ">" and task[field] > value:
                    filtered_db.tasks[task_id] = task
                elif op == "<" and task[field] < value:
                    filtered_db.tasks[task_id] = task
        
        return filtered_db

demo_db = DemoDatabase()

def get_db():
    """Get database instance (either Firebase or demo)"""
    if firebase_admin._apps:
        return firestore.client()
    else:
        return demo_db

def authenticate_user(email, password):
    """Authenticate user with Firebase or demo DB"""
    try:
        if firebase_admin._apps:
            # Use Firebase Authentication
            user = auth.get_user_by_email(email)
            # In a real app, you'd verify the password with Firebase
            # Here we're assuming success for simplicity
            username = email.split('@')[0]
            return True, username, user.uid
        else:
            # Use demo authentication
            if email in demo_db.users and demo_db.users[email]["password"] == password:
                return True, demo_db.users[email]["username"], demo_db.users[email]["user_id"]
            return False, None, None
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return False, None, None

def create_user(email, password):
    """Create a new user with Firebase or demo DB"""
    try:
        if firebase_admin._apps:
            # Create user in Firebase Authentication
            user = auth.create_user(
                email=email,
                password=password
            )
            username = email.split('@')[0]
            return True, username, user.uid
        else:
            # Create user in demo DB
            if email in demo_db.users:
                return False, None, None
            username = email.split('@')[0]
            user_id = f"user_{len(demo_db.users) + 1}"
            demo_db.users[email] = {
                "password": password,
                "username": username,
                "user_id": user_id
            }
            return True, username, user_id
    except Exception as e:
        st.error(f"User creation error: {e}")
        return False, None, None

def login_page():
    """Display the login page"""
    st.markdown('<h1 class="main-header">Task Management System</h1>', unsafe_allow_html=True)
    
    # Create two columns for login and signup
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h2 class="sub-header">Login</h2>', unsafe_allow_html=True)
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        login_button = st.button("Login")
        
        if login_button:
            if login_email and login_password:
                success, username, user_id = authenticate_user(login_email, login_password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_id = user_id
                    st.session_state.email = login_email
                    st.experimental_rerun()
                else:
                    st.error("Invalid email or password")
            else:
                st.error("Please enter both email and password")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h2 class="sub-header">Sign Up</h2>', unsafe_allow_html=True)
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Password", type="password", key="signup_password")
        signup_confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
        signup_button = st.button("Sign Up")
        
        if signup_button:
            if signup_email and signup_password and signup_confirm_password:
                if not re.match(r"[^@]+@[^@]+\.[^@]+", signup_email):
                    st.error("Please enter a valid email address")
                elif signup_password != signup_confirm_password:
                    st.error("Passwords do not match")
                elif len(signup_password) < 6:
                    st.error("Password must be at least 6 characters long")
                else:
                    success, username, user_id = create_user(signup_email, signup_password)
                    if success:
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error("Email already exists or there was an error creating the account")
            else:
                st.error("Please fill in all fields")
        st.markdown('</div>', unsafe_allow_html=True)

def add_task_form():
    """Form for adding a new task"""
    st.markdown('<h2 class="sub-header">Create New Task</h2>', unsafe_allow_html=True)
    
    with st.form("add_task_form", clear_on_submit=True):
        title = st.text_input("Task Title", placeholder="Enter task title")
        description = st.text_area("Description", placeholder="Describe the task in detail")
        
        col1, col2 = st.columns(2)
        with col1:
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        
        with col2:
            assignee = st.text_input("Assignee", value=st.session_state.username, 
                                     help="Enter the username of the person assigned to this task")
            due_date = st.date_input("Due Date", 
                                   value=datetime.datetime.now() + datetime.timedelta(days=7))
        
        submitted = st.form_submit_button("Add Task")
        
        if submitted:
            if title:
                db = get_db()
                new_task = {
                    "title": title,
                    "description": description,
                    "status": status,
                    "priority": priority,
                    "assignee": assignee,
                    "due_date": due_date.strftime("%Y-%m-%d"),
                    "created_at": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "created_by": st.session_state.username
                }
                
                # Add the task to the database
                db.collection("tasks").add(new_task)
                st.success("Task added successfully!")
                return True
            else:
                st.error("Task title is required!")
                return False
        return False

def fetch_tasks():
    """Fetch all tasks from the database"""
    db = get_db()
    tasks_ref = db.collection("tasks").get()
    
    tasks = []
    for task in tasks_ref.docs:
        task_data = task.to_dict()
        task_data["task_id"] = task.id
        tasks.append(task_data)
    
    return tasks

def format_task_table(tasks):
    """Format tasks for display in a table"""
    if not tasks:
        return pd.DataFrame()
    
    # Convert tasks to DataFrame
    df = pd.DataFrame(tasks)
    
    # Select and rename columns for display
    display_columns = [
        "title", "status", "priority", "assignee", "due_date", "created_at"
    ]
    
    column_names = {
        "title": "Task Title",
        "status": "Status",
        "priority": "Priority",
        "assignee": "Assigned To",
        "due_date": "Due Date",
        "created_at": "Created On"
    }
    
    # Make sure all columns exist
    for col in display_columns:
        if col not in df.columns:
            df[col] = ""
    
    # Create the display dataframe
    display_df = df[display_columns].rename(columns=column_names)
    
    return display_df

def task_details(task_id):
    """Display and edit task details"""
    db = get_db()
    
    # Fetch the task
    task_ref = db.collection("tasks").document(task_id)
    task_data = task_ref.get().to_dict()
    
    if not task_data:
        st.error("Task not found!")
        return
    
    st.markdown(f'<h2 class="sub-header">Task Details</h2>', unsafe_allow_html=True)
    
    with st.form("edit_task_form"):
        title = st.text_input("Task Title", value=task_data.get("title", ""))
        description = st.text_area("Description", value=task_data.get("description", ""))
        
        col1, col2 = st.columns(2)
        with col1:
            status = st.selectbox("Status", 
                                ["To Do", "In Progress", "Done"], 
                                index=["To Do", "In Progress", "Done"].index(task_data.get("status", "To Do")))
            priority = st.selectbox("Priority", 
                                 ["Low", "Medium", "High"],
                                 index=["Low", "Medium", "High"].index(task_data.get("priority", "Medium")))
        
        with col2:
            assignee = st.text_input("Assignee", value=task_data.get("assignee", st.session_state.username))
            due_date = st.date_input("Due Date", 
                                  value=datetime.datetime.strptime(task_data.get("due_date", datetime.datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d"))
        
        col1, col2 = st.columns(2)
        with col1:
            update_button = st.form_submit_button("Update Task")
        with col2:
            delete_button = st.form_submit_button("Delete Task", type="secondary")
        
        if update_button:
            updated_task = {
                "title": title,
                "description": description,
                "status": status,
                "priority": priority,
                "assignee": assignee,
                "due_date": due_date.strftime("%Y-%m-%d"),
                "last_updated": datetime.datetime.now().strftime("%Y-%m-%d")
            }
            
            # Update the task in the database
            task_ref.update(updated_task)
            st.success("Task updated successfully!")
            st.session_state.selected_task = None
            st.experimental_rerun()
        
        if delete_button:
            task_ref.delete()
            st.success("Task deleted successfully!")
            st.session_state.selected_task = None
            st.experimental_rerun()

def generate_eod_report():
    """Generate an End of Day report"""
    tasks = fetch_tasks()
    
    # Filter tasks for the current user
    user_tasks = [task for task in tasks if task.get("assignee") == st.session_state.username]
    
    # Group tasks by status
    tasks_by_status = {
        "To Do": [task for task in user_tasks if task.get("status") == "To Do"],
        "In Progress": [task for task in user_tasks if task.get("status") == "In Progress"],
        "Done": [task for task in user_tasks if task.get("status") == "Done"]
    }
    
    # Create the report
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    report = f"""
# End of Day Report - {today}
## User: {st.session_state.username}

### Summary
- Total tasks: {len(user_tasks)}
- To Do: {len(tasks_by_status['To Do'])}
- In Progress: {len(tasks_by_status['In Progress'])}
- Done: {len(tasks_by_status['Done'])}

### Tasks Done Today
"""
    
    if tasks_by_status["Done"]:
        for task in tasks_by_status["Done"]:
            report += f"- {task.get('title')}\n"
    else:
        report += "- No tasks completed today\n"
    
    report += "\n### Tasks In Progress\n"
    
    if tasks_by_status["In Progress"]:
        for task in tasks_by_status["In Progress"]:
            report += f"- {task.get('title')} (Due: {task.get('due_date')})\n"
    else:
        report += "- No tasks in progress\n"
    
    report += "\n### Upcoming Tasks\n"
    
    if tasks_by_status["To Do"]:
        for task in tasks_by_status["To Do"]:
            report += f"- {task.get('title')} (Due: {task.get('due_date')})\n"
    else:
        report += "- No upcoming tasks\n"
    
    return report

def send_email(to_email, subject, body):
    """Send email with the EOD report (for demo purposes)"""
    if firebase_admin._apps:
        # In a real app, you would use an email service
        st.info("In a production app, this would send an email using a service like SendGrid or SMTP")
        st.code(f"""
To: {to_email}
Subject: {subject}
        
{body}
        """)
        return True
    else:
        # Show demo email
        st.info("Demo Mode: Email would be sent with the following content")
        st.markdown(body)
        return True

def dashboard():
    """Display the main dashboard with task management features"""
    # Display header with logout option
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f'<h1 class="main-header">Task Management Dashboard</h1>', unsafe_allow_html=True)
    with col2:
        st.write(f"Logged in as: **{st.session_state.username}**")
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Tasks", "Create Task", "EOD Report"])
    
    with tab1:
        # Dashboard overview
        st.markdown('<h2 class="sub-header">Project Overview</h2>', unsafe_allow_html=True)
        
        # Fetch tasks for metrics
        tasks = fetch_tasks()
        
        # Calculate metrics
        total_tasks = len(tasks)
        tasks_todo = len([task for task in tasks if task.get("status") == "To Do"])
        tasks_in_progress = len([task for task in tasks if task.get("status") == "In Progress"])
        tasks_done = len([task for task in tasks if task.get("status") == "Done"])
        
        # Display metrics in a nice layout
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        
        # Total Tasks
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Tasks</div>
            <div class="metric-value">{total_tasks}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # To Do
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">To Do</div>
            <div class="metric-value">{tasks_todo}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # In Progress
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">In Progress</div>
            <div class="metric-value">{tasks_in_progress}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Done
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Done</div>
            <div class="metric-value">{tasks_done}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Recent tasks section
        st.markdown('<h3 class="sub-header">Recent Tasks</h3>', unsafe_allow_html=True)
        
        if tasks:
            # Sort tasks by creation date (most recent first)
            sorted_tasks = sorted(tasks, key=lambda x: x.get("created_at", ""), reverse=True)
            recent_tasks = sorted_tasks[:5]  # Get the 5 most recent tasks
            
            for task in recent_tasks:
                with st.container():
                    st.markdown(f"""
                    <div class="card">
                        <h4>{task.get('title')}</h4>
                        <p>{task.get('description', '')[:100]}{'...' if len(task.get('description', '')) > 100 else ''}</p>
                        <p>
                            <span class="status-{task.get('status', '').lower().replace(' ', '-')}">
                                {task.get('status', '')}
                            </span>
                            &nbsp;•&nbsp;
                            <span class="priority-{task.get('priority', '').lower()}">
                                {task.get('priority', '')} Priority
                            </span>
                            &nbsp;•&nbsp;
                            Due: {task.get('due_date', '')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No tasks found. Create some tasks to see them here!")
    
    with tab2:
        # Task list and management
        st.markdown('<h2 class="sub-header">Task List</h2>', unsafe_allow_html=True)
        
        # Add filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "To Do", "In Progress", "Done"])
        with col2:
            priority_filter = st.selectbox("Filter by Priority", ["All", "Low", "Medium", "High"])
        with col3:
            assignee_filter = st.text_input("Filter by Assignee", value="")
        
        # Fetch and display tasks
        tasks = fetch_tasks()
        
        # Apply filters
        if status_filter != "All":
            tasks = [task for task in tasks if task.get("status") == status_filter]
        
        if priority_filter != "All":
            tasks = [task for task in tasks if task.get("priority") == priority_filter]
        
        if assignee_filter:
            tasks = [task for task in tasks if assignee_filter.lower() in task.get("assignee", "").lower()]
        
        # Display tasks in a table
        if tasks:
            task_df = format_task_table(tasks)
            st.dataframe(task_df, use_container_width=True)
            
            # Add a way to select tasks for detailed view
            task_titles = [task.get("title") for task in tasks]
            task_ids = [task.get("task_id") for task in tasks]
            
            selected_task_title = st.selectbox("Select a task to view/edit details", 
                                             ["Select a task..."] + task_titles)
            
            if selected_task_title != "Select a task...":
                selected_index = task_titles.index(selected_task_title)
                selected_task_id = task_ids[selected_index]
                st.session_state.selected_task = selected_task_id
                task_details(selected_task_id)
        else:
            st.info("No tasks found with the current filters.")
    
    with tab3:
        # Create new task form
        task_added = add_task_form()
        if task_added:
            # Clear form after successful submission
            st.experimental_rerun()
    
    with tab4:
        # EOD Report generation
        st.markdown('<h2 class="sub-header">End of Day Report</h2>', unsafe_allow_html=True)
        
        # Generate the report
        eod_report = generate_eod_report()
        
        # Display preview of the report
        st.markdown(eod_report)
        
        # Add email option
        st.markdown('<h3 class="sub-header">Send Report by Email</h3>', unsafe_allow_html=True)
        
        recipient_email = st.text_input("Recipient Email", value=st.session_state.email)
        subject = st.text_input("Email Subject", value=f"EOD Report - {datetime.datetime.now().strftime('%Y-%m-%d')}")
        
        if st.button("Send EOD Report"):
            success = send_email(recipient_email, subject, eod_report)
            if success:
                st.success("EOD report sent successfully!")

def main():
    # Initialize session state variables if they don't exist
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if "selected_task" not in st.session_state:
        st.session_state.selected_task = None
    
    # Display the appropriate page based on login status
    if not st.session_state.logged_in:
        login_page()
    else:
        dashboard()

if __name__ == "__main__":
    main()
