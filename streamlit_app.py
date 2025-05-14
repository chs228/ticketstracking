import streamlit as st
import pyrebase
import pandas as pd
from datetime import datetime
import os

# Firebase Configuration (Use environment variables on Streamlit Cloud)
firebaseConfig = {
  apiKey: "AIzaSyBTsa0pgK0R6aDOxPe_c_MBdKR4XaHPGGA",
  authDomain: "tracking-c62bb.firebaseapp.com",
  databaseURL: "https://tracking-c62bb-default-rtdb.firebaseio.com",
  projectId: "tracking-c62bb",
  storageBucket: "tracking-c62bb.firebasestorage.app",
  messagingSenderId: "977902624059",
  appId: "1:977902624059:web:165e120df5463bde332b1e",
  measurementId: "G-PNHDJF45Z6"}

# Initialize Firebase
try:
    firebase = pyrebase.initialize_app(firebaseConfig)
    auth = firebase.auth()
    db = firebase.database()
except Exception as e:
    st.error(f"Failed to initialize Firebase: {str(e)}")
    st.stop()

# Streamlit App
def main():
    st.set_page_config(page_title="Task & Issue Management System", layout="wide")

    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'project_id' not in st.session_state:
        st.session_state.project_id = None

    # Authentication
    if not st.session_state.user:
        st.title("Task & Issue Management System")
        auth_option = st.radio("Choose an option", ["Sign In", "Sign Up"])
        
        if auth_option == "Sign Up":
            st.subheader("Create Account")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            username = st.text_input("Username")
            if st.button("Sign Up"):
                try:
                    users = db.child("users").get().val()
                    if users and any(user_data.get('username') == username for user_data in users.values()):
                        st.error("Username already taken. Please choose another.")
                    else:
                        user = auth.create_user_with_email_and_password(email, password)
                        db.child("users").child(user['localId']).set({
                            "email": email,
                            "username": username
                        }, user['idToken'])
                        st.session_state.user = user
                        st.session_state.username = username
                        st.rerun()
                except Exception as e:
                    st.error(f"Sign-up failed: {str(e)}")
        
        else:
            st.subheader("Sign In")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.button("Sign In"):
                try:
                    user = auth.sign_in_with_email_and_password(email, password)
                    username = db.child("users").child(user['localId']).child("username").get(user['idToken']).val()
                    if username:
                        st.session_state.user = user
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("User not found. Please sign up.")
                except Exception as e:
                    st.error(f"Sign-in failed: {str(e)}")
        return

    # Main App
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    if st.sidebar.button("Sign Out"):
        try:
            st.session_state.user = None
            st.session_state.username = None
            st.session_state.project_id = None
            st.rerun()
        except Exception as e:
            st.error(f"Sign-out failed: {str(e)}")

    section = st.sidebar.radio("Menu", ["Projects", "Tasks", "Issues", "Tickets", "EOD Report"])

    if section == "Projects":
        st.title("Projects")
        project_name = st.text_input("Project Name")
        if st.button("Create Project"):
            if project_name:
                try:
                    project_ref = db.child("projects").push({
                        "name": project_name,
                        "created_by": st.session_state.user['email'],
                        "created_at": datetime.now().isoformat()
                    }, st.session_state.user['idToken'])
                    st.success("Project created successfully!")
                except Exception as e:
                    st.error(f"Error creating project: {str(e)}")
            else:
                st.error("Project name cannot be empty.")

        try:
            projects = db.child("projects").get(st.session_state.user['idToken']).val()
            project_options = {data['name']: key for key, data in projects.items()} if projects else {}
            selected_project = st.selectbox("Select Project", [""] + list(project_options.keys()))
            st.session_state.project_id = project_options.get(selected_project)
        except Exception as e:
            st.error(f"Error loading projects: {str(e)}")
            project_options = {}

    elif section in ["Tasks", "Issues", "Tickets"]:
        table = section.lower()
        st.title(section)
        if not st.session_state.project_id:
            st.warning("Please select a project from the Projects section.")
            return

        st.subheader(f"Create New {section[:-1]}")
        with st.form(f"{table}_form"):
            title = st.text_input("Title", key=f"{table}_title")
            description = st.text_area("Description", key=f"{table}_description")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"] if table == "tasks" else ["Open", "In Progress", "Resolved"], key=f"{table}_status")
            try:
                users = db.child("users").get(st.session_state.user['idToken']).val()
                user_emails = [data['email'] for data in users.values()] if users else []
            except Exception as e:
                st.error(f"Error loading users: {str(e)}")
                user_emails = []
            assignee = st.selectbox("Assignee", [""] + user_emails, key=f"{table}_assignee")
            submitted = st.form_submit_button("Add")
            if submitted and title:
                try:
                    db.child(table).push({
                        "project_id": st.session_state.project_id,
                        "title": title,
                        "description": description,
                        "status": status.lower(),
                        "assignee": assignee,
                        "created_by": st.session_state.user['email'],
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }, st.session_state.user['idToken'])
                    st.success(f"{section[:-1]} created successfully!")
                except Exception as e:
                    st.error(f"Error creating {section[:-1].lower()}: {str(e)}")
            elif submitted:
                st.error("Title is required.")

        st.subheader(f"{section} List")
        try:
            items = db.child(table).get(st.session_state.user['idToken']).val()
            item_list = [
                (key, data) for key, data in items.items()
                if data.get('project_id') == st.session_state.project_id
            ] if items else []
        except Exception as e:
            st.error(f"Error loading {table}: {str(e)}")
            item_list = []

        if not item_list:
            st.write(f"No {table} found.")
        else:
            df = pd.DataFrame(
                [(key, data['title'], data.get('description', ''), data['status'], data.get('assignee', ''), data['created_by'], data['created_at'], data['updated_at']) for key, data in item_list],
                columns=['ID', 'Title', 'Description', 'Status', 'Assignee', 'Created By', 'Created At', 'Updated At']
            )
            for idx, row in df.iterrows():
                with st.expander(f"{row['Title']} (Status: {row['Status']})"):
                    st.write(f"Description: {row['Description'] or 'No description'}")
                    st.write(f"Assignee: {row['Assignee'] or 'Unassigned'}")
                    st.write(f"Created By: {row['Created By']}")
                    st.write(f"Created At: {row['Created At']}")
                    st.write(f"Updated At: {row['Updated At']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Edit", key=f"edit_{table}_{row['ID']}"):
                            st.session_state[f"edit_{table}_{row['ID']}"] = True
                    with col2:
                        if st.button("Delete", key=f"delete_{table}_{row['ID']}"):
                            try:
                                db.child(table).child(row['ID']).remove(st.session_state.user['idToken'])
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting {section[:-1].lower()}: {str(e)}")

                    if st.session_state.get(f"edit_{table}_{row['ID']}"):
                        with st.form(f"edit_{table}_{row['ID']}_form"):
                            new_title = st.text_input("Title", value=row['Title'], key=f"edit_{table}_{row['ID']}_title")
                            new_description = st.text_area("Description", value=row['Description'] or '', key=f"edit_{table}_{row['ID']}_description")
                            new_status = st.selectbox(
                                "Status",
                                ["To Do", "In Progress", "Done"] if table == "tasks" else ["Open", "In Progress", "Resolved"],
                                index=["To Do", "In Progress", "Done"].index(row['Status'].title()) if table == "tasks" and row['Status'].title() in ["To Do", "In Progress", "Done"] else ["Open", "In Progress", "Resolved"].index(row['Status'].title()),
                                key=f"edit_{table}_{row['ID']}_status"
                            )
                            new_assignee = st.selectbox(
                                "Assignee",
                                [""] + user_emails,
                                index=user_emails.index(row['Assignee']) if row['Assignee'] in user_emails else 0,
                                key=f"edit_{table}_{row['ID']}_assignee"
                            )
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("Save"):
                                    try:
                                        db.child(table).child(row['ID']).update({
                                            "title": new_title,
                                            "description": new_description,
                                            "status": new_status.lower(),
                                            "assignee": new_assignee,
                                            "updated_at": datetime.now().isoformat()
                                        }, st.session_state.user['idToken'])
                                        st.session_state[f"edit_{table}_{row['ID']}"] = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error updating {section[:-1].lower()}: {str(e)}")
                            with col_cancel:
                                if st.form_submit_button("Cancel"):
                                    st.session_state[f"edit_{table}_{row['ID']}"] = False
                                    st.rerun()

    elif section == "EOD Report":
        st.title("End of Day Report")
        if not st.session_state.project_id:
            st.warning("Please select a project from the Projects section.")
            return
        if st.button("Generate EOD Report"):
            try:
                start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                report = "End of Day Report\n\n"
                
                for table, name in [('tasks', 'Tasks'), ('issues', 'Issues'), ('tickets', 'Tickets')]:
                    items = db.child(table).get(st.session_state.user['idToken']).val()
                    report += f"{name}:\n"
                    found = False
                    if items:
                        for key, data in items.items():
                            if data.get('project_id') == st.session_state.project_id and data.get('updated_at', '') >= start_of_day:
                                found = True
                                report += f"- {data['title']}\n  Status: {data['status']}\n  Assignee: {data.get('assignee', 'Unassigned')}\n\n"
                    if not found:
                        report += f"No {name.lower()} updated today.\n\n"
                
                st.session_state.eod_report = report
                st.text_area("EOD Report", report, height=300, disabled=True)
                st.download_button("Download Report", report, "eod_report.txt")
            except Exception as e:
                st.error(f"Error generating EOD report: {str(e)}")

if __name__ == "__main__":
    main()
