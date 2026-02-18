from flask import Flask, render_template, request, redirect, session, url_for, flash
import mysql.connector
import pandas as pd
import io
import re

app = Flask(__name__)
app.secret_key = "placement_secret"

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Dani@m13",
        database="placement_db",
        autocommit=True
    )

db = get_db_connection()
cursor = db.cursor(dictionary=True)

# Helper to ensure connection is alive
def check_conn():
    global db, cursor
    try:
        db.ping(reconnect=True, attempts=3, delay=1)
    except:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

# Auth decorator (essential for security)
def login_required(role=None):
    def wrapper(f):
        def wrapped(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('login'))
            if role and session['user']['role'] != role:
                return "Unauthorized Access", 403
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return wrapper

# Login Page
@app.route('/')
def login():
    if 'user' in session:
        return redirect(url_for('admin_dashboard') if session['user']['role'] == 'admin' else url_for('student_dashboard'))
    return render_template("login.html")

# Login Logic
@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']

    if not cursor:
        return "Database connection error. Please check your MySQL setup.", 500

    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    user = cursor.fetchone()

    if user:
        session['user'] = user
        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    else:
        return "Invalid Login Credentials", 401

# Admin Dashboard
@app.route('/admin')
@login_required(role='admin')
def admin_dashboard():
    check_conn()
    # Fetch some stats for the dashboard
    cursor.execute("SELECT COUNT(*) as count FROM students")
    total_students = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM companies")
    total_companies = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(DISTINCT s.student_id) as count FROM students s JOIN offers o ON s.student_id = o.student_id WHERE o.status='Selected'")
    placed_students = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM offers WHERE status='Interview'")
    ongoing_interviews = cursor.fetchone()['count']
    
    # Fetch recent activities
    # 1. Recent Companies
    cursor.execute("SELECT company_name, offer_role, DATE_FORMAT(created_at, '%b %d') as date FROM companies ORDER BY created_at DESC LIMIT 5")
    recent_companies = cursor.fetchall()

    # 2. Recent Applications
    cursor.execute("""
        SELECT s.name as student_name, c.company_name, DATE_FORMAT(o.applied_at, '%b %d') as date 
        FROM offers o 
        JOIN students s ON o.student_id = s.student_id 
        JOIN companies c ON o.company_id = c.company_id 
        ORDER BY o.applied_at DESC LIMIT 5
    """)
    recent_apps = cursor.fetchall()

    # 3. Recent Placements
    cursor.execute("""
        SELECT s.name as student_name, c.company_name, DATE_FORMAT(o.updated_at, '%b %d') as date 
        FROM offers o 
        JOIN students s ON o.student_id = s.student_id 
        JOIN companies c ON o.company_id = c.company_id 
        WHERE o.status = 'Selected'
        ORDER BY o.updated_at DESC LIMIT 5
    """)
    recent_placements = cursor.fetchall()
    
    return render_template("admin.html", 
                         total_students=total_students, 
                         total_companies=total_companies, 
                         placed_students=placed_students,
                         ongoing_interviews=ongoing_interviews,
                         recent_companies=recent_companies,
                         recent_apps=recent_apps,
                         recent_placements=recent_placements)

# Admin - Students List
@app.route('/admin/students')
@login_required(role='admin')
def admin_students():
    check_conn()
    search = request.args.get('search', '').strip()
    dept_filter = request.args.get('department', '').strip()
    status_filter = request.args.get('filter', '').strip()
    
    base_query = """
        SELECT s.*, 
        EXISTS(SELECT 1 FROM offers o WHERE o.student_id = s.student_id AND o.status = 'Selected') as is_placed,
        (SELECT COUNT(*) FROM offers o WHERE o.student_id = s.student_id AND o.status = 'Interview') as interview_count
        FROM students s
    """
    
    conditions = []
    params = []
    
    if search:
        conditions.append("(s.name LIKE %s OR s.email LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])
        
    if dept_filter:
        conditions.append("s.department = %s")
        params.append(dept_filter)
        
    query = base_query
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    if status_filter == 'placed':
        query = f"SELECT * FROM ({query}) as sub WHERE is_placed = 1"
    elif status_filter == 'unplaced':
        query = f"SELECT * FROM ({query}) as sub WHERE is_placed = 0"
        
    query += " ORDER BY name ASC"
    
    cursor.execute(query, tuple(params))
    students = cursor.fetchall()
    
    return render_template("admin_students.html", 
                         students=students, 
                         current_filter=status_filter,
                         search=search,
                         dept_filter=dept_filter)

# Admin - Companies List
@app.route('/companies')
@login_required(role='admin')
def admin_companies():
    check_conn()
    search = request.args.get('search', '').strip()
    
    query = "SELECT * FROM companies"
    params = []
    
    if search:
        query += " WHERE company_name LIKE %s"
        params.append(f"%{search}%")
        
    query += " ORDER BY company_name ASC"
    cursor.execute(query, tuple(params))
    companies = cursor.fetchall()
    return render_template("companies.html", companies=companies, search=search)

# Admin - Job Offers
@app.route('/admin/jobs')
@login_required(role='admin')
def admin_jobs():
    check_conn()
    status_filter = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()
    
    query = """
        SELECT o.offer_id, s.name as student_name, c.company_name, o.status, DATE_FORMAT(o.applied_at, '%b %d, %Y') as applied_date
        FROM offers o
        JOIN students s ON o.student_id = s.student_id
        JOIN companies c ON o.company_id = c.company_id
    """
    
    conditions = []
    params = []
    
    if status_filter:
        conditions.append("o.status = %s")
        params.append(status_filter)
        
    if search:
        conditions.append("(s.name LIKE %s OR c.company_name LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += " ORDER BY o.applied_at DESC"
    cursor.execute(query, tuple(params))
        
    offers = cursor.fetchall()
    return render_template("admin_jobs.html", offers=offers, current_filter=status_filter, search=search)

@app.route('/add_company', methods=['POST'])
@login_required(role='admin')
def add_company():
    check_conn()
    company_name = request.form['company_name']
    offer_role = request.form['offer_role']
    work_location = request.form['work_location']
    package_lpa = request.form['package_lpa']

    cursor.execute(
        "INSERT INTO companies (company_name, offer_role, work_location, package_lpa) VALUES (%s, %s, %s, %s)",
        (company_name, offer_role, work_location, package_lpa)
    )
    db.commit()
    flash('Company added successfully!', 'success')
    return redirect(url_for('admin_companies'))

@app.route('/delete_company/<int:company_id>')
@login_required(role='admin')
def delete_company(company_id):
    check_conn()
    # Note: This might fail if there are foreign key constraints from 'offers'
    try:
        cursor.execute("DELETE FROM companies WHERE company_id=%s", (company_id,))
        db.commit()
        flash('Company deleted successfully!', 'success')
    except Exception as e:
        print(f"Error deleting company: {e}")
        flash('Could not delete company. It might be linked to existing offers.', 'error')
    return redirect(url_for('admin_companies'))

# Add Student
@app.route('/add_student', methods=['POST'])
@login_required(role='admin')
def add_student():
    name = request.form['name']
    email = request.form['email']
    department = request.form['department']
    cgpa = request.form['cgpa']
    arrears = request.form.get('arrears', 0)

    cursor.execute(
        "INSERT INTO students (name, email, department, cgpa, arrears) VALUES (%s, %s, %s, %s, %s)",
        (name, email, department, cgpa, arrears)
    )
    db.commit()
    flash('Student added successfully!', 'success')
    return redirect(url_for('admin_students'))

# Delete Student
@app.route('/delete_student/<int:student_id>')
@login_required(role='admin')
def delete_student(student_id):
    check_conn()
    cursor.execute("DELETE FROM students WHERE student_id=%s", (student_id,))
    db.commit()
    flash('Student record deleted successfully!', 'success')
    return redirect(url_for('admin_students'))

# --- Company Excel Import ---

@app.route('/admin/import_companies', methods=['POST'])
@login_required(role='admin')
def import_companies():
    if 'excel_file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('admin_companies'))
    
    file = request.files['excel_file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('admin_companies'))

    try:
        df = pd.read_excel(file)
        # Required columns for companies
        required_cols = ['company_name', 'offer_role', 'work_location', 'package_lpa']
        df.columns = [c.lower().strip().replace(' ', '_') for c in df.columns]
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            flash(f"Missing required columns: {', '.join(missing_cols)}", 'error')
            return redirect(url_for('admin_companies'))

        preview_data = []
        for _, row in df.iterrows():
            record = {
                'company_name': str(row['company_name']).strip() if pd.notnull(row['company_name']) else None,
                'offer_role': str(row['offer_role']).strip() if pd.notnull(row['offer_role']) else None,
                'work_location': str(row['work_location']).strip() if pd.notnull(row['work_location']) else None,
                'package_lpa': row['package_lpa'],
                'errors': []
            }
            
            if not record['company_name']: record['errors'].append("Company name is required")
            if not record['offer_role']: record['errors'].append("Role is required")
            if pd.isnull(record['package_lpa']): record['errors'].append("Package is required")
            
            try:
                record['package_lpa'] = float(record['package_lpa'])
            except:
                if record['package_lpa']: record['errors'].append("Package must be a number")

            preview_data.append(record)

        session['pending_company_import'] = preview_data
        has_errors = any(r['errors'] for r in preview_data)
        
        return render_template("admin_company_import_preview.html", 
                             preview_data=preview_data, 
                             has_errors=has_errors)

    except Exception as e:
        flash(f"Failed to process file: {str(e)}", 'error')
        return redirect(url_for('admin_companies'))

@app.route('/admin/save_company_import', methods=['POST'])
@login_required(role='admin')
def save_imported_companies():
    names = request.form.getlist('company_name')
    roles = request.form.getlist('offer_role')
    locations = request.form.getlist('work_location')
    packages = request.form.getlist('package_lpa')

    all_records = []
    if names:
        for i in range(len(names)):
            all_records.append({
                'company_name': names[i],
                'offer_role': roles[i],
                'work_location': locations[i],
                'package_lpa': packages[i]
            })
    else:
        all_records = session.get('pending_company_import', [])

    if not all_records:
        flash('No data to import', 'error')
        return redirect(url_for('admin_companies'))
    
    check_conn()
    inserted_count = 0
    for rec in all_records:
        name = str(rec.get('company_name', '')).strip()
        role = str(rec.get('offer_role', '')).strip()
        loc = str(rec.get('work_location', '')).strip()
        pkg = rec.get('package_lpa')

        if not name or not role:
            continue

        try:
            cursor.execute(
                "INSERT INTO companies (company_name, offer_role, work_location, package_lpa) VALUES (%s, %s, %s, %s)",
                (name, role, loc, pkg)
            )
            inserted_count += 1
        except:
            continue

    db.commit()
    session.pop('pending_company_import', None)
    flash(f"Successfully imported {inserted_count} companies!", 'success')
    return redirect(url_for('admin_companies'))

# --- Excel Import Functionality ---

@app.route('/admin/import_students', methods=['POST'])
@login_required(role='admin')
def import_students():
    if 'excel_file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('admin_students'))
    
    file = request.files['excel_file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('admin_students'))

    try:
        # Read the Excel file
        df = pd.read_excel(file)
        
        # Required columns check
        required_cols = ['name', 'email', 'department', 'cgpa']
        # Convert columns to lowercase for flexible matching
        df.columns = [c.lower().strip() for c in df.columns]
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            flash(f"Missing required columns: {', '.join(missing_cols)}", 'error')
            return redirect(url_for('admin_students'))

        check_conn()
        # Fetch existing emails to check duplicates
        cursor.execute("SELECT email FROM students")
        existing_emails = {row['email'].lower() for row in cursor.fetchall()}
        
        preview_data = []
        valid_records = []
        
        allowed_depts = ['CSE', 'ECS', 'AIDS', 'CS']

        for _, row in df.iterrows():
            record = {
                'name': str(row['name']).strip() if pd.notnull(row['name']) else None,
                'email': str(row['email']).strip().lower() if pd.notnull(row['email']) else None,
                'department': str(row['department']).strip().upper() if pd.notnull(row['department']) else None,
                'cgpa': row['cgpa'],
                'arrears': row.get('arrears', 0),
                'errors': []
            }
            
            # 1. Null Checks
            if not record['name']: record['errors'].append("Name is required")
            if not record['email']: record['errors'].append("Email is required")
            if not record['department']: record['errors'].append("Department is required")
            if pd.isnull(record['cgpa']): record['errors'].append("CGPA is required")
            
            # 2. Duplicate Check
            if record['email'] in existing_emails:
                record['errors'].append("Email already exists in database")
            
            # 3. Type/Format Checks
            if record['email'] and not re.match(r"[^@]+@[^@]+\.[^@]+", record['email']):
                record['errors'].append("Invalid email format")
            
            if record['department'] and record['department'] not in allowed_depts:
                record['errors'].append(f"Invalid Department. Must be one of: {', '.join(allowed_depts)}")
            
            try:
                cgpa_val = float(record['cgpa'])
                if not (0 <= cgpa_val <= 10):
                    record['errors'].append("CGPA must be between 0 and 10")
                record['cgpa'] = cgpa_val
            except (ValueError, TypeError):
                if not pd.isnull(record['cgpa']):
                    record['errors'].append("CGPA must be a number")

            try:
                arrears_val = int(record['arrears']) if pd.notnull(record['arrears']) else 0
                record['arrears'] = arrears_val
            except (ValueError, TypeError):
                record['errors'].append("Arrears must be a number")

            preview_data.append(record)
            if not record['errors']:
                valid_records.append({
                    'name': record['name'],
                    'email': record['email'],
                    'department': record['department'],
                    'cgpa': record['cgpa'],
                    'arrears': record['arrears']
                })

        # Prepare records for session: if a field has an error, it will be nulled during save
        # but for the preview, we keep them as is.
        session['pending_import'] = preview_data
        
        has_errors = any(r['errors'] for r in preview_data)
        
        return render_template("admin_import_preview.html", 
                             preview_data=preview_data, 
                             has_errors=has_errors)

    except Exception as e:
        print(f"Import Error: {e}")
        flash(f"Failed to process file: {str(e)}", 'error')
        return redirect(url_for('admin_students'))

@app.route('/admin/save_import', methods=['POST'])
@login_required(role='admin')
def save_imported_students():
    # Priority: Read from form (editable preview), fallback to session
    names = request.form.getlist('name')
    emails = request.form.getlist('email')
    depts = request.form.getlist('department')
    cgpas = request.form.getlist('cgpa')
    arrears_list = request.form.getlist('arrears')

    all_records = []
    if names:
        # Construct records from form data
        for i in range(len(names)):
            all_records.append({
                'name': names[i],
                'email': emails[i],
                'department': depts[i],
                'cgpa': cgpas[i],
                'arrears': arrears_list[i] if i < len(arrears_list) else 0
            })
    else:
        all_records = session.get('pending_import', [])

    if not all_records:
        flash('No data to import', 'error')
        return redirect(url_for('admin_students'))
    
    check_conn()
    inserted_count = 0
    records_to_correct = []
    
    allowed_depts = ['CSE', 'ECS', 'AIDS', 'CS']
    
    # Pre-fetch existing emails for duplicate check during processing
    cursor.execute("SELECT email FROM students")
    existing_emails = {row['email'].lower() for row in cursor.fetchall()}

    for rec in all_records:
        # 1. Define Required Fields
        name = str(rec.get('name', '')).strip()
        email = str(rec.get('email', '')).strip().lower()
        
        # 2. Check if record can be inserted at all (Required Check)
        is_duplicate = email in existing_emails if email else False
        is_invalid_email = not re.match(r"[^@]+@[^@]+\.[^@]+", str(email)) if email else True
        
        # If required fields are missing OR email is invalid/duplicate, it's a CORRECTION case
        if not name or not email or is_invalid_email or is_duplicate:
            # Attach specific error if it was a duplicate for UI feedback
            if is_duplicate: rec['errors'] = ["Email already exists"]
            records_to_correct.append(rec)
            continue

        # 3. Handle Optional Fields (Nullify if invalid)
        dept = str(rec.get('department', '')).upper().strip()
        if dept not in allowed_depts:
            dept = None
            
        cgpa = rec.get('cgpa')
        try:
            if cgpa is not None:
                cgpa_val = float(cgpa)
                if not (0 <= cgpa_val <= 10):
                    cgpa = None
                else:
                    cgpa = cgpa_val
            else:
                cgpa = None
        except:
            cgpa = None

        arrears = rec.get('arrears')
        try:
            arrears = int(arrears) if arrears is not None else 0
        except:
            arrears = 0

        try:
            cursor.execute(
                "INSERT INTO students (name, email, department, cgpa, arrears) VALUES (%s, %s, %s, %s, %s)",
                (name, email, dept, cgpa, arrears)
            )
            inserted_count += 1
            existing_emails.add(email) # Track newly added emails
        except Exception as e:
            print(f"Insertion fail: {e}")
            records_to_correct.append(rec)

    db.commit()
    session.pop('pending_import', None)
    
    if records_to_correct:
        session['records_to_correct'] = records_to_correct
        flash(f"Imported {inserted_count} records. {len(records_to_correct)} records need corrections.", 'warning')
        return redirect(url_for('import_correction'))
    
    flash(f"Successfully imported all {inserted_count} records!", 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/import_correction', methods=['GET', 'POST'])
@login_required(role='admin')
def import_correction():
    if request.method == 'POST':
        # Process the manually corrected data
        names = request.form.getlist('name')
        emails = request.form.getlist('email')
        depts = request.form.getlist('department')
        cgpas = request.form.getlist('cgpa')
        arrears_list = request.form.getlist('arrears')
        
        check_conn()
        corrected_count = 0
        still_errors = []
        
        allowed_depts = ['CSE', 'ECS', 'AIDS', 'CS']
        
        for i in range(len(names)):
            name = names[i].strip()
            email = emails[i].strip().lower()
            dept = depts[i].strip().upper()
            cgpa = cgpas[i]
            arrears = arrears_list[i] if i < len(arrears_list) else 0
            
            # Validation
            errors = []
            if not name: errors.append("Name required")
            if not email: errors.append("Email required")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email): errors.append("Invalid email")
            
            # Duplicate check
            cursor.execute("SELECT 1 FROM students WHERE email=%s", (email,))
            if cursor.fetchone(): errors.append("Email exists")

            if errors:
                still_errors.append({
                    'name': name, 'email': email, 'department': dept, 'cgpa': cgpa, 'arrears': arrears, 'errors': errors
                })
                continue
            
            # Optional field nullification
            final_dept = dept if dept in allowed_depts else None
            try:
                final_cgpa = float(cgpa) if 0 <= float(cgpa) <= 10 else None
            except:
                final_cgpa = None

            try:
                final_arrears = int(arrears) if arrears else 0
            except:
                final_arrears = 0
                
            cursor.execute(
                "INSERT INTO students (name, email, department, cgpa, arrears) VALUES (%s, %s, %s, %s, %s)",
                (name, email, final_dept, final_cgpa, final_arrears)
            )
            corrected_count += 1
            
        db.commit()
        if still_errors:
            session['records_to_correct'] = still_errors
            flash(f"Saved {corrected_count} records. {len(still_errors)} still have errors.", 'warning')
            return render_template("admin_import_correction.html", records=still_errors)
        
        session.pop('records_to_correct', None)
        flash(f"All {corrected_count} corrected records saved successfully!", 'success')
        return redirect(url_for('admin_students'))

    # GET request
    records = session.get('records_to_correct', [])
    if not records:
        return redirect(url_for('admin_students'))
    return render_template("admin_import_correction.html", records=records)

@app.route('/student')
@login_required(role='student')
def student_dashboard():
    student_id = session['user'].get('student_id')
    if not student_id:
         return render_template("student.html", data=[], stats={'total': 0, 'placed': 0, 'interviews': 0})

    cursor.execute("""
        SELECT c.company_name, c.offer_role, o.status, DATE_FORMAT(o.applied_at, '%b %d, %Y') as applied_date
        FROM offers o
        JOIN companies c ON o.company_id = c.company_id
        WHERE o.student_id = %s
        ORDER BY o.applied_at DESC
    """, (student_id,))
    data = cursor.fetchall()

    # Calculate stats
    stats = {
        'total': len(data),
        'placed': len([r for r in data if r['status'] == 'Selected']),
        'interviews': len([r for r in data if r['status'] == 'Interview'])
    }

    return render_template("student.html", data=data, stats=stats)

# Student Profile
@app.route('/student/profile')
@login_required(role='student')
def student_profile():
    student_id = session['user'].get('student_id')
    if not student_id:
        return "Student profiling not available for this user.", 404
    
    cursor.execute("SELECT * FROM students WHERE student_id=%s", (student_id,))
    student = cursor.fetchone()
    return render_template("student_profile.html", student=student)

# Student - Find Jobs
@app.route('/student/jobs')
@login_required(role='student')
def student_jobs():
    check_conn()
    student_id = session['user'].get('student_id')
    search_query = request.args.get('search', '')
    
    # Base query for companies and student's application status
    query = """
        SELECT c.*, o.status as app_status 
        FROM companies c 
        LEFT JOIN offers o ON c.company_id = o.company_id AND o.student_id = %s
    """
    params = [student_id]

    if search_query:
        # Implementing the specific search logic requested
        query += " WHERE c.company_name LIKE %s"
        params.append(f"%{search_query}%")
    
    cursor.execute(query, tuple(params))
    jobs = cursor.fetchall()
    
    # Fetch student's own arrears to check eligibility
    cursor.execute("SELECT arrears FROM students WHERE student_id = %s", (student_id,))
    student = cursor.fetchone()
    has_arrears = (student['arrears'] or 0) > 0 if student else False

    return render_template("student_jobs.html", jobs=jobs, search=search_query, has_arrears=has_arrears)

# Student - Apply for Job
@app.route('/apply/<int:company_id>', methods=['POST'])
@login_required(role='student')
def apply_job(company_id):
    student_id = session['user'].get('student_id')
    if not student_id:
        return "Student profile missing", 400

    # Check eligibility (Arrears check)
    cursor.execute("SELECT arrears FROM students WHERE student_id = %s", (student_id,))
    student = cursor.fetchone()
    if student and (student['arrears'] or 0) > 0:
        flash('You are not eligible for placement due to active arrears.', 'error')
        return redirect(url_for('student_jobs'))

    # Check if already applied
    cursor.execute("SELECT * FROM offers WHERE student_id=%s AND company_id=%s", (student_id, company_id))
    if cursor.fetchone():
        return "Already applied", 400

    # Insert pending application
    cursor.execute(
        "INSERT INTO offers (student_id, company_id, status) VALUES (%s, %s, 'Pending')",
        (student_id, company_id)
    )
    db.commit()
    flash('Application submitted successfully!', 'success')
    return redirect(url_for('student_jobs'))

@app.route('/admin/offers/update/<int:offer_id>/<string:status>')
@login_required(role='admin')
def update_offer_status(offer_id, status):
    check_conn()
    if status not in ['Selected', 'Rejected', 'Pending', 'Interview']:
        flash('Invalid status', 'error')
        return redirect(url_for('admin_jobs'))
    
    cursor.execute("UPDATE offers SET status=%s WHERE offer_id=%s", (status, offer_id))
    db.commit()
    flash(f'Offer status updated to {status}!', 'success')
    return redirect(url_for('admin_jobs'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
