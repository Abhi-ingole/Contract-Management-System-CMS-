from io import BytesIO
from flask import Flask, jsonify, request, render_template, Response, send_file, session, redirect, url_for
from functools import wraps
import os
from dotenv import load_dotenv
from datetime import datetime

from logic_handler import (
    generate_all_clients_pdf,
    generate_client_pdf,
    generate_master_pdf_report,
    get_all_clients_data,
    get_client_details,
    get_dashboard_counts,
    # Clients
    add_new_client, get_all_clients, delete_client,
    # Projects
    get_all_projects, add_new_project, delete_project, get_project_details, generate_project_pdf,
    get_all_projects_data, generate_all_projects_pdf,
    # Employees
    get_all_employees, add_new_employee, delete_employee, get_all_employees_data,
    generate_all_employees_pdf, get_employee_details, generate_employee_pdf,
    # Suppliers
    get_all_suppliers, add_new_supplier, delete_supplier, get_all_suppliers_data,
    generate_all_suppliers_pdf, get_supplier_details, generate_supplier_pdf,
    # Invoices
    get_all_invoices, generate_new_invoice, delete_invoice, get_invoice_details,
    generate_invoice_pdf,
    # Payments
    get_all_payments, record_new_payment, delete_payment, get_payment_details,
    generate_payment_pdf,
    # Services
    get_all_services, add_new_service, delete_service,
    # Materials
    get_all_materials, add_new_material, delete_material, get_material_details,
    generate_material_pdf, get_all_materials_data, generate_all_materials_pdf,
    # Login
    verify_admin_credentials
)

app = Flask(__name__, template_folder='templates', static_folder='static')

load_dotenv()
app.secret_key = os.getenv("SECRET_KEY") or "your_super_secret_key"

# Login Required Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# --- HTML Page Routes ---
@app.route('/')
@app.route('/index.html')
@login_required
def serve_index():
    return render_template('index.html')

@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/clients.html')
@login_required
def serve_clients():
    return render_template('clients.html')

@app.route('/projects.html')
@login_required
def serve_projects():
    return render_template('projects.html')

@app.route('/employees.html')
@login_required
def serve_employees():
    return render_template('employees.html')

@app.route('/invoices.html')
@login_required
def serve_invoices():
    return render_template('invoices.html')

@app.route('/payments.html')
@login_required
def serve_payments():
    return render_template('payments.html')

@app.route('/services.html')
@login_required
def serve_services():
    return render_template('services.html')

@app.route('/materials.html')
@login_required
def serve_materials():
    return render_template('materials.html')

@app.route('/suppliers.html')
@login_required
def serve_suppliers():
    return render_template('suppliers.html')
    
@app.route('/about.html')
def serve_about():
    return render_template('about.html')

# --- API Endpoints ---
# Login
@app.route('/api/login', methods=['POST'])
def login():
    credentials = request.get_json()
    username = credentials.get('username')
    password = credentials.get('password')

    if verify_admin_credentials(username, password):
        session['logged_in'] = True
        return jsonify({"success": True, "message": "Login successful"})
    else:
        return jsonify({"success": False, "message": "Invalid username or password"})
        
@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return jsonify({"success": True, "message": "Logged out successfully"})

# Dashboard
@app.route('/api/counts', methods=['GET'])
@login_required
def get_counts_api():
    counts = get_dashboard_counts()
    return jsonify(counts)

# Clients
@app.route('/api/clients', methods=['GET'])
@login_required
def get_clients_api():
    clients = get_all_clients()
    return jsonify(clients)

@app.route('/api/addClient', methods=['POST'])
@login_required
def handle_add_client():
    if not request.is_json:
        return jsonify({"success": False, "message": "Request must be JSON"}), 400
    
    data = request.get_json()
    success, message = add_new_client(data)
    
    if success:
        return jsonify({"success": True, "message": message}), 201
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route('/api/deleteClient/<client_id>', methods=['DELETE'])
@login_required
def delete_client_api(client_id):
    success, message = delete_client(client_id)
    if success:
        return jsonify({"success": True, "message": message}), 200
    else:
        return jsonify({"success": False, "message": message}), 500

# Projects
@app.route('/api/projects', methods=['GET'])
@login_required
def get_projects_api():
    projects = get_all_projects()
    return jsonify(projects)

@app.route('/api/addProject', methods=['POST'])
@login_required
def handle_add_project():
    if not request.is_json:
        return jsonify({"success": False, "message": "Request must be JSON"}), 400

    data = request.get_json()
    success, message = add_new_project(data)

    if success:
        return jsonify({"success": True, "message": message}), 201
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route('/api/deleteProject/<project_id>', methods=['DELETE'])
@login_required
def delete_project_api(project_id):
    success, message = delete_project(project_id)
    if success:
        return jsonify({"success": True, "message": message}), 200
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route('/api/downloadProject/<project_id>')
def download_project(project_id):
    project_data, message = get_project_details(project_id)
    if project_data:
        pdf_content = generate_project_pdf(project_data)
        if pdf_content:
            response = Response(pdf_content, mimetype='application/pdf')
            response.headers.set("Content-Disposition", "attachment", filename=f"project_report_{project_id}.pdf")
            return response
        return jsonify({"success": False, "message": "Failed to generate PDF."}), 500
    return jsonify({"success": False, "message": message}), 404

@app.route('/api/downloadAllProjects', methods=['GET'])
@login_required
def download_all_projects():
    projects_data, message = get_all_projects_data()
    if projects_data:
        pdf_content = generate_all_projects_pdf(projects_data)
        if pdf_content:
            response = Response(pdf_content, mimetype='application/pdf')
            response.headers.set("Content-Disposition", "attachment", filename=f"all_projects_report.pdf")
            return response
        return jsonify({"success": False, "message": "Failed to generate PDF."}), 500
    return jsonify({"success": False, "message": message}), 404



# Employees
@app.route('/api/employees', methods=['GET'])
@login_required
def get_employees_api():
    employees = get_all_employees()
    return jsonify(employees)

@app.route('/api/addEmployee', methods=['POST'])
@login_required
def handle_add_employee():
    if not request.is_json:
        return jsonify({"success": False, "message": "Request must be JSON"}), 400

    data = request.get_json()
    success, message = add_new_employee(data)

    if success:
        return jsonify({"success": True, "message": message}), 201
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route('/api/deleteEmployee/<employee_id>', methods=['DELETE'])
@login_required
def delete_employee_api(employee_id):
    success, message = delete_employee(employee_id)
    if success:
        return jsonify({"success": True, "message": message}), 200
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route('/api/downloadEmployee/<employee_id>')
@login_required
def download_employee(employee_id):
    employee_data, message = get_employee_details(employee_id)
    if employee_data:
        pdf_content = generate_employee_pdf(employee_data)
        if pdf_content:
            response = Response(pdf_content, mimetype='application/pdf')
            response.headers.set("Content-Disposition", "attachment", filename=f"employee_profile_{employee_id}.pdf")
            response.headers.set("Content-Length", len(pdf_content))
            return response
        return jsonify({"success": False, "message": "Failed to generate PDF."}), 500
    return jsonify({"success": False, "message": message}), 404

@app.route('/api/downloadAllEmployees', methods=['GET'])
@login_required
def download_all_employees():
    employees_data, message = get_all_employees_data()
    if employees_data:
        pdf_content = generate_all_employees_pdf(employees_data)
        if pdf_content:
            response = Response(pdf_content, mimetype='application/pdf')
            response.headers.set("Content-Disposition", "attachment", filename=f"Employee_Roster_{datetime.now().strftime('%Y%m%d')}.pdf")
            return response
        return jsonify({"success": False, "message": "Failed to generate PDF."}), 500
    return jsonify({"success": False, "message": message}), 404

# Suppliers
@app.route('/api/suppliers', methods=['GET'])
@login_required
def get_suppliers_api():
    suppliers = get_all_suppliers()
    return jsonify(suppliers)

@app.route('/api/addSupplier', methods=['POST'])
@login_required
def handle_add_supplier():
    if not request.is_json:
        return jsonify({"success": False, "message": "Request must be JSON"}), 400

    data = request.get_json()
    success, message = add_new_supplier(data)

    if success:
        return jsonify({"success": True, "message": message}), 201
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route('/api/deleteSupplier/<supplier_id>', methods=['DELETE'])
@login_required
def delete_supplier_api(supplier_id):
    success, message = delete_supplier(supplier_id)
    if success:
        return jsonify({"success": True, "message": message}), 200
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route('/api/downloadSupplier/<supplier_id>')
@login_required
def download_supplier(supplier_id):
    supplier_data, message = get_supplier_details(supplier_id)
    if supplier_data:
        pdf_content = generate_supplier_pdf(supplier_data)
        if pdf_content:
            response = Response(pdf_content, mimetype='application/pdf')
            response.headers.set("Content-Disposition", "attachment", filename=f"supplier_{supplier_id}.pdf")
            return response
        return jsonify({"success": False, "message": "Failed to generate PDF."}), 500
    return jsonify({"success": False, "message": message}), 404

@app.route('/api/downloadAllSuppliers', methods=['GET'])
@login_required
def download_all_suppliers():
    suppliers_data, message = get_all_suppliers_data()
    if suppliers_data:
        pdf_content = generate_all_suppliers_pdf(suppliers_data)
        if pdf_content:
            response = Response(pdf_content, mimetype='application/pdf')
            response.headers.set("Content-Disposition", "attachment", filename=f"all_suppliers_data.pdf")
            return response
        return jsonify({"success": False, "message": "Failed to generate PDF."}), 500
    return jsonify({"success": False, "message": message}), 404

# Invoices
@app.route('/api/invoices', methods=['GET'])
@login_required
def get_invoices_api():
    invoices = get_all_invoices()
    return jsonify(invoices)

@app.route('/api/generateInvoice', methods=['POST'])
@login_required
def handle_generate_invoice():
    if not request.is_json:
        return jsonify({"success": False, "message": "Request must be JSON"}), 400

    data = request.get_json()
    success, message = generate_new_invoice(data)

    if success:
        return jsonify({"success": True, "message": message}), 201
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route('/api/deleteInvoice/<invoice_id>', methods=['DELETE'])
@login_required
def delete_invoice_api(invoice_id):
    success, message = delete_invoice(invoice_id)
    if success:
        return jsonify({"success": True, "message": message}), 200
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route('/api/downloadInvoice/<invoice_id>')
@login_required
def download_invoice(invoice_id):
    invoice_data, message = get_invoice_details(invoice_id)
    if invoice_data:
        pdf_content = generate_invoice_pdf(invoice_data)
        if pdf_content:
            response = Response(pdf_content, mimetype='application/pdf')
            response.headers.set("Content-Disposition", "attachment", filename=f"invoice_{invoice_id}.pdf")
            return response
        return jsonify({"success": False, "message": "Failed to generate PDF."}), 500
    return jsonify({"success": False, "message": message}), 404

# Payments
@app.route('/api/payments', methods=['GET'])
@login_required
def get_payments_api():
    payments = get_all_payments()
    return jsonify(payments)

@app.route('/api/recordPayment', methods=['POST'])
@login_required
def handle_record_payment():
    if not request.is_json:
        return jsonify({"success": False, "message": "Request must be JSON"}), 400
    data = request.get_json()
    success, message = record_new_payment(data)
    if success:
        return jsonify({"success": True, "message": message}), 201
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route('/api/deletePayment/<payment_id>', methods=['DELETE'])
@login_required
def delete_payment_api(payment_id):
    success, message = delete_payment(payment_id)
    if success:
        return jsonify({"success": True, "message": message}), 200
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route('/api/downloadPayment/<payment_id>')
def download_payment(payment_id):
    """Download payment receipt as PDF."""
    payment_data, message = get_payment_details(payment_id)
    if not payment_data:
        return jsonify({"error": message}), 404

    pdf_data = generate_payment_pdf(payment_data)
    if not pdf_data:
        return jsonify({"error": "Failed to generate PDF"}), 500

    buffer = BytesIO(pdf_data)
    filename = f"PaymentReceipt_{payment_id}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

# Services
@app.route('/api/services', methods=['GET'])
@login_required
def get_services_api():
    services = get_all_services()
    return jsonify(services)

@app.route('/api/addService', methods=['POST'])
@login_required
def handle_add_service():
    if not request.is_json:
        return jsonify({"success": False, "message": "Request must be JSON"}), 400

    data = request.get_json()
    success, message = add_new_service(data)

    if success:
        return jsonify({"success": True, "message": message}), 201
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route('/api/deleteService/<service_id>', methods=['DELETE'])
@login_required
def delete_service_api(service_id):
    success, message = delete_service(service_id)
    if success:
        return jsonify({"success": True, "message": message}), 200
    else:
        return jsonify({"success": False, "message": message}), 500

# Materials
@app.route('/api/materials', methods=['GET'])
@login_required
def get_materials_api():
    materials = get_all_materials()
    return jsonify(materials)

@app.route('/api/addMaterial', methods=['POST'])
@login_required
def handle_add_material():
    if not request.is_json:
        return jsonify({"success": False, "message": "Request must be JSON"}), 400

    data = request.get_json()
    success, message = add_new_material(data)

    if success:
        return jsonify({"success": True, "message": message}), 201
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route('/api/deleteMaterial/<material_id>', methods=['DELETE'])
@login_required
def delete_material_api(material_id):
    success, message = delete_material(material_id)
    if success:
        return jsonify({"success": True, "message": message}), 200
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route('/api/downloadMaterial/<material_id>')
@login_required
def download_material(material_id):
    material_data, message = get_material_details(material_id)
    if material_data:
        pdf_content = generate_material_pdf(material_data)
        if pdf_content:
            response = Response(pdf_content, mimetype='application/pdf')
            response.headers.set("Content-Disposition", "attachment", filename=f"material_{material_id}.pdf")
            return response
        return jsonify({"success": False, "message": "Failed to generate PDF."}), 500
    return jsonify({"success": False, "message": message}), 404

@app.route('/api/downloadAllMaterials', methods=['GET'])
@login_required
def download_all_materials():
    materials_data, message = get_all_materials_data()
    if materials_data:
        pdf_content = generate_all_materials_pdf(materials_data)
        if pdf_content:
            response = Response(pdf_content, mimetype='application/pdf')
            response.headers.set("Content-Disposition", "attachment", filename=f"all_materials_data.pdf")
            return response
        return jsonify({"success": False, "message": "Failed to generate PDF."}), 500
    return jsonify({"success": False, "message": message}), 404


@app.route('/living')
def living():
    return render_template('living.html')

@app.route('/dining-room.html')
def dining():
    """Renders the single-page SVG Visualizer application."""
    # We use render_template_string because all HTML/CSS/JS is inline
    return render_template('dining-room.html')

@app.route('/kitchen-room.html')
def kitchen():
    return render_template('kitchen-room.html')

@app.route('/masterbed-room.html')
def masterbed():
    return render_template('masterbed-room.html')

@app.route('/kidsbed-room.html')
def kidsbed():
    return render_template('kidsbed-room.html')

@app.route('/guestbed-room.html')
def guestbed():
    return render_template('guestbed-room.html')

@app.route('/api/downloadMasterReport', methods=['GET'])
@login_required
def download_master_report():
    pdf_content = generate_master_pdf_report()
    if pdf_content:
        response = Response(pdf_content, mimetype='application/pdf')
        response.headers.set("Content-Disposition", "attachment", filename="CMS_Master_Report.pdf")
        return response
    return jsonify({"success": False, "message": "Failed to generate PDF. Check if tables are empty."}), 500

@app.route('/api/downloadClient/<client_id>')
def download_client(client_id):
    client_data, message = get_client_details(client_id)
    if client_data:
        pdf_content = generate_client_pdf(client_data)
        if pdf_content:
            response = Response(pdf_content, mimetype='application/pdf')
            response.headers.set("Content-Disposition", "attachment", filename=f"client_profile_{client_id}.pdf")
            return response
        return jsonify({"success": False, "message": "Failed to generate PDF."}), 500
    return jsonify({"success": False, "message": message}), 404

# Route for downloading ALL clients' PDF
@app.route('/api/downloadAllClients', methods=['GET'])
def download_all_clients():
    clients_data, message = get_all_clients_data()
    if clients_data:
        pdf_content = generate_all_clients_pdf(clients_data)
        if pdf_content:
            response = Response(pdf_content, mimetype='application/pdf')
            response.headers.set("Content-Disposition", "attachment", filename=f"client_roster_report.pdf")
            return response
        return jsonify({"success": False, "message": "Failed to generate PDF."}), 500
    return jsonify({"success": False, "message": message}), 404




if __name__ == '__main__':
    app.run(debug=True)


