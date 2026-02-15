# -*- coding: utf-8 -*-
from datetime import datetime
from database_connector import get_db_connection
import mysql
from fpdf import FPDF
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime, date, timedelta
import decimal
import math
from functools import wraps

def get_dashboard_counts():
    """
    Handles the logic for fetching dashboard counts.
    It calls the database connector, executes queries, and returns the results.
    """
    conn = get_db_connection()
    if conn is None:
        return {'error': 'Database connection failed'}

    cursor = conn.cursor()
    counts = {}

    try:
        cursor.execute("SELECT COUNT(*) FROM Clients")
        counts['clients'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Projects")
        counts['projects'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Employees")
        counts['employees'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Invoices")
        counts['invoices'] = cursor.fetchone()[0]
        
        return counts
    except Exception as e:
        print(f"Logic Handler Error: {e}")
        return {'error': 'Failed to retrieve counts due to a query error.'}
    finally:
        cursor.close()
        conn.close()

def add_new_client(client_data):
    """
    Handles the logic for adding a new client.
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    sql_insert = """
    INSERT INTO Clients (ClientName, ContactPerson, Phone, Email, Address, ClientType)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (
        client_data.get('clientName'),
        client_data.get('contactPerson'),
        client_data.get('phone'),
        client_data.get('email'),
        client_data.get('address'),
        client_data.get('clientType')
    )
    
    try:
        cursor.execute(sql_insert, values)
        conn.commit()
        return True, "Client added successfully!"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

# You would add more functions here for other logic, like getting a list of clients, etc.
def generate_new_id(prefix, table_name):
    """Generates a new ID based on the count of existing records."""
    conn = get_db_connection()
    if conn is None:
        return None

    cursor = conn.cursor()
    try:
        # Use a parameterized query to avoid SQL injection
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        new_id = f"{prefix}_{count + 1:03d}"
        return new_id
    except Exception as e:
        print(f"Error generating ID: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def add_new_client(client_data):
    """
    Handles the logic for adding a new client with robust error checking.
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()

    # Step 1: Check for required fields to prevent NOT NULL errors
    if not client_data.get('client_name'):
        return False, "Client Name is a required field."

    try:
        # Step 2: Get the current count to generate a new ID
        cursor.execute("SELECT COUNT(*) FROM clients")
        count = cursor.fetchone()[0]
        # Format the ID to match your 'C_001' pattern
        client_id = f"C_{count + 1:03d}"
        
        # Step 3: Insert the new client record
        sql_insert = """
        INSERT INTO clients (client_id, client_name, contact_person, phone, email, address, client_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            client_id,
            client_data.get('client_name'),
            client_data.get('contact_person'),
            client_data.get('phone'),
            client_data.get('email'),
            client_data.get('address'),
            client_data.get('client_type')
        )
        
        cursor.execute(sql_insert, values)
        conn.commit()
        return True, "Client added successfully!"

    except mysql.connector.Error as err:
        conn.rollback()
        # Return a more specific error from the database
        return False, f"Database Error: {err}"
    except Exception as e:
        conn.rollback()
        return False, f"An unexpected error occurred: {e}"
    finally:
        cursor.close()
        conn.close()

def get_all_clients():
    """Retrieves all client records from the database."""
    conn = get_db_connection()
    if conn is None:
        return {'error': 'Database connection failed'}

    # Ensure cursor returns a dictionary for easy key access
    cursor = conn.cursor(dictionary=True)
    clients = []

    try:
        cursor.execute("SELECT * FROM clients")
        clients = cursor.fetchall()
        return {'clients': clients}
    except Exception as e:
        print(f"Logic Handler Error (get_all_clients): {e}")
        return {'error': 'Failed to retrieve clients.'}
    finally:
        cursor.close()
        conn.close()

def delete_client(client_id):
    """
    Handles the logic for deleting a client.
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    sql_delete = "DELETE FROM clients WHERE client_id = %s"
    
    try:
        cursor.execute(sql_delete, (client_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Client deleted successfully!"
        else:
            return False, "Client not found."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def get_client_details(client_id):
    """Fetches details of a single client to generate a PDF."""
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed."
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        sql_query = "SELECT * FROM clients WHERE client_id = %s"
        cursor.execute(sql_query, (client_id,))
        client_data = cursor.fetchone()
        return client_data, "Success"
    except Exception as e:
        print(f"Error fetching client details: {e}")
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def generate_client_pdf(client_data):
    """Generates a professional single-client PDF report."""
    if not client_data:
        return None

    pdf = FPDF()
    pdf.add_page()
    
    # --- COMPANY HEADER ---
    pdf.set_fill_color(0, 77, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 15, 'OM Enterprises', 0, 1, 'C', 1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, 'Client Profile Report', 0, 1, 'C', 0)
    pdf.ln(10)
    
    # --- CLIENT IDENTIFICATION ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"CLIENT: {client_data.get('client_name', 'N/A').upper()}", 0, 1, 'L')
    pdf.set_line_width(0.5)
    pdf.set_draw_color(0, 77, 153)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # Details Layout
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 7, 'Client ID:', 0, 0, 'L')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 7, f"{client_data.get('client_id', 'N/A')}", 0, 1, 'L')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 7, 'Client Type:', 0, 0, 'L')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 7, f"{client_data.get('client_type', 'N/A')}", 0, 1, 'L')
    pdf.ln(5)

    # --- CONTACT INFORMATION ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, 'Contact Information', 0, 1, 'L')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 7, 'Contact Person:', 0, 0, 'L')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 7, f"{client_data.get('contact_person', 'N/A')}", 0, 1, 'L')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 7, 'Phone:', 0, 0, 'L')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 7, f"{client_data.get('phone', 'N/A')}", 0, 1, 'L')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 7, 'Email:', 0, 0, 'L')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 7, f"{client_data.get('email', 'N/A')}", 0, 1, 'L')

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 7, 'Address:', 0, 0, 'L')
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 7, f"{client_data.get('address', 'N/A')}", 0, 'L')
    pdf.ln(10)
    
     # --- FOOTER ---
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'This document is a confidential Client Profile generated by the CMS System.', 0, 1, 'C')
   
    return pdf.output(dest='S').encode('latin1')

def get_all_clients_data():
    """Fetches all client records to generate a master PDF."""
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed."

    cursor = conn.cursor(dictionary=True)

    try:
        sql_query = "SELECT * FROM clients"
        cursor.execute(sql_query)
        clients_data = cursor.fetchall()
        return clients_data, "Success"
    except Exception as e:
        print(f"Error fetching all client data: {e}")
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def generate_all_clients_pdf(clients_data):
    """Generates a single, professional PDF report for all clients."""
    if not clients_data:
        return None

    pdf = FPDF()
    pdf.add_page()
    
    # --- GLOBAL HEADER ---
    pdf.set_fill_color(0, 77, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 15, 'OM Enterprises', 0, 1, 'C', 1)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 5, 'Comprehensive Client Roster', 0, 1, 'C', 0)
    pdf.ln(10)
    
    # --- TABLE SETUP ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(220, 220, 220)
    
    # Define Column Widths
    col_widths = [15, 45, 40, 30, 40]
    
    # Table Headers
    pdf.cell(col_widths[0], 7, 'ID', 1, 0, 'C', 1)
    pdf.cell(col_widths[1], 7, 'Name', 1, 0, 'L', 1)
    pdf.cell(col_widths[2], 7, 'Contact Person', 1, 0, 'L', 1)
    pdf.cell(col_widths[3], 7, 'Phone', 1, 0, 'L', 1)
    pdf.cell(col_widths[4], 7, 'Type', 1, 1, 'L', 1)
    
    # Table Data
    pdf.set_font('Arial', '', 9)
    for client in clients_data:
        # Check if new page is needed
        if pdf.get_y() > 270:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 10)
            pdf.set_fill_color(220, 220, 220)
            pdf.cell(col_widths[0], 7, 'ID', 1, 0, 'C', 1)
            pdf.cell(col_widths[1], 7, 'Name', 1, 0, 'L', 1)
            pdf.cell(col_widths[2], 7, 'Contact Person', 1, 0, 'L', 1)
            pdf.cell(col_widths[3], 7, 'Phone', 1, 0, 'L', 1)
            pdf.cell(col_widths[4], 7, 'Type', 1, 1, 'L', 1)
            pdf.set_font('Arial', '', 9)

        pdf.cell(col_widths[0], 6, client.get('client_id', 'N/A'), 1, 0, 'C', 0)
        pdf.cell(col_widths[1], 6, client.get('client_name', 'N/A'), 1, 0, 'L', 0)
        pdf.cell(col_widths[2], 6, client.get('contact_person', 'N/A'), 1, 0, 'L', 0)
        pdf.cell(col_widths[3], 6, client.get('phone', 'N/A'), 1, 0, 'L', 0)
        pdf.cell(col_widths[4], 6, client.get('client_type', 'N/A'), 1, 1, 'L', 0)
    
     # --- FOOTER ---
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'Report Generated by CMS System', 0, 1, 'C')

    return pdf.output(dest='S').encode('latin1')

def get_all_projects():
    """
    Retrieves all project records from the Projects table using snake_case.
    """
    conn = get_db_connection()
    if conn is None:
        return {'error': 'Database connection failed'}

    cursor = conn.cursor(dictionary=True)
    projects = []

    try:
        cursor.execute("SELECT * FROM projects")
        projects = cursor.fetchall()
        return {'projects': projects}
    except Exception as e:
        print(f"Logic Handler Error (get_all_projects): {e}")
        return {'error': 'Failed to retrieve projects.'}
    finally:
        cursor.close()
        conn.close()

def add_new_project(project_data):
    """
    Handles the logic for adding a new project using snake_case.
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."
    
    cursor = conn.cursor()

    try:
        sql_insert = """
        INSERT INTO projects (project_id, client_id, project_name, project_location, start_date, end_date, status, budget, actual_cost, contract_value, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            project_data.get('project_id'),
            project_data.get('client_id'),
            project_data.get('project_name'),
            project_data.get('project_location'),
            project_data.get('start_date'),
            project_data.get('end_date'),
            project_data.get('status'),
            project_data.get('budget'),
            project_data.get('actual_cost'),
            project_data.get('contract_value'),
            project_data.get('description')
        )
        
        cursor.execute(sql_insert, values)
        conn.commit()
        return True, "Project added successfully!"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def delete_project(project_id):
    """
    Handles the logic for deleting a project using snake_case.
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    sql_delete = "DELETE FROM projects WHERE project_id = %s"
    
    try:
        cursor.execute(sql_delete, (project_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Project deleted successfully!"
        else:
            return False, "Project not found."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def get_project_details(project_id):
    """Fetches details of a single project to generate a PDF."""
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed."
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        sql_query = "SELECT * FROM projects WHERE project_id = %s"
        cursor.execute(sql_query, (project_id,))
        project_data = cursor.fetchone()
        return project_data, "Success"
    except Exception as e:
        print(f"Error fetching project details: {e}")
        return None, str(e)
    finally:
        cursor.close()
        conn.close()
        
def generate_project_pdf(project_data):
    """Generates a professional project details PDF with improved styling."""
    if not project_data:
        return None

    pdf = FPDF()
    pdf.add_page()
    
    # --- COMPANY HEADER (OM Enterprises Branding) ---
    pdf.set_fill_color(0, 77, 153) # Dark Blue background (004D99 in hex)
    pdf.set_text_color(255, 255, 255) # White text
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 15, 'OM Enterprises', 0, 1, 'C', 1)
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, 'Contractor Management System | Project Report', 0, 1, 'C', 0)
    pdf.ln(8)
    
    # --- PROJECT IDENTIFICATION ---
    pdf.set_text_color(0, 0, 0) # Black text
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"PROJECT: {project_data.get('project_name', 'N/A').upper()}", 0, 1, 'L')
    pdf.set_line_width(0.5)
    pdf.set_draw_color(0, 77, 153)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    # Two-Column Detail Layout
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(40, 6, 'Project ID:', 0, 0, 'L')
    pdf.set_font("Arial", '', 11)
    pdf.cell(50, 6, f"{project_data.get('project_id', 'N/A')}", 0, 0, 'L')
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(40, 6, 'Client ID:', 0, 0, 'L')
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 6, f"{project_data.get('client_id', 'N/A')}", 0, 1, 'L')

    pdf.set_font("Arial", 'B', 11)
    pdf.cell(40, 6, 'Location:', 0, 0, 'L')
    pdf.set_font("Arial", '', 11)
    pdf.cell(50, 6, f"{project_data.get('project_location', 'N/A')}", 0, 0, 'L')
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(40, 6, 'Status:', 0, 0, 'L')
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, f"{project_data.get('status', 'N/A').upper()}", 0, 1, 'L')
    pdf.ln(5)

    # --- FINANCIAL SUMMARY TABLE ---
    pdf.set_fill_color(220, 220, 220) # Light grey for table header
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(60, 8, 'FINANCIAL METRIC', 1, 0, 'L', 1)
    pdf.cell(50, 8, 'VALUE (Rs)', 1, 1, 'R', 1)
    
    pdf.set_font("Arial", '', 11)
    pdf.cell(60, 8, 'Contract Value', 1, 0, 'L', 0)
    pdf.cell(50, 8, f"Rs. {project_data.get('contract_value', 'N/A')}", 1, 1, 'R', 0)
    
    pdf.cell(60, 8, 'Initial Budget', 1, 0, 'L', 0)
    pdf.cell(50, 8, f"Rs. {project_data.get('budget', 'N/A')}", 1, 1, 'R', 0)
    
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(200, 200, 200) # Slightly darker grey for cost
    pdf.cell(60, 8, 'Actual Cost', 1, 0, 'L', 1)
    pdf.cell(50, 8, f"Rs. {project_data.get('actual_cost', 'N/A')}", 1, 1, 'R', 1)
    
    pdf.ln(10)

    # --- DESCRIPTION ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 7, 'Detailed Description:', 0, 1, 'L')
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 6, f"{project_data.get('description', 'No description provided.')}", 1, 'L')
    
    pdf.ln(15)

    # --- FOOTER ---
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'Report Generated by CMS System', 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin1')

def get_all_projects_data():
    """Fetches all project records to generate a PDF."""
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed."

    cursor = conn.cursor(dictionary=True)

    try:
        sql_query = "SELECT * FROM projects"
        cursor.execute(sql_query)
        projects_data = cursor.fetchall()
        return projects_data, "Success"
    except Exception as e:
        print(f"Error fetching all project data: {e}")
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def generate_all_projects_pdf(projects_data):
    """Generates a single, professional PDF report for all projects."""
    if not projects_data:
        return None

    pdf = FPDF()
    pdf.add_page()
    
    # --- Company Header ---
    pdf.set_fill_color(0, 77, 153)  # Dark Blue background
    pdf.set_text_color(255, 255, 255)  # White text
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(0, 15, 'OM Enterprises', 0, 1, 'C', 1)
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 5, 'Comprehensive Project Report', 0, 1, 'C', 0)
    pdf.ln(10)
    
    # --- Content ---
    pdf.set_text_color(0, 0, 0)  # Black text
    
    for project in projects_data:
        # Project Main Title
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 8, f"Project ID: {project.get('project_id', 'N/A')} - {project.get('project_name', 'No Name')}", 0, 1, 'L')
        
        # Details Table (Simplified two-column layout)
        pdf.set_font("Arial", '', 11)
        
        # Financial Row 1
        pdf.cell(40, 6, 'Client ID:', 0, 0, 'L')
        pdf.cell(50, 6, f"{project.get('client_id', 'N/A')}", 0, 0, 'L')
        pdf.cell(40, 6, 'Status:', 0, 0, 'L')
        pdf.cell(0, 6, f"{project.get('status', 'N/A')}", 0, 1, 'L')
        
        # Financial Row 2
        pdf.cell(40, 6, 'Start Date:', 0, 0, 'L')
        pdf.cell(50, 6, f"{project.get('start_date', 'N/A')}", 0, 0, 'L')
        pdf.cell(40, 6, 'Contract Value:', 0, 0, 'L')
        pdf.cell(0, 6, f"Rs. {project.get('contract_value', '0.00')}", 0, 1, 'L')
        
        # Financial Row 3
        pdf.cell(40, 6, 'Budget:', 0, 0, 'L')
        pdf.cell(50, 6, f"Rs. {project.get('budget', '0.00')}", 0, 0, 'L')
        pdf.cell(40, 6, 'Actual Cost:', 0, 0, 'L')
        pdf.cell(0, 6, f"Rs. {project.get('actual_cost', '0.00')}", 0, 1, 'L')
        
        # Description
        pdf.set_font("Arial", 'I', 10)
        pdf.multi_cell(0, 5, f"Location: {project.get('project_location', 'N/A')}", 0, 'L')
        pdf.ln(3)
        
        # Separator Line for Next Project
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        

    return pdf.output(dest='S').encode('latin1')

# Function to add existing employees from the project synopsis
def add_existing_employees():
    """Adds existing employee data from the project document."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()

    # The data from your project synopsis 
    existing_employees = [
        ('E_001', 'Bharat', 'Gharat', 'Project Manager', '7 Years', None, 'Active', '9876543210', 'bharat.g@omenter.com', '2018-01-15', 75000.00),
        ('E_002', 'Sushank', 'Kirdak', 'Civil Engineer', '7 Years', None, 'Active', '9876543211', 'sushank.k@omenter.com', '2018-01-15', 75000.00),
        ('E_003', 'Rambhau', 'Gharat', 'Site Supervisor', '10 Years', None, 'Active', '9876543212', 'rambhau.g@omenter.com', '2018-01-15', 75000.00),
        ('E_004', 'Pandurang', 'Kirdak', 'Site Supervisor', '10 Years', None, 'Active', '9876543213', 'pandurang.k@omenter.com', '2018-01-15', 75000.00),
        ('E_005', 'Rupchand', 'Gharat', 'Site Supervisor', '12 Years', None, 'Active', '9876543214', 'rupchand.g@omenter.com', '2018-01-15', 75000.00),
        ('E_006', 'Ashok', 'Kirdak', 'Site Supervisor', '10 Years', None, 'Active', '9876543215', 'ashok.k@omenter.com', '2018-01-15', 75000.00),
        ('E_007', 'Datta', 'Ingole', 'Site Supervisor', '10 Years', None, 'Active', '9876543216', 'datta.i@omenter.com', '2018-01-15', 75000.00)
    ]
    
    # This query uses snake_case to match your database schema
    sql_insert = """
    INSERT INTO employees (employee_id, first_name, last_name, role, experience_years, contact_phone, email, hire_date, salary, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        # Check if the table is empty before populating
        cursor.execute("SELECT COUNT(*) FROM employees")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.executemany(sql_insert, existing_employees)
            conn.commit()
            print(f"Successfully added {cursor.rowcount} existing employees.")
        else:
            print("Employee table is not empty. Skipping population.")
        return True, "Existing employees processed."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def get_all_employees():
    """
    Retrieves all employee records from the database.
    """
    conn = get_db_connection()
    if conn is None:
        return {'error': 'Database connection failed'}

    cursor = conn.cursor(dictionary=True)
    employees = []

    try:
        cursor.execute("SELECT * FROM employees")
        employees = cursor.fetchall()
        return {'employees': employees}
    except Exception as e:
        print(f"Logic Handler Error (get_all_employees): {e}")
        return {'error': 'Failed to retrieve employees.'}
    finally:
        cursor.close()
        conn.close()

def add_new_employee(employee_data):
    """
    Handles the logic for adding a new employee.
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    
    try:
        sql_insert = """
        INSERT INTO employees (employee_id, first_name, last_name, role, contact_phone, email, hire_date, salary, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            employee_data.get('employee_id'),
            employee_data.get('first_name'),
            employee_data.get('last_name'),
            employee_data.get('role'),
            employee_data.get('contact_phone'),
            employee_data.get('email'),
            employee_data.get('hire_date'),
            employee_data.get('salary'),
            employee_data.get('status')
        )
        
        cursor.execute(sql_insert, values)
        conn.commit()
        return True, "Employee added successfully!"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def delete_employee(employee_id):
    """
    Handles the logic for deleting an employee.
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    sql_delete = "DELETE FROM employees WHERE employee_id = %s"
    
    try:
        cursor.execute(sql_delete, (employee_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Employee deleted successfully!"
        else:
            return False, "Employee not found."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def get_all_employees_data():
    """Fetches all employee records to generate a PDF."""
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed."

    cursor = conn.cursor(dictionary=True)

    try:
        sql_query = "SELECT employee_id, first_name, last_name, role, contact_phone, email, hire_date, salary, status FROM employees"
        cursor.execute(sql_query)
        employees_data = cursor.fetchall()
        return employees_data, "Success"
    except Exception as e:
        print(f"Error fetching all employee data: {e}")
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def get_employee_details(employee_id):
    # ... (code remains the same) ...
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed."
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 1. Fetch Employee Details
        sql_employee = "SELECT * FROM employees WHERE employee_id = %s"
        cursor.execute(sql_employee, (employee_id,))
        employee_data = cursor.fetchone()

        if not employee_data:
            return None, "Employee not found."

        # 2. Fetch Project Assignment Details
        sql_assignments = """
        SELECT 
            pa.project_id, 
            pa.assignment_role, 
            pa.assignment_start_date, 
            pa.assignment_end_date,
            p.client_id
        FROM project_assignments pa
        LEFT JOIN projects p ON pa.project_id = p.project_id
        WHERE pa.employee_id = %s
        """
        cursor.execute(sql_assignments, (employee_id,))
        assignments_data = cursor.fetchall()
        
        # --- Data Conversion for Employee Data ---
        for key, value in employee_data.items():
            if isinstance(value, (date, decimal.Decimal)):
                employee_data[key] = str(value)
            elif value is None:
                employee_data[key] = 'N/A'
        
        # --- Data Conversion for Assignment Data ---
        final_assignments = []
        for assign in assignments_data:
            for key, value in assign.items():
                if isinstance(value, (date, decimal.Decimal)):
                    assign[key] = str(value)
                elif value is None:
                    assign[key] = 'N/A'
            final_assignments.append(assign)
            
        employee_data['assignments'] = final_assignments
        
        return employee_data, "Success"
    except Exception as e:
        print(f"Error fetching employee details and assignments: {e}")
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def generate_employee_pdf(employee_data):
    """Generates a professional single-employee PDF report with Project ID and Client ID."""
    if not employee_data:
        return None

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, margin=15)
    
    # --- COMPANY HEADER ---
    pdf.set_fill_color(0, 77, 153) # Dark Blue background
    pdf.set_text_color(255, 255, 255) # White text
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 15, 'OM Enterprises', 0, 1, 'C', 1)
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, 'Official Employee Profile', 0, 1, 'C', 0)
    pdf.ln(10)
    
    # --- EMPLOYEE IDENTIFICATION ---
    pdf.set_text_color(0, 0, 0) # Black text
    full_name = f"{employee_data.get('first_name', 'N/A')} {employee_data.get('last_name', 'N/A')}"
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"EMPLOYEE: {full_name.upper()}", 0, 1, 'L')
    pdf.set_line_width(0.5)
    pdf.set_draw_color(0, 77, 153)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # --- JOB AND STATUS DETAILS (Two Columns) ---
    
    # Row 1: ID and Role
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 7, 'Employee ID:', 0, 0, 'L')
    pdf.set_font("Arial", '', 12)
    pdf.cell(50, 7, employee_data.get('employee_id', 'N/A'), 0, 0, 'L')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 7, 'Role:', 0, 0, 'L')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 7, employee_data.get('role', 'N/A'), 0, 1, 'L')
    
    # Row 2: Status and Hire Date
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 7, 'Status:', 0, 0, 'L')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 7, employee_data.get('status', 'N/A').upper(), 0, 0, 'L')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 7, 'Hire Date:', 0, 0, 'L')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 7, employee_data.get('hire_date', 'N/A'), 0, 1, 'L')
    
    pdf.ln(5)

    # --- PROJECT ASSIGNMENTS SECTION ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, 'Project Assignments', 0, 1, 'L')
    pdf.set_line_width(0.2)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    assignments = employee_data.get('assignments', [])
    
    if assignments:
        # Table Headers
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(240, 240, 240)
        
        # Define Column Widths: ProjectID, ClientID, Role, StartDate, EndDate
        col_widths = [25, 25, 55, 45, 40] 
        
        pdf.cell(col_widths[0], 6, 'Project ID', 1, 0, 'C', 1)
        pdf.cell(col_widths[1], 6, 'Client ID', 1, 0, 'C', 1)
        pdf.cell(col_widths[2], 6, 'Role', 1, 0, 'L', 1)
        pdf.cell(col_widths[3], 6, 'Start Date', 1, 0, 'C', 1)
        pdf.cell(col_widths[4], 6, 'End Date', 1, 1, 'C', 1)

        # Table Data
        pdf.set_font('Arial', '', 9)
        for assign in assignments:
            # All assignment fields are already strings due to conversion above
            pdf.cell(col_widths[0], 5, assign.get('project_id', 'N/A'), 1, 0, 'C')
            pdf.cell(col_widths[1], 5, assign.get('client_id', 'N/A'), 1, 0, 'C')
            pdf.cell(col_widths[2], 5, assign.get('assignment_role', 'N/A'), 1, 0, 'L')
            pdf.cell(col_widths[3], 5, assign.get('assignment_start_date', 'N/A'), 1, 0, 'C')
            pdf.cell(col_widths[4], 5, assign.get('assignment_end_date', 'N/A'), 1, 1, 'C')
    else:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 5, 'No current or past project assignments found.', 0, 1, 'L')
    
    pdf.ln(10)

    # --- FINANCIAL AND CONTACT INFORMATION ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, 'Contact & Financials', 0, 1, 'L')
    pdf.ln(1)

    # Financial Row
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(50, 7, 'Annual Salary (Rs):', 1, 0, 'L', 1)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 7, f"Rs. {employee_data.get('salary', 'N/A')}", 1, 1, 'R', 1)
    
    # Contact Row 1
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 7, 'Contact Phone:', 0, 0, 'L')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 7, employee_data.get('contact_phone', 'N/A'), 0, 1, 'L')
    
    # Contact Row 2
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 7, 'Email:', 0, 0, 'L')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 7, employee_data.get('email', 'N/A'), 0, 1, 'L')
    
    pdf.ln(15)

    # --- FOOTER ---
    pdf.set_y(-15)
    pdf.set_font('Arial', 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, f"Report generated by CMS System on {datetime.now().strftime('%Y-%m-%d')}", 0, 1, 'C')
    
    # CRITICAL FIX APPLIED: Removed .encode('latin1')
    return pdf.output(dest='S').encode('latin1')

def generate_all_employees_pdf(employees_data):
    """Generates a single, professional PDF report for all employees."""
    if not employees_data:
        return None

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- GLOBAL COMPANY HEADER ---
    pdf.set_fill_color(0, 77, 153) # Dark Blue background (004D99)
    pdf.set_text_color(255, 255, 255) # White text
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(0, 15, 'OM Enterprises', 0, 1, 'C', 1)
    
    pdf.set_fill_color(0, 77, 153) # Dark Blue background (004D99)
    pdf.set_text_color(255, 255, 255) # White text
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 5, 'Official Employee Roster Report', 0, 1, 'C', 0)
    pdf.ln(10)
    
    pdf.set_text_color(0, 0, 0) # Reset to Black text
    
    # --- TABLE HEADER ---
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(220, 220, 220) # Light Gray background for header
    
    # Define Column Widths
    col_widths = [15, 30, 35, 25, 40, 25, 20] 
    
    # Print Table Headers
    pdf.cell(col_widths[0], 7, 'ID', 1, 0, 'C', 1)
    pdf.cell(col_widths[1], 7, 'Full Name', 1, 0, 'L', 1)
    pdf.cell(col_widths[2], 7, 'Role', 1, 0, 'L', 1)
    pdf.cell(col_widths[3], 7, 'Status', 1, 0, 'C', 1)
    pdf.cell(col_widths[4], 7, 'Email', 1, 0, 'L', 1)
    pdf.cell(col_widths[5], 7, 'Hire Date', 1, 0, 'C', 1)
    pdf.cell(col_widths[6], 7, 'Salary (Rs)', 1, 1, 'R', 1)

    # --- TABLE BODY ---
    pdf.set_font('Arial', '', 9)
    pdf.set_fill_color(255, 255, 255) # White background for rows
    
    for emp in employees_data:
        # Check for page break
        if pdf.get_y() > 270:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 10)
            pdf.set_fill_color(220, 220, 220)
            # Reprint Headers on new page
            pdf.cell(col_widths[0], 7, 'ID', 1, 0, 'C', 1)
            pdf.cell(col_widths[1], 7, 'Full Name', 1, 0, 'L', 1)
            pdf.cell(col_widths[2], 7, 'Role', 1, 0, 'L', 1)
            pdf.cell(col_widths[3], 7, 'Status', 1, 0, 'C', 1)
            pdf.cell(col_widths[4], 7, 'Email', 1, 0, 'L', 1)
            pdf.cell(col_widths[5], 7, 'Hire Date', 1, 0, 'C', 1)
            pdf.cell(col_widths[6], 7, 'Salary (Rs)', 1, 1, 'R', 1)
            pdf.set_font('Arial', '', 9)


        full_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}"
        
        pdf.cell(col_widths[0], 6, emp.get('employee_id', 'N/A'), 1, 0, 'C')
        pdf.cell(col_widths[1], 6, full_name, 1, 0, 'L')
        pdf.cell(col_widths[2], 6, emp.get('role', 'N/A'), 1, 0, 'L')
        pdf.cell(col_widths[3], 6, emp.get('status', 'N/A'), 1, 0, 'C')
        pdf.cell(col_widths[4], 6, emp.get('email', 'N/A'), 1, 0, 'L')
        pdf.cell(col_widths[5], 6, str(emp.get('hire_date', 'N/A')), 1, 0, 'C') # Convert Date object to string
        pdf.cell(col_widths[6], 6, f"{emp.get('salary', '0.00'):.2f}", 1, 1, 'R')
        

     # --- FOOTER ---
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'Report Generated by CMS System', 0, 1, 'C')

    return pdf.output(dest='S').encode('latin1')

# Function to add existing suppliers from the project synopsis
def add_existing_suppliers():
    """Adds existing supplier data from the project document."""
    conn = get_db_connection()
    if conn is None:
        print("Cannot populate data: No database connection.")
        return False, "Database connection failed."

    cursor = conn.cursor()

    # [cite_start]The data from your project synopsis [cite: 665]
    existing_suppliers = [
        ('SP_001', 'Bright Paints India', 'Anil Kumar', '+918001122334', 'sales@brightpaints.in', '7, Industrial Area, Mumbai-400004', 'Material'),
    ]

    # This query uses snake_case to match your database schema
    sql_insert = """
    INSERT INTO suppliers (supplier_id, name, contact_person, phone, email, address, supplier_type)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    try:
        # Check if the table is empty before populating
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.executemany(sql_insert, existing_suppliers)
            conn.commit()
            print(f"Successfully added {cursor.rowcount} existing suppliers.")
        else:
            print("Supplier table is not empty. Skipping population.")
        return True, "Existing suppliers processed."
    except mysql.connector.Error as err:
        conn.rollback()
        return False, str(err)
    finally:
        cursor.close()
        conn.close()

def get_all_suppliers():
    """
    Retrieves all supplier records from the database.
    """
    conn = get_db_connection()
    if conn is None:
        return {'error': 'Database connection failed'}

    cursor = conn.cursor(dictionary=True)
    suppliers = []

    try:
        cursor.execute("SELECT * FROM suppliers")
        suppliers = cursor.fetchall()
        return {'suppliers': suppliers}
    except Exception as e:
        print(f"Logic Handler Error (get_all_suppliers): {e}")
        return {'error': 'Failed to retrieve suppliers.'}
    finally:
        cursor.close()
        conn.close()

def add_new_supplier(supplier_data):
    """
    Handles the logic for adding a new supplier.
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    
    try:
        # ⚠️ Corrected column name to 'Name'
        sql_insert = """
        INSERT INTO suppliers (supplier_id, supplier_name, contact_person, phone, email, address)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            supplier_data.get('supplier_id'),
            supplier_data.get('supplier_name'),
            supplier_data.get('contact_person'),
            supplier_data.get('phone'),
            supplier_data.get('email'),
            supplier_data.get('address'),
        )
        
        cursor.execute(sql_insert, values)
        conn.commit()
        return True, "Supplier added successfully!"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def delete_supplier(supplier_id):
    """
    Handles the logic for deleting a supplier.
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    sql_delete = "DELETE FROM suppliers WHERE supplier_id = %s"
    
    try:
        cursor.execute(sql_delete, (supplier_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Supplier deleted successfully!"
        else:
            return False, "Supplier not found."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()
def get_all_suppliers_data():
    """
    Fetches all supplier records to generate a PDF.
    """
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed."

    cursor = conn.cursor(dictionary=True)

    try:
        sql_query = "SELECT * FROM suppliers"
        cursor.execute(sql_query)
        suppliers_data = cursor.fetchall()
        return suppliers_data, "Success"
    except Exception as e:
        print(f"Error fetching all supplier data: {e}")
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def generate_all_suppliers_pdf(suppliers_data):
    """
    Generates a single PDF with details of all suppliers.
    """
    if not suppliers_data:
        return None

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="All Supplier Details", ln=True, align="C")
    pdf.ln(10)

    for supplier in suppliers_data:
        pdf.cell(200, 10, txt=f"Supplier ID: {supplier.get('supplier_id', 'N/A')}", ln=True, align="L")
        pdf.cell(200, 10, txt=f"Name: {supplier.get('name', 'N/A')}", ln=True, align="L")
        pdf.cell(200, 10, txt=f"Contact Person: {supplier.get('contact_person', 'N/A')}", ln=True, align="L")
        pdf.cell(200, 10, txt=f"Phone: {supplier.get('phone', 'N/A')}", ln=True, align="L")
        pdf.cell(200, 10, txt=f"Email: {supplier.get('email', 'N/A')}", ln=True, align="L")
        pdf.cell(200, 10, txt=f"Address: {supplier.get('address', 'N/A')}", ln=True, align="L")
        pdf.cell(200, 10, txt=f"Supplier Type: {supplier.get('supplier_type', 'N/A')}", ln=True, align="L")
        pdf.ln(5)
    
    return pdf.output(dest='S').encode('latin1')

def get_supplier_details(supplier_id):
    """
    Fetches details of a single supplier to generate a PDF.
    """
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed."
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        sql_query = "SELECT * FROM suppliers WHERE supplier_id = %s"
        cursor.execute(sql_query, (supplier_id,))
        supplier_data = cursor.fetchone()
        return supplier_data, "Success"
    except Exception as e:
        print(f"Error fetching supplier details: {e}")
        return None, str(e)
    finally:
        cursor.close()
        conn.close()
        
def generate_supplier_pdf(supplier_data):
    """
    Generates a supplier details PDF.
    """
    if not supplier_data:
        return None

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Supplier Details", ln=True, align="C")
    pdf.cell(200, 10, txt=f"Supplier ID: {supplier_data.get('supplier_id', 'N/A')}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Name: {supplier_data.get('name', 'N/A')}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Contact Person: {supplier_data.get('contact_person', 'N/A')}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Phone: {supplier_data.get('phone', 'N/A')}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Email: {supplier_data.get('email', 'N/A')}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Address: {supplier_data.get('address', 'N/A')}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Supplier Type: {supplier_data.get('supplier_type', 'N/A')}", ln=True, align="L")
    
    return pdf.output(dest='S').encode('latin1')

# Function to add existing invoices from the project synopsis
def add_existing_invoices():
    """Adds existing invoice data from the project document."""
    conn = get_db_connection()
    if conn is None:
        print("Cannot populate data: No database connection.")
        return False, "Database connection failed."

    cursor = conn.cursor()

    existing_invoices = [
        ('1001', 'P_001', 'C_001', '2024-04-16', '2024-05-16', 160000.00, 160000.00, 'Paid'),
    ]

    sql_insert = """
    INSERT INTO invoices (invoice_id, project_id, client_id, invoice_date, due_date, amount_due, amount_paid, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        cursor.execute("SELECT COUNT(*) FROM invoices")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.executemany(sql_insert, existing_invoices)
            conn.commit()
            print(f"Successfully added {cursor.rowcount} existing invoices.")
        else:
            print("Invoices table is not empty. Skipping population.")
        return True, "Existing invoices processed."
    except mysql.connector.Error as err:
        conn.rollback()
        return False, str(err)
    finally:
        cursor.close()
        conn.close()

def get_all_invoices():
    """
    Retrieves all invoice records from the database.
    """
    conn = get_db_connection()
    if conn is None:
        return {'error': 'Database connection failed'}

    cursor = conn.cursor(dictionary=True)
    invoices = []

    try:
        cursor.execute("SELECT * FROM invoices")
        invoices = cursor.fetchall()
        return {'invoices': invoices}
    except Exception as e:
        print(f"Logic Handler Error (get_all_invoices): {e}")
        return {'error': 'Failed to retrieve invoices.'}
    finally:
        cursor.close()
        conn.close()

def generate_new_invoice(invoice_data):
    """
    Generates a new invoice record and saves it to the database.
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    
    try:
        sql_insert = """
        INSERT INTO invoices (invoice_id, project_id, client_id, invoice_date, due_date, amount_due, amount_paid, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            invoice_data.get('invoice_id'),
            invoice_data.get('project_id'),
            invoice_data.get('client_id'),
            invoice_data.get('invoice_date'),
            invoice_data.get('due_date'),
            invoice_data.get('amount_due'),
            invoice_data.get('amount_paid'),
            invoice_data.get('status')
        )
        
        cursor.execute(sql_insert, values)
        conn.commit()
        return True, "Invoice generated successfully!"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def delete_invoice(invoice_id):
    """
    Handles the logic for deleting an invoice.
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    sql_delete = "DELETE FROM invoices WHERE invoice_id = %s"
    
    try:
        cursor.execute(sql_delete, (invoice_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Invoice deleted successfully!"
        else:
            return False, "Invoice not found."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def get_invoice_details(invoice_id):
    # ... (Code remains the same, fetches data via JOIN) ...
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed."
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        sql_query = """
        SELECT 
            i.*, 
            c.client_name, 
            c.address AS client_address 
        FROM invoices i
        LEFT JOIN clients c ON i.client_id = c.client_id
        WHERE i.invoice_id = %s
        """
        cursor.execute(sql_query, (invoice_id,))
        invoice_data = cursor.fetchone()
        
        if invoice_data:
            for key, value in invoice_data.items():
                if isinstance(value, (date, decimal.Decimal)):
                    invoice_data[key] = str(value)
            
        return invoice_data, "Success"
    except Exception as e:
        print(f"Error fetching invoice details: {e}")
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def generate_invoice_pdf(invoice_data):
    """
    Generates a professional invoice PDF with proper table alignment and clear data visibility,
    using the 'bill_amount' column as the net amount.
    """
    if not invoice_data:
        return None

    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_auto_page_break(False)
    
    # --- Data Conversion and Calculation ---
    def safe_float(key, default=0.00):
        try:
            # Use the 'bill_amount' for the NET amount, and 'amount_paid' for payments.
            return float(invoice_data.get(key, default))
        except (TypeError, ValueError, decimal.InvalidOperation):
            return default
            
    # CRITICAL CHANGE: Use 'bill_amount' as the Net Amount (Base for Tax)
    bill_amount_num = safe_float('bill_amount')
    amount_paid_num = safe_float('amount_paid')

    tax_rate = 0.09
    
    # Calculate tax based on the new bill_amount_num
    tax_amount = round(bill_amount_num * tax_rate, 2)
    total_tax_amt = round(tax_amount * 2, 2)
    subtotal_with_tax = bill_amount_num + total_tax_amt
    
    # Assuming a 0.00 round-off for simplicity, as per the code's pattern
    round_off = 0.00 
    final_total = round(subtotal_with_tax + round_off, 2)
    balance_due_num = final_total - amount_paid_num
        
    
    # Calculate final amounts
    subtotal_with_tax = bill_amount_num + total_tax_amt
    round_off = 0.58 
    final_total = round(subtotal_with_tax + round_off, 2) 
    balance_due_num = final_total - amount_paid_num
    # --- PDF GENERATION START (Header/Details remain the same) ---
    
    # 1. Company Header and Logo (Medium Size)
    pdf.set_y(10)
    
    # Logo Placeholder - Increased width to 70mm for better visibility
    try:
        pdf.image('Logo.jpg', x=10, y=10, w=95) 
    except RuntimeError:
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(70, 10, 'Om Enterprises (LOGO PLACEHOLDER)', 0, 0, 'L')
    
    # Company Address Block (Top Right)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(105, 10)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 5, 'LAXMAN A. GHARAT', 0, 1, 'R')
    pdf.set_font('Arial', '', 8)
    pdf.set_x(105)
    pdf.multi_cell(95, 4, 'Room No. A/B49,', 0, 'R')
    pdf.multi_cell(190, 4, 'Jai Tulja Bhavani Welfare Society,', 0, 'R')
    pdf.multi_cell(190, 4, 'S.V Road, Shanti Nagar,', 0, 'R')
    pdf.multi_cell(190, 4, 'Dahisar (East),Mumbai- 400068,', 0, 'R')
    pdf.multi_cell(190, 4, 'Mob : +(91) 9594105903 / 8779240990', 0, 'R')
    pdf.multi_cell(190, 4, 'E-mail : gharatlaxman44@gmail.com', 0, 'R')
   
    pdf.ln(5)

    # 2. Invoice Details (Date, No., Status, IDs)
    pdf.set_y(45)
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font('Arial', 'B', 9)
    
    # Setup for Detail Block
    x_start_details = 10 
    
    # Row 1: Invoice No. and Date
    pdf.set_x(x_start_details)
    pdf.cell(30, 5, 'INVOICE NO:', 1, 0, 'L', 1)
    pdf.set_font('Arial', '', 9)
    pdf.cell(40, 5, invoice_data.get('invoice_id', 'N/A'), 1, 0, 'L', 0)
    
    pdf.set_x(x_start_details + 80)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(30, 5, 'DATE:', 1, 0, 'L', 1)
    pdf.set_font('Arial', '', 9)
    pdf.cell(40, 5, invoice_data.get('invoice_date', 'N/A'), 1, 1, 'L', 0)
    
    # Row 2: Project ID and Client ID
    pdf.set_x(x_start_details)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(30, 5, 'PROJECT ID:', 1, 0, 'L', 1)
    pdf.set_font('Arial', '', 9)
    pdf.cell(40, 5, invoice_data.get('project_id', 'N/A'), 1, 0, 'L', 0)
    
    pdf.set_x(x_start_details + 80)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(30, 5, 'CLIENT ID:', 1, 0, 'L', 1)
    pdf.set_font('Arial', '', 9)
    pdf.cell(40, 5, invoice_data.get('client_id', 'N/A'), 1, 1, 'L', 0)
    
    # Row 3: Status
    pdf.set_x(x_start_details)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(30, 5, 'STATUS:', 1, 0, 'L', 1)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(40, 5, invoice_data.get('status', 'PENDING').upper(), 1, 1, 'L', 0)
    pdf.set_text_color(0, 0, 0) # Reset color
    pdf.ln(5)

# 3. Billing Section (Bill To / Service To)
    y_start = pdf.get_y()
    pdf.set_x(10)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(95, 6, 'Bill To Party', 1, 0, 'C', 1)
    pdf.cell(95, 6, 'Service To Party', 1, 1, 'C', 1)
    
    # Content Block (Names and Addresses)
    client_name = invoice_data.get('client_name', 'N/A')
    client_address = invoice_data.get('client_address', 'N/A')

    pdf.set_font('Arial', 'B', 8)
    pdf.set_x(10)
    pdf.cell(95, 4, f"Name: {client_name}", 'L,R', 0, 'L')
    pdf.cell(95, 4, f"Name: {client_name}", 'L,R', 1, 'L')
    
    pdf.set_font('Arial', '', 7)
    pdf.set_x(10)
    pdf.multi_cell(95, 3.5, f"Address: {client_address}", 'L,R', 'L')
    pdf.set_xy(105, y_start + 10)
    pdf.multi_cell(95, 3.5, f"Address: {client_address}", 'L,R', 'L')
    pdf.set_y(y_start + 25) 

    # 2. Project/Client Quick IDs and Billing Section (Code remains the same)
    y_start = pdf.get_y()
    pdf.set_font('Arial', 'B', 9)
    # ... (Detail rows and Bill To/Service To blocks) ...
    pdf.set_y(y_start + 25) 

    # 4. LINE ITEM TABLE
    pdf.set_x(10)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(15, 6, 'SR.NO.', 1, 0, 'C', 1)
    pdf.cell(125, 6, 'ITEM (Painting Work/Project Services)', 1, 0, 'L', 1)
    pdf.cell(25, 6, 'Rate Rs.', 1, 0, 'C', 1)
    pdf.cell(25, 6, 'Amount Rs.', 1, 1, 'R', 1)
    

    # Line Item 1
    pdf.set_font('Arial', '', 9)
    pdf.set_x(10)
    pdf.cell(15, 6, '01', 1, 0, 'C')
    pdf.cell(125, 6, 'General Project Services (See Project ID)', 1, 0, 'L')
    pdf.cell(25, 6, 'L.S.', 1, 0, 'C') 
    pdf.cell(25, 6, f"{bill_amount_num:.2f}", 1, 1, 'R')
    
    # Empty space (to match height)
    y_line_items_end = pdf.get_y()
    pdf.set_x(10)
    pdf.cell(190, 15, '', 1, 1, 'R') 
    pdf.ln(2)

    # 5. FINANCIAL SUMMARY AND BANK DETAILS (THE FIXED BLOCK)
    
    # Define constants
    summary_label_width = 50
    summary_value_width = 40
    summary_start_x = 110 # X position where the summary table begins
    bank_box_width = 90
    
    # Set starting Y position for both left (Bank) and right (Summary) blocks
    y_bank_start = pdf.get_y() # Define the variable here
    pdf.set_x(10)# Move up to align with the bottom of the Line Item Table

    # A. BANK DETAILS TABLE (Left side)
    
    pdf.set_font('Arial', 'B', 10) 
    pdf.cell(bank_box_width, 6, 'Bank Details:', 1, 1, 'L', 1) # Header
    
    pdf.set_font('Arial', '', 9)
    pdf.set_x(10)
    pdf.cell(bank_box_width, 6, 'Name: Apna Sahakari Bank Ltd', 1, 1, 'L', 0)
    pdf.set_x(10)
    pdf.cell(bank_box_width, 6, 'A/C: 014012xxxx177', 1, 1, 'L', 0)
    pdf.set_x(10)
    pdf.cell(bank_box_width, 6, 'IFSC: ASBI0000014', 1, 1, 'L', 0)
    pdf.set_x(10)
    pdf.cell(bank_box_width, 6, 'Terms & Conditions', 1, 1, 'L', 1)
    pdf.set_x(10)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(bank_box_width, 6, 'Payment within 7 days of submission of bill.', 1, 1, 'L', 0)
    

    # B. FINANCIAL SUMMARY TABLE (Right side)
    pdf.set_xy(summary_start_x, y_bank_start) # Reset Y position to start alignment

   # Row 1: Bill Amount Rs. (Net)
    pdf.set_fill_color(180, 200, 180) 
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(summary_label_width, 6, 'Bill Amount Rs.', 1, 0, 'L', 1)
    pdf.set_font('Arial', '', 9)
    pdf.cell(summary_value_width, 6, f"Rs. {bill_amount_num:.2f}", 1, 1, 'R', 1) # Now using bill_amount_num

    # Row 2: CGST
    pdf.set_x(summary_start_x)
    pdf.set_fill_color(255, 255, 255) 
    pdf.set_font('Arial', '', 9)
    pdf.cell(summary_label_width, 6, 'Add: CGST @9.00% Rs.', 1, 0, 'L', 0)
    pdf.cell(summary_value_width, 6, f"Rs. {tax_amount:.2f}", 1, 1, 'R', 0)
    
    # Row 3: SGST
    pdf.set_x(summary_start_x)
    pdf.cell(summary_label_width, 6, 'Add: SGST @9.00% Rs.', 1, 0, 'L', 0)
    pdf.cell(summary_value_width, 6, f"Rs. {tax_amount:.2f}", 1, 1, 'R', 0) 
    
    # Row 4: Total Tax Amount (Sum of CGST + SGST)
    pdf.set_x(summary_start_x)
    pdf.set_fill_color(180, 200, 180) 
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(summary_label_width, 6, 'Total Tax Amt. Rs.', 1, 0, 'L', 1)
    pdf.cell(summary_value_width, 6, f"Rs. {total_tax_amt:.2f}", 1, 1, 'R', 1) 

    # Row 5: Round Off Amount (0.00 for clean total)
    pdf.set_x(summary_start_x)
    pdf.set_fill_color(255, 255, 255) 
    pdf.set_font('Arial', '', 9)
    pdf.cell(summary_label_width, 6, 'Round Off Amt. Rs.', 1, 0, 'L', 0)
    pdf.cell(summary_value_width, 6, f"0.00", 1, 1, 'R', 0) 

    # Row 6: Total Bill Amt. With Tax (GRAND TOTAL)
    # Final Total Row
    pdf.set_x(summary_start_x)
    pdf.set_fill_color(180, 200, 180) 
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(summary_label_width, 6, 'Total Bill Amt. With Tax Rs.', 1, 0, 'L', 1)
    pdf.cell(summary_value_width, 6, f"Rs. {final_total:.2f}", 1, 1, 'R', 1) # Final total is calculated correctly

    # Row 7: AMOUNT PAID 
    pdf.set_x(summary_start_x)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(summary_label_width, 6, 'AMOUNT PAID', 1, 0, 'L', 0)
    pdf.cell(summary_value_width, 6, f"Rs. {amount_paid_num:.2f}", 1, 1, 'R', 0)
    
    # Row 8: Balance Due (Prominent)
    pdf.set_x(summary_start_x)
    pdf.set_fill_color(255, 230, 230) 
    pdf.cell(summary_label_width, 6, 'BALANCE DUE', 1, 0, 'L', 1)
    pdf.cell(summary_value_width, 6, f"Rs. {balance_due_num:.2f}", 1, 1, 'R', 1)

    pdf.set_y(pdf.get_y() + 10) 
    pdf.set_x(10)
    # Use the right side of the page (Total Width - Margin - Signature Width) for alignment
    signature_width = 70
    
    # Print the "For OM ENTERPRISES" line
    pdf.set_x(200 - signature_width - 10) # 200 (page width) - 70 (sig width) - 10 (margin) = 120
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(signature_width, 5, 'For OM ENTERPRISES', 0, 1, 'R') 
    
    # Print the "AUTHORISED SIGNATORY." line
    pdf.set_x(200 - signature_width - 10)
    pdf.cell(signature_width, 5, 'AUTHORISED SIGNATORY.', 0, 1, 'R')
    
    return pdf.output(dest='S').encode('latin1')

def add_existing_payments():
    """Adds existing payment data from the project document."""
    conn = get_db_connection()
    if conn is None:
        print("Cannot populate data: No database connection.")
        return False, "Database connection failed."
    cursor = conn.cursor()
    existing_payments = [
        ('PY_001', '1001', '2024-05-10 10:30:00', 160000.00, 'Bank Transfer', 'TRN123456789'),
    ]
    sql_insert = """
    INSERT INTO payments (payment_id, invoice_id, payment_date, amount, payment_method, transaction_id)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute("SELECT COUNT(*) FROM payments")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.executemany(sql_insert, existing_payments)
            conn.commit()
            print(f"Successfully added {cursor.rowcount} existing payments.")
        else:
            print("Payments table is not empty. Skipping population.")
        return True, "Existing payments processed."
    except mysql.connector.Error as err:
        conn.rollback()
        return False, str(err)
    finally:
        cursor.close()
        conn.close()

def get_all_payments():
    """Retrieves all payment records from the database."""
    conn = get_db_connection()
    if conn is None:
        return {'error': 'Database connection failed'}
    cursor = conn.cursor(dictionary=True)
    payments = []
    try:
        cursor.execute("SELECT * FROM payments")
        payments = cursor.fetchall()
        return {'payments': payments}
    except Exception as e:
        print(f"Logic Handler Error (get_all_payments): {e}")
        return {'error': 'Failed to retrieve payments.'}
    finally:
        cursor.close()
        conn.close()

def record_new_payment(payment_data):
    """Records a new payment record and saves it to the database."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."
    cursor = conn.cursor()
    try:
        sql_insert = """
        INSERT INTO payments (payment_id, transaction_id, invoice_id, payment_date, amount, payment_method)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            payment_data.get('payment_id'),
            payment_data.get('transaction_id'),
            payment_data.get('invoice_id'),
            payment_data.get('payment_date'),
            payment_data.get('amount'),
            payment_data.get('payment_method')
        )
        cursor.execute(sql_insert, values)
        conn.commit()
        return True, "Payment recorded successfully!"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def delete_payment(payment_id):
    """Handles the logic for deleting a payment."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."
    cursor = conn.cursor()
    sql_delete = "DELETE FROM payments WHERE payment_id = %s"
    try:
        cursor.execute(sql_delete, (payment_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Payment deleted successfully!"
        else:
            return False, "Payment not found."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def get_payment_details(payment_id):
    """Fetch details of a single payment."""
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed."

    cursor = conn.cursor(dictionary=True)
    try:
        sql_query = "SELECT * FROM payments WHERE payment_id = %s"
        cursor.execute(sql_query, (payment_id,))
        payment_data = cursor.fetchone()
        return payment_data, "Success"
    except Exception as e:
        print(f"Error fetching payment details: {e}")
        return None, str(e)
    finally:
        cursor.close()
        conn.close()


# -------------------- Generate PDF --------------------
class PDF(FPDF):
    def header(self):
        """Custom header with logo and gray line."""
        try:
            self.image("Logo.jpg", x=10, y=10, w=95)  # Company logo on top-left
        except:
            self.set_font("Arial", "B", 14)
            self.cell(0, 10, "Company Name", ln=True, align="L")

        self.set_y(40)
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.6)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(10)

    def footer(self):
        """Custom footer text."""
        self.set_y(-20)
        self.set_font("Arial", "I", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, "This is a system-generated receipt. No signature required.", 0, 1, "C")


def generate_payment_pdf(payment_data):
    """Generate a clean, professional payment receipt."""
    if not payment_data:
        return None

    pdf = PDF()
    pdf.add_page()

    # Title Section
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "PAYMENT RECEIPT", ln=True, align="C")
    pdf.set_draw_color(0, 77, 153)
    pdf.ln(15)

    # Receipt Info
    pdf.set_font("Arial", "", 12)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(0, 8, f"Receipt Date: {datetime.now().strftime('%d %B %Y')}", ln=True, fill=True)
    pdf.ln(5)

    # Details Table
    pdf.set_font("Arial", "", 12)
    pdf.cell(60, 10, "Payment ID:", 0, 0)
    pdf.cell(0, 10, payment_data["payment_id"], 0, 1)

    pdf.cell(60, 10, "Invoice ID:", 0, 0)
    pdf.cell(0, 10, payment_data["invoice_id"], 0, 1)

    pdf.cell(60, 10, "Payment Date:", 0, 0)
    pdf.cell(0, 10, str(payment_data["payment_date"]), 0, 1)

    pdf.cell(60, 10, "Payment Method:", 0, 0)
    pdf.cell(0, 10, payment_data.get("payment_method", "N/A"), 0, 1)

    pdf.cell(60, 10, "Transaction ID:", 0, 0)
    pdf.cell(0, 10, str(payment_data.get("transaction_id", "N/A")), 0, 1)

    pdf.cell(60, 10, "Amount Paid:", 0, 0)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0, 102, 0)
    pdf.cell(0, 10, f"Rs {float(payment_data['amount']):,.2f}", 0, 1)
    pdf.set_text_color(0, 0, 0)

    pdf.ln(8)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)

    # Thank you note
    pdf.set_font("Arial", "I", 12)
    pdf.multi_cell(
        0, 8,
        "Thank you for your payment.\n"
        "We appreciate your business and look forward to serving you again.\n\n"
        "For any billing-related queries, please contact:\n"
        "Email: gharatlaxman44@gmail.com | Phone: +91 9594105903"
    )

    pdf.ln(15)

    # Signature section
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, "Authorized Signature:", ln=True, align="R")
    pdf.line(130, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, "(Finance Department)", ln=True, align="R")

    # Output as binary data
    return pdf.output(dest='S').encode('latin1')

def get_all_services():
    """
    Retrieves all service records from the database using corrected case.
    """
    conn = get_db_connection()
    if conn is None:
        return {'error': 'Database connection failed'}

    cursor = conn.cursor(dictionary=True)
    services = []

    try:
        cursor.execute("SELECT service_id, service_name, unit_price FROM services")
        services = cursor.fetchall()
        return {'services': services}

    except Exception as e:
        print(f"Logic Handler Error (get_all_services): {e}")
        return {'error': 'Failed to retrieve services.'}
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

def add_new_service(service_data):
    """
    Handles the logic for adding a new service.
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    
    try:
        sql_insert = """
        INSERT INTO services (service_id, service_name, unit_price)
        VALUES (%s, %s, %s)
        """
        values = (
            service_data.get('service_id'),
            service_data.get('service_name'),
            service_data.get('unit_price'),
        )
        
        cursor.execute(sql_insert, values)
        conn.commit()
        return True, "Service added successfully!"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def delete_service(service_id):
    """
    Handles the logic for deleting a service.
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    sql_delete = "DELETE FROM services WHERE service_id = %s"
    
    try:
        cursor.execute(sql_delete, (service_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Service deleted successfully!"
        else:
            return False, "Service not found."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()
        
def add_existing_services():
    """Adds existing service data from the project document."""
    conn = get_db_connection()
    if conn is None:
        print("Cannot populate data: No database connection.")
        return False, "Database connection failed."

    cursor = conn.cursor()
    existing_services = [
        ('S001', 'Interior Painting', 25.00,),
    ]

    sql_insert = """
    INSERT INTO services (service_id, service_name, unit_price)
    VALUES (%s, %s, %s)
    """

    try:
        cursor.execute("SELECT COUNT(*) FROM services")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.executemany(sql_insert, existing_services)
            conn.commit()
            print(f"Successfully added {cursor.rowcount} existing services.")
        else:
            print("Services table is not empty. Skipping population.")
        return True, "Existing services processed."
    except mysql.connector.Error as err:
        conn.rollback()
        return False, str(err)
    finally:
        cursor.close()
        conn.close()

def add_existing_materials():
    """Adds existing material data from the project document."""
    conn = get_db_connection()
    if conn is None:
        print("Cannot populate data: No database connection.")
        return False, "Database connection failed."

    cursor = conn.cursor()

    # Existing material data from the project synopsis document
    existing_materials = [
        ('M001', 'Acrylic Emulsion', 'SP_001', 'Paints', 600.00, 'Liters', 150.00, 'Durable exterior paint with weather resistance.'),
    ]

    sql_insert = """
    INSERT INTO materials (material_id, material_name, supplier_id, manufacturer, unit_price, unit_of_measure, stock_quantity, description)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        # Check if the table is empty before populating
        cursor.execute("SELECT COUNT(*) FROM materials")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.executemany(sql_insert, existing_materials)
            conn.commit()
            print(f"Successfully added {cursor.rowcount} existing materials.")
        else:
            print("Materials table is not empty. Skipping population.")
        return True, "Existing materials processed."
    except mysql.connector.Error as err:
        conn.rollback()
        return False, str(err)
    finally:
        cursor.close()
        conn.close()

def get_all_materials():
    """Retrieves all material records from the database."""
    conn = get_db_connection()
    if conn is None:
        return {'error': 'Database connection failed'}

    cursor = conn.cursor(dictionary=True)
    materials = []

    try:
        cursor.execute("SELECT * FROM materials")
        materials = cursor.fetchall()
        return {'materials': materials}
    except Exception as e:
        print(f"Logic Handler Error (get_all_materials): {e}")
        return {'error': 'Failed to retrieve materials.'}
    finally:
        cursor.close()
        conn.close()

def add_new_material(material_data):
    """Handles the logic for adding a new material."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    
    try:
        sql_insert = """
        INSERT INTO materials (material_id, material_name, manufacturer, unit_price, stock_quantity, supplier_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            material_data.get('material_id'),
            material_data.get('material_name'),
            material_data.get('manufacturer'),
            material_data.get('unit_price'),
            material_data.get('stock_quantity'),
            material_data.get('supplier_id')
        )
        
        cursor.execute(sql_insert, values)
        conn.commit()
        return True, "Material added successfully!"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def delete_material(material_id):
    """Handles the logic for deleting a material."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    sql_delete = "DELETE FROM materials WHERE material_id = %s"
    
    try:
        cursor.execute(sql_delete, (material_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Material deleted successfully!"
        else:
            return False, "Material not found."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()
        
def get_material_details(material_id):
    """Fetches details of a single material to generate a PDF."""
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed."
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        sql_query = "SELECT * FROM materials WHERE material_id = %s"
        cursor.execute(sql_query, (material_id,))
        material_data = cursor.fetchone()
        
        # --- FIX: Ensure all numeric/date types are converted to strings ---
        if material_data:
            for key, value in material_data.items():
                if isinstance(value, (date, decimal.Decimal, int)): # Added 'int' to the conversion check
                    material_data[key] = str(value)
                elif value is None:
                    material_data[key] = 'N/A'
            
        return material_data, "Success"
    except Exception as e:
        print(f"Error fetching material details: {e}")
        return None, str(e)
    finally:
        cursor.close()
        conn.close()
        
def generate_material_pdf(material_data):
    """Generates a professional single-material PDF report."""
    if not material_data:
        return None

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(False)
    
    # --- COMPANY HEADER ---
    pdf.set_fill_color(0, 77, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 15, 'OM Enterprises', 0, 1, 'C', 1)
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, 'Material Inventory Profile', 0, 1, 'C', 0)
    pdf.ln(10)
    
    # --- MATERIAL IDENTIFICATION ---
    pdf.set_text_color(0, 0, 0)
    material_name = material_data.get('material_name', 'N/A')
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"MATERIAL: {material_name.upper()}", 0, 1, 'L')
    pdf.set_line_width(0.5)
    pdf.set_draw_color(0, 77, 153)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # --- DETAILS TABLE (Two Columns) ---
    
    # Define Column Widths
    col_widths = [50, 100]
    
    # Helper function for setting cell styles
    def print_detail_row(label, value, bold=False):
        # NOTE: The value passed here is already a string due to the fix in get_material_details
        pdf.set_font('Arial', 'B' if bold else '', 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(col_widths[0], 7, label, 1, 0, 'L', 1)
        pdf.set_font('Arial', '', 10)
        pdf.set_fill_color(255, 255, 255)
        pdf.cell(col_widths[1], 7, value, 1, 1, 'L', 0)

    # Data Rows
    # Use material_data.get() without string conversion here, as it's done in the fetch function
    print_detail_row('Material ID:', material_data.get('material_id', 'N/A'))
    print_detail_row('Material Name:', material_data.get('material_name', 'N/A'), bold=True)
    print_detail_row('Manufacturer:', material_data.get('manufacturer', 'N/A'))
    print_detail_row('Unit Price:', f"Rs. {material_data.get('unit_price', 'N/A')}")
    print_detail_row('Stock Quantity:', material_data.get('stock_quantity', 'N/A'), bold=True)
    print_detail_row('Supplier ID:', material_data.get('supplier_id', 'N/A'))

    pdf.ln(15)

    # --- FOOTER ---
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'Report Generated by CMS System', 0, 1, 'C')
    return pdf.output(dest='S').encode('latin1')

def get_all_materials_data():
    """Fetches all material records to generate a PDF."""
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed."

    cursor = conn.cursor(dictionary=True)

    try:
        sql_query = "SELECT * FROM materials"
        cursor.execute(sql_query)
        materials_data = cursor.fetchall()
        
        # --- FIX: Safe Type Conversion ---
        for material in materials_data:
            for key, value in material.items():
                if isinstance(value, (date, decimal.Decimal, int)): # Ensure all numeric types are covered
                    material[key] = str(value)
                elif value is None:
                    material[key] = 'N/A'
        # --- END FIX ---
        
        return materials_data, "Success"
    except Exception as e:
        print(f"Error fetching all material data: {e}")
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def generate_all_materials_pdf(materials_data):
    """Generates a single, professional PDF report for all materials."""
    if not materials_data:
        return None

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, margin=15)
    
    # --- GLOBAL HEADER ---
    pdf.set_fill_color(0, 77, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(0, 15, 'OM Enterprises', 0, 1, 'C', 1)
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 5, 'Comprehensive Material Inventory Report', 0, 1, 'C', 0)
    pdf.ln(10)
    
    pdf.set_text_color(0, 0, 0)
    
    # --- TABLE SETUP ---
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(220, 220, 220)
    
    # Define Column Widths
    col_widths = [15, 45, 30, 25, 25, 30] 
    
    # Table Headers
    pdf.cell(col_widths[0], 7, 'ID', 1, 0, 'C', 1)
    pdf.cell(col_widths[1], 7, 'Material Name', 1, 0, 'L', 1)
    pdf.cell(col_widths[2], 7, 'Manufacturer', 1, 0, 'L', 1)
    pdf.cell(col_widths[3], 7, 'Price (Rs)', 1, 0, 'R', 1)
    pdf.cell(col_widths[4], 7, 'Stock Qty', 1, 0, 'R', 1)
    pdf.cell(col_widths[5], 7, 'Supplier ID', 1, 1, 'L', 1)

    # --- TABLE BODY ---
    pdf.set_font('Arial', '', 8)
    pdf.set_fill_color(255, 255, 255)
    
    for material in materials_data:
        # Data conversion is handled in the fetching function
        pdf.cell(col_widths[0], 6, material.get('material_id', 'N/A'), 1, 0, 'C', 0)
        pdf.cell(col_widths[1], 6, material.get('material_name', 'N/A'), 1, 0, 'L', 0)
        pdf.cell(col_widths[2], 6, material.get('manufacturer', 'N/A'), 1, 0, 'L', 0)
        pdf.cell(col_widths[3], 6, f"Rs. {material.get('unit_price', '0.00')}", 1, 0, 'R', 0)
        pdf.cell(col_widths[4], 6, material.get('stock_quantity', '0'), 1, 0, 'R', 0)
        pdf.cell(col_widths[5], 6, material.get('supplier_id', 'N/A'), 1, 1, 'L', 0)
        
    pdf.ln(10)

    # --- FINAL FOOTER ---
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'Report Generated by CMS System', 0, 1, 'C')
    # FIX: Remove the redundant .encode('latin1')
    return pdf.output(dest='S').encode('latin1')

def get_employee_details(employee_id):
    """Fetches details of a single employee to generate a PDF."""
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed."
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        sql_query = "SELECT * FROM employees WHERE employee_id = %s"
        cursor.execute(sql_query, (employee_id,))
        employee_data = cursor.fetchone()
        return employee_data, "Success"
    except Exception as e:
        print(f"Error fetching employee details: {e}")
        return None, str(e)
    finally:
        cursor.close()
        conn.close()
        
def generate_employee_pdf(employee_data):
    """Generates an employee details PDF."""
    if not employee_data:
        return None

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Employee Details", ln=True, align="C")
    pdf.ln(10)
    
    # Safely access data, defaulting to 'N/A' if a key is missing
    pdf.cell(200, 10, txt=f"Employee ID: {employee_data.get('employee_id', 'N/A')}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"First Name: {employee_data.get('first_name', 'N/A')}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Last Name: {employee_data.get('last_name', 'N/A')}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Role: {employee_data.get('role', 'N/A')}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Contact Phone: {employee_data.get('contact_phone', 'N/A')}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Email: {employee_data.get('email', 'N/A')}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Hire Date: {employee_data.get('hire_date', 'N/A')}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Salary: {employee_data.get('salary', 'N/A')}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Status: {employee_data.get('status', 'N/A')}", ln=True, align="L")
    
    return pdf.output(dest='S').encode('latin1')


def verify_admin_credentials(username, password):
    """
    Verifies admin credentials against environment variables.
    
    :param username: The username provided by the admin.
    :param password: The password provided by the admin.
    :return: True if credentials are correct, False otherwise.
    """
    # Load environment variables from .env file
    # Make sure you have installed it: pip install python-dotenv
    load_dotenv()

    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if username == admin_username and password == admin_password:
        return True
    else:
        return False

def get_all_clients_data_for_report():
    conn = get_db_connection()
    if conn is None:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT client_id, client_name, contact_person, phone FROM clients")
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching client data for master report: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# Add this new function to get employee data for the master report
def get_all_employees_data_for_report():
    conn = get_db_connection()
    if conn is None:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT employee_id, first_name, last_name, role, status FROM employees")
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching employee data for master report: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def generate_master_pdf_report():
    """
    Generates a single, professional PDF report containing data from Clients, Projects, and Employees.
    """
    projects_data, msg_p = get_all_projects_data()
    clients_data = get_all_clients_data_for_report()
    employees_data = get_all_employees_data_for_report()

    pdf = FPDF()
    pdf.add_page()
    
    # --- GLOBAL HEADER ---
    pdf.set_fill_color(0, 77, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(0, 15, 'OM Enterprises', 0, 1, 'C', 1)
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 5, 'Comprehensive CMS Master Report', 0, 1, 'C', 0)
    pdf.ln(15)
    
    pdf.set_text_color(0, 0, 0)
    
    # --- 1. PROJECTS SECTION ---
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, '1. Projects Overview', 0, 1, 'L')
    pdf.set_line_width(0.4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    if projects_data:
        for project in projects_data:
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 6, f"  > {project.get('project_name', 'N/A')} ({project.get('project_id', 'N/A')})", 0, 1, 'L')
            
            pdf.set_font("Arial", '', 10)
            pdf.cell(5, 5, '', 0, 0) # Indent
            pdf.cell(60, 5, f"Client: {project.get('client_id', 'N/A')}", 0, 0)
            pdf.cell(60, 5, f"Status: {project.get('status', 'N/A')}", 0, 0)
            pdf.cell(0, 5, f"Value: Rs. {project.get('contract_value', '0.00')}", 0, 1)
            
            pdf.cell(5, 5, '', 0, 0) # Indent
            pdf.multi_cell(0, 5, f"Description: {project.get('description', 'N/A')[:50]}...", 0, 'L')
            pdf.ln(2)
    else:
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 5, 'No active project data found.', 0, 1, 'L')
    pdf.ln(10)
    
    # --- 2. CLIENTS SECTION ---
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, '2. Clients Summary', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    if clients_data:
        # Table Headers
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(20, 7, 'ID', 1, 0, 'C', 1)
        pdf.cell(50, 7, 'Name', 1, 0, 'L', 1)
        pdf.cell(40, 7, 'Contact Person', 1, 0, 'L', 1)
        pdf.cell(40, 7, 'Phone', 1, 1, 'L', 1)
        
        # Table Data
        pdf.set_font('Arial', '', 10)
        for client in clients_data:
            pdf.cell(20, 6, client.get('client_id', 'N/A'), 1, 0, 'C', 0)
            pdf.cell(50, 6, client.get('client_name', 'N/A'), 1, 0, 'L', 0)
            pdf.cell(40, 6, client.get('contact_person', 'N/A'), 1, 0, 'L', 0)
            pdf.cell(40, 6, client.get('phone', 'N/A'), 1, 1, 'L', 0)
    else:
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 5, 'No client data found.', 0, 1, 'L')
    pdf.ln(10)

    # --- 3. EMPLOYEES SECTION ---
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, '3. Employee Roster', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    if employees_data:
        # Table Headers
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(20, 7, 'ID', 1, 0, 'C', 1)
        pdf.cell(40, 7, 'Name', 1, 0, 'L', 1)
        pdf.cell(40, 7, 'Role', 1, 0, 'L', 1)
        pdf.cell(25, 7, 'Status', 1, 1, 'C', 1)
        
        # Table Data
        pdf.set_font('Arial', '', 10)
        for emp in employees_data:
            name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}"
            pdf.cell(20, 6, emp.get('employee_id', 'N/A'), 1, 0, 'C', 0)
            pdf.cell(40, 6, name, 1, 0, 'L', 0)
            pdf.cell(40, 6, emp.get('role', 'N/A'), 1, 0, 'L', 0)
            pdf.cell(25, 6, emp.get('status', 'N/A'), 1, 1, 'C', 0)
    else:
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 5, 'No employee data found.', 0, 1, 'L')

    # --- FINAL FOOTER ---
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'Report Generated by CMS System', 0, 1, 'C')

    return pdf.output(dest='S').encode('latin1')

def get_dashboard_counts():
    """
    Handles the logic for fetching dashboard counts, including detailed project status data (counts and names).
    """
    conn = get_db_connection()
    if conn is None:
        return {'error': 'Database connection failed'}

    cursor = conn.cursor()
    counts = {}

    try:
        # --- PRIMARY TOTAL COUNTS ---
        cursor.execute("SELECT COUNT(*) FROM Clients")
        counts['clients'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Projects")
        counts['projects'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Employees")
        counts['employees'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Invoices")
        counts['invoices'] = cursor.fetchone()[0]
        
        # --- NEW PROJECT STATUS COUNTS AND NAMES ---
        
        # Working Projects
        cursor.execute("SELECT COUNT(*), GROUP_CONCAT(project_name SEPARATOR '; ') FROM Projects WHERE status = 'Working'")
        working_result = cursor.fetchone()
        counts['projects_working'] = working_result[0]
        counts['projects_working_names'] = working_result[1] if working_result[1] else 'None'

        # Pending Projects
        cursor.execute("SELECT COUNT(*), GROUP_CONCAT(project_name SEPARATOR '; ') FROM Projects WHERE status = 'Pending'")
        pending_result = cursor.fetchone()
        counts['projects_pending'] = pending_result[0]
        counts['projects_pending_names'] = pending_result[1] if pending_result[1] else 'None'

        # Completed Projects
        cursor.execute("SELECT COUNT(*), GROUP_CONCAT(project_name SEPARATOR '; ') FROM Projects WHERE status = 'Completed'")
        completed_result = cursor.fetchone()
        counts['projects_completed'] = completed_result[0]
        counts['projects_completed_names'] = completed_result[1] if completed_result[1] else 'None'
        
        return counts
    except Exception as e:
        print(f"Logic Handler Error: {e}")
        return {'error': 'Failed to retrieve counts due to a query error.'}
    finally:
        cursor.close()
        conn.close()

# You can run this file directly to add the sample data
if __name__ == '__main__':
    add_existing_suppliers()