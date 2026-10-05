import os
import csv
import io
import psycopg2
import psycopg2.extras
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, jsonify
from dotenv import load_dotenv
from google import genai
import csv
from io import StringIO
from flask import Response, make_response


from flask import send_from_directory

# --- PWA Routes ---
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    response = send_from_directory('static', 'sw.js')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


# 1. SABSE PEHLE .env file load karni hai
load_dotenv()

# 2. USKE BAAD Gemini AI setup karna hai (taaki os.getenv ko key mil sake)
ai_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

# 3. Flask App Setup
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    return psycopg2.connect(db_url)

# Security Lock: Bina login ke koi page nahi khulega
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'school_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Har page par logged-in school ka naam bhejne ke liye
@app.context_processor
def inject_school():
    if 'school_id' in session:
        return dict(current_school={
            'id': session['school_id'],
            'code': session['school_code'],
            'name': session['school_name']
        })
    return dict(current_school=None)

# ================= 1. LOGIN SYSTEM =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Agar pehle se login hai, toh check karo Admin hai ya Normal School
    if 'school_id' in session:
        if session.get('is_admin'):
            return redirect(url_for('master_admin'))
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        school_code = request.form.get('school_code')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM schools WHERE school_code = %s AND password = %s", (school_code, password))
        school = cursor.fetchone()
        cursor.close()
        conn.close()

        if school:
            # Session mein user details save karein
            session['school_id'] = school['school_id']
            session['school_code'] = school['school_code']
            session['school_name'] = school['school_name']
            
            # Database se check karein ki kya yeh Admin hai
            session['is_admin'] = school.get('is_admin', False) 

            # Redirect Logic: Admin ko master-admin par bhejo, baki schools ko dashboard par
            if session['is_admin']:
                return redirect(url_for('master_admin'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash("Invalid School Code or Password!", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ================= 2. DASHBOARD =================
@app.route('/')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    school_id = session['school_id']

    # 1. Total Students Count
    cursor.execute("SELECT COUNT(*) AS total FROM students WHERE school_id = %s;", (school_id,))
    total_students = cursor.fetchone()['total']

    # 2. Total Active Classes Count
    cursor.execute("SELECT COUNT(DISTINCT class_name) AS classes FROM students WHERE school_id = %s;", (school_id,))
    total_classes = cursor.fetchone()['classes']

    # 3. Recent 5 Admissions
    cursor.execute("""
        SELECT name, class_name, roll_no, gender 
        FROM students 
        WHERE school_id = %s 
        ORDER BY student_id DESC LIMIT 5;
    """, (school_id,))
    recent_students = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return render_template('dashboard.html', active_page='dashboard', 
                           total_students=total_students, 
                           total_classes=total_classes,
                           recent_students=recent_students)

# ================= 3. STUDENTS DIRECTORY =================
@app.route('/students')
@login_required
def students_page():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("""
        SELECT * FROM students 
        WHERE school_id = %s 
        ORDER BY class_name, roll_no ASC;
    """, (session['school_id'],))
    
    students_data = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('students.html', active_page='students', students=students_data)

@app.route('/students/create', methods=['POST'])
@login_required
def create_student():
    if request.method == 'POST':
        roll_no = request.form.get('roll_no')
        name = request.form.get('name')
        gender = request.form.get('gender')
        class_name = request.form.get('class_name')
        father_name = request.form.get('father_name')
        mother_name = request.form.get('mother_name')
        dob = request.form.get('dob')
        address = request.form.get('address')
        
        school_id = session['school_id']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO students (school_id, roll_no, name, gender, class_name, father_name, mother_name, dob, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (school_id, roll_no, name, gender, class_name, father_name, mother_name, dob, address))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()
            
        return redirect(url_for('students_page'))

@app.route('/students/<int:id>/delete', methods=['POST'])
@login_required
def delete_student(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM students WHERE student_id = %s AND school_id = %s;", (id, session['school_id']))
        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('students_page'))


# ==========================================
# UPDATE STUDENT RECORD ROUTE
# ==========================================
@app.route('/students/update', methods=['POST'])
@login_required
def update_student():
    student_id = request.form.get('student_id')
    name = request.form.get('name')
    roll_no = request.form.get('roll_no')
    class_name = request.form.get('class_name')
    gender = request.form.get('gender')
    father_name = request.form.get('father_name')
    mother_name = request.form.get('mother_name')
    dob = request.form.get('dob') or None
    address = request.form.get('address')
    school_id = session.get('school_id')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Database mein student ka record update karne ki query
        cur.execute("""
            UPDATE students 
            SET name=%s, roll_no=%s, class_name=%s, gender=%s, father_name=%s, mother_name=%s, dob=%s, address=%s 
            WHERE student_id=%s AND school_id=%s
        """, (name, roll_no, class_name, gender, father_name, mother_name, dob, address, student_id, school_id))
        
        conn.commit()
        cur.close()
        conn.close()

        flash(f'Student {name} updated successfully!', 'success')
    except Exception as e:
        print("Error updating student:", e)
        flash('An error occurred while updating the student.', 'error')

    # Update hone ke baad wapas students page par bhej do
    return redirect('/students')

# ================= 4. MONTHLY ATTENDANCE =================
@app.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance_page():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    selected_class = request.args.get('class_name', 'Class 1')
    selected_month = request.args.get('month_name', 'August')
    academic_year = "2026-2027"

    cursor.execute("""
        SELECT * FROM students 
        WHERE school_id = %s AND class_name = %s 
        ORDER BY roll_no ASC;
    """, (session['school_id'], selected_class))
    students = cursor.fetchall()

    cursor.execute("""
        SELECT student_id, total_working_days, present_days 
        FROM monthly_attendance 
        WHERE school_id = %s AND month_name = %s AND academic_year = %s;
    """, (session['school_id'], selected_month, academic_year))
    
    saved_records = {row['student_id']: row for row in cursor.fetchall()}

    cursor.close()
    conn.close()

    return render_template('attendance.html', active_page='attendance', 
                           students=students, saved_records=saved_records, 
                           selected_class=selected_class, selected_month=selected_month)

@app.route('/attendance/save', methods=['POST'])
@login_required
def save_attendance():
    school_id = session['school_id']
    selected_class = request.form.get('class_name')
    selected_month = request.form.get('month_name')
    academic_year = "2026-2027"
    total_working_days = int(request.form.get('total_working_days', 25))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for key, value in request.form.items():
            if key.startswith('present_days_'):
                student_id = key.split('_')[2]
                present_days = int(value) if value else 0

                cursor.execute("""
                    INSERT INTO monthly_attendance (school_id, student_id, month_name, academic_year, total_working_days, present_days)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (student_id, month_name, academic_year) 
                    DO UPDATE SET total_working_days = EXCLUDED.total_working_days, present_days = EXCLUDED.present_days;
                """, (school_id, student_id, selected_month, academic_year, total_working_days, present_days))
        
        conn.commit()
        flash("Attendance saved successfully!", "success")
    except Exception as e:
        conn.rollback()
        print(f"Attendance Error: {e}")
        flash("Error saving attendance.", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('attendance_page', class_name=selected_class, month_name=selected_month))


#=============================================

# ==========================================
# 3. ROUTE: MAIN EXAM RESULTS PAGE
# ==========================================
@app.route('/results', methods=['GET'])
@login_required
def results_page():
    class_name = request.args.get('class_name', 'Class 1')
    exam_type = request.args.get('exam_type', 'Unit Test 1')
    student_id = request.args.get('student_id')
    
    # Force school_id to be a string to avoid PostgreSQL type errors
    school_id = str(session.get('school_id'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # 1. Safely fetch students using CAST
    cur.execute("""
        SELECT student_id, name, roll_no, class_name, father_name, mother_name, dob, gender 
        FROM students 
        WHERE class_name = %s AND CAST(school_id AS VARCHAR) = %s 
        ORDER BY roll_no
    """, (class_name, school_id))
    students = cur.fetchall()

    record = None
    student_profile = None
    if student_id:
        student_profile = next((s for s in students if str(s['student_id']) == str(student_id)), None)
        
        # 2. Safely fetch exam results using CAST
        cur.execute("""
            SELECT * FROM exam_results 
            WHERE CAST(student_id AS VARCHAR) = %s 
            AND exam_type = %s 
            AND CAST(school_id AS VARCHAR) = %s
        """, (str(student_id), exam_type, school_id))
        record = cur.fetchone()

    cur.close()
    conn.close()

    return render_template('results.html', 
                           active_page='results',
                           selected_class=class_name,
                           selected_exam=exam_type,
                           selected_student_id=student_id,
                           students=students,
                           record=record,
                           student_profile=student_profile)

# ==========================================
# 1. ROUTE: SAVE EXAM RESULTS
# ==========================================
@app.route('/results/save', methods=['POST'])
@login_required
def save_results():
    student_id = request.form.get('student_id')
    class_name = request.form.get('class_name')
    exam_type = request.form.get('exam_type')
    max_marks = int(request.form.get('max_marks', 100))
    school_id = session.get('school_id')

    hindi = float(request.form.get('hindi') or 0)
    english = float(request.form.get('english') or 0)
    math = float(request.form.get('math') or 0)
    evs = float(request.form.get('evs') or 0)
    sanskrit = float(request.form.get('sanskrit') or 0)
    computer = float(request.form.get('computer') or 0)
    art = float(request.form.get('art') or 0)
    gk = float(request.form.get('gk') or 0)

    total_marks = hindi + english + math + evs + sanskrit + computer + art + gk
    grand_max = max_marks * 8
    percentage = round((total_marks / grand_max) * 100, 1) if grand_max > 0 else 0

    if percentage >= 90: grade = 'A1'
    elif percentage >= 80: grade = 'A2'
    elif percentage >= 70: grade = 'B1'
    elif percentage >= 60: grade = 'B2'
    elif percentage >= 50: grade = 'C1'
    elif percentage >= 40: grade = 'C2'
    elif percentage >= 33: grade = 'D'
    else: grade = 'E'

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO exam_results 
            (student_id, school_id, class_name, exam_type, max_marks, hindi, english, math, evs, sanskrit, computer, art, gk, total_marks, percentage, grade)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (student_id, exam_type) 
            DO UPDATE SET 
                max_marks = EXCLUDED.max_marks, hindi = EXCLUDED.hindi, english = EXCLUDED.english, math = EXCLUDED.math, 
                evs = EXCLUDED.evs, sanskrit = EXCLUDED.sanskrit, computer = EXCLUDED.computer, 
                art = EXCLUDED.art, gk = EXCLUDED.gk, total_marks = EXCLUDED.total_marks, 
                percentage = EXCLUDED.percentage, grade = EXCLUDED.grade;
        """, (student_id, school_id, class_name, exam_type, max_marks, hindi, english, math, evs, sanskrit, computer, art, gk, total_marks, percentage, grade))
        
        conn.commit()
        cur.close()
        conn.close()
        flash('Marks saved successfully!', 'success')
    except Exception as e:
        print("Error saving results:", e)
        flash('Error saving marks to the database.', 'error')

    return redirect(f'/results?class_name={class_name}&exam_type={exam_type}&student_id={student_id}')


# ==========================================
# 2. ROUTE: EXPORT RESULTS TO EXCEL (CSV)
# ==========================================
@app.route('/results/export', methods=['GET'])
@login_required
def export_results():
    class_name = request.args.get('class_name')
    exam_type = request.args.get('exam_type')
    school_id = session.get('school_id')

    if not class_name or not exam_type:
        flash('Please select class and exam type first.', 'error')
        return redirect('/results')

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cur.execute("""
        SELECT s.roll_no, s.name, r.hindi, r.english, r.math, r.evs, 
               r.sanskrit, r.computer, r.art, r.gk, r.total_marks, r.percentage, r.grade
        FROM students s
        JOIN exam_results r ON s.student_id = r.student_id
        WHERE s.class_name = %s AND r.exam_type = %s AND s.school_id = %s
        ORDER BY s.roll_no;
    """, (class_name, exam_type, school_id))
    
    results = cur.fetchall()
    cur.close()
    conn.close()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Roll No', 'Student Name', 'Hindi', 'English', 'Math', 'EVS', 'Sanskrit', 'Computer', 'Art', 'GK', 'Total Marks', 'Percentage', 'Grade'])
    
    for r in results:
        cw.writerow([r['roll_no'], r['name'], r['hindi'], r['english'], r['math'], r['evs'], r['sanskrit'], r['computer'], r['art'], r['gk'], r['total_marks'], f"{r['percentage']}%", r['grade']])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={class_name}_{exam_type}_Results.csv"
    output.headers["Content-type"] = "text/csv"
    
    return output

# ==========================================
# 7. MATERIAL DISTRIBUTION MODULE
# ==========================================
@app.route('/distribution', methods=['GET', 'POST'])
@login_required
def distribution_page():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    selected_class = request.args.get('class_name', 'Class 1')
    academic_year = "2026-2027"

    # Fetch all students of the selected class
    cursor.execute("""
        SELECT * FROM students 
        WHERE school_id = %s AND class_name = %s 
        ORDER BY roll_no ASC;
    """, (session['school_id'], selected_class))
    students = cursor.fetchall()

    # Fetch existing distribution records for this class
    cursor.execute("""
        SELECT student_id, uniform_given, books_given, shoes_given, bag_given 
        FROM material_distribution 
        WHERE school_id = %s AND academic_year = %s;
    """, (session['school_id'], academic_year))
    
    saved_records = {row['student_id']: row for row in cursor.fetchall()}

    cursor.close()
    conn.close()

    return render_template('distribution.html', active_page='distribution', 
                           students=students, saved_records=saved_records, 
                           selected_class=selected_class)

@app.route('/distribution/save', methods=['POST'])
@login_required
def save_distribution():
    school_id = session['school_id']
    selected_class = request.form.get('class_name')
    academic_year = "2026-2027"

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get all student IDs from the form
        student_ids = request.form.getlist('student_ids')
        
        for s_id in student_ids:
            # Checkbox values: if checked it returns 'on', else None
            uniform = True if request.form.get(f'uniform_{s_id}') == 'on' else False
            books = True if request.form.get(f'books_{s_id}') == 'on' else False
            shoes = True if request.form.get(f'shoes_{s_id}') == 'on' else False
            bag = True if request.form.get(f'bag_{s_id}') == 'on' else False

            cursor.execute("""
                INSERT INTO material_distribution (school_id, student_id, academic_year, uniform_given, books_given, shoes_given, bag_given)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (student_id, academic_year) 
                DO UPDATE SET 
                    uniform_given = EXCLUDED.uniform_given, 
                    books_given = EXCLUDED.books_given, 
                    shoes_given = EXCLUDED.shoes_given, 
                    bag_given = EXCLUDED.bag_given;
            """, (school_id, s_id, academic_year, uniform, books, shoes, bag))
        
        conn.commit()
        flash("Material distribution updated successfully!", "success")
    except Exception as e:
        conn.rollback()
        print(f"Distribution Error: {e}")
        flash("Error saving records.", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('distribution_page', class_name=selected_class))

# ==========================================
# 8. MASTER ADMIN PANEL ROUTES
# ==========================================

@app.route('/master-admin')
def master_admin():
    # Check if user is logged in
    if 'school_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Check karein ki kya current user sach mein admin hai
    cursor.execute("SELECT is_admin FROM schools WHERE school_id = %s", (session['school_id'],))
    user = cursor.fetchone()
    
    if not user or not user.get('is_admin'):
        cursor.close()
        conn.close()
        flash('Access Denied: You are not an admin!', 'error')
        return redirect(url_for('dashboard')) 
        
    # Agar admin hai, toh saare normal schools ka data fetch karo
    cursor.execute("SELECT * FROM schools WHERE is_admin = FALSE ORDER BY created_at DESC")
    all_schools = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('master_admin.html', schools=all_schools)

@app.route('/master-admin/create-school', methods=['POST'])
def create_school():
    if 'school_id' not in session:
        return redirect(url_for('login'))
        
    school_name = request.form['school_name']
    school_code = request.form['school_code']
    email = request.form['email']
    password = request.form['password']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Naya school database mein insert karein
        cursor.execute("""
            INSERT INTO schools (school_name, school_code, email, password, is_admin)
            VALUES (%s, %s, %s, %s, FALSE)
        """, (school_name, school_code, email, password))
        
        conn.commit()
        flash(f'New School "{school_name}" created successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash('Error creating school. Email or Code might already exist.', 'error')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('master_admin'))

# ======== NEW ROUTES: EDIT & RESET PASSWORD ========

@app.route('/master-admin/edit-school/<int:school_id>', methods=['POST'])
def edit_school(school_id):
    if 'school_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    school_name = request.form['school_name']
    school_code = request.form['school_code']
    email = request.form['email']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE schools 
            SET school_name = %s, school_code = %s, email = %s 
            WHERE school_id = %s
        """, (school_name, school_code, email, school_id))
        conn.commit()
        flash('School details updated successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash('Error updating school. Code might already exist.', 'error')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('master_admin'))

@app.route('/master-admin/reset-password/<int:school_id>', methods=['POST'])
def reset_password(school_id):
    if 'school_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    new_password = request.form['new_password']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE schools SET password = %s WHERE school_id = %s", (new_password, school_id))
        conn.commit()
        flash('Password reset successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash('Error resetting password.', 'error')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('master_admin'))

# ======== ADMIN PROFILE SETTINGS ========

@app.route('/master-admin/update-profile', methods=['POST'])
def update_admin_profile():
    if 'school_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    new_username = request.form['username']
    new_password = request.form['password']
    admin_id = session['school_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Admin ka username aur password update karein
        cursor.execute("""
            UPDATE schools 
            SET school_code = %s, password = %s 
            WHERE school_id = %s AND is_admin = TRUE
        """, (new_username, new_password, admin_id))
        conn.commit()
        
        # Session mein bhi naya username update kar dein taaki turant dikhe
        session['school_code'] = new_username
        
        flash('Super Admin credentials updated successfully! Please remember your new login details.', 'success')
    except Exception as e:
        conn.rollback()
        flash('Error updating credentials. This username might already be taken.', 'error')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('master_admin'))


# ==========================================
# 9. STUDENT PROMOTION MODULE
# ==========================================

@app.route('/promotion', methods=['GET'])
@login_required
def promotion_page():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    selected_class = request.args.get('class_name', 'Class 1')

    # Source class ke saare bacchon ko fetch karein
    cursor.execute("""
        SELECT * FROM students 
        WHERE school_id = %s AND class_name = %s 
        ORDER BY roll_no ASC;
    """, (session['school_id'], selected_class))
    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('promotion.html', active_page='promotion', 
                           students=students, selected_class=selected_class)

@app.route('/promotion/execute', methods=['POST'])
@login_required
def execute_promotion():
    school_id = session['school_id']
    source_class = request.form.get('source_class')
    target_class = request.form.get('target_class')
    student_ids = request.form.getlist('student_ids')

    if not student_ids:
        flash("No students selected for promotion.", "error")
        return redirect(url_for('promotion_page', class_name=source_class))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Bacchon ki class update kar rahe hain
        cursor.execute("""
            UPDATE students 
            SET class_name = %s 
            WHERE school_id = %s AND student_id = ANY(%s::int[]);
        """, (target_class, school_id, [int(s) for s in student_ids]))

        conn.commit()
        flash(f"Successfully promoted {len(student_ids)} students to {target_class}!", "success")
    except Exception as e:
        conn.rollback()
        print(f"Promotion Error: {e}")
        flash("Error executing student promotion.", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('promotion_page', class_name=source_class))


@app.route('/analytics', methods=['GET'])
@login_required
def analytics_page():
    # Force school_id to be a string
    school_id = str(session.get('school_id'))
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        # 1. Total Students
        cur.execute("SELECT COUNT(*) FROM students WHERE CAST(school_id AS VARCHAR) = %s", (school_id,))
        total_students = cur.fetchone()[0] or 0

        # 2. Class Strength
        cur.execute("SELECT class_name, COUNT(*) as count FROM students WHERE CAST(school_id AS VARCHAR) = %s GROUP BY class_name ORDER BY class_name", (school_id,))
        class_strength = [dict(row) for row in cur.fetchall()]

        # 3. Gender Dist
        cur.execute("SELECT gender, COUNT(*) as count FROM students WHERE CAST(school_id AS VARCHAR) = %s GROUP BY gender", (school_id,))
        gender_dist = [dict(row) for row in cur.fetchall()]

        # 4. Avg Percentage (Fix applied here)
        cur.execute("SELECT AVG(percentage) FROM exam_results WHERE CAST(school_id AS VARCHAR) = %s", (school_id,))
        avg_percent_raw = cur.fetchone()[0]
        avg_percentage = round(float(avg_percent_raw), 1) if avg_percent_raw else 0

        # 5. Grade Dist
        cur.execute("SELECT grade, COUNT(*) as count FROM exam_results WHERE CAST(school_id AS VARCHAR) = %s GROUP BY grade ORDER BY grade", (school_id,))
        grade_dist = [dict(row) for row in cur.fetchall()]

        # 6. Avg Attendance (Safe Fallback)
        try:
            cur.execute("SELECT AVG((present_days::float / total_working_days) * 100) FROM attendance WHERE CAST(school_id AS VARCHAR) = %s AND total_working_days > 0", (school_id,))
            avg_att_raw = cur.fetchone()[0]
            avg_attendance = round(float(avg_att_raw), 1) if avg_att_raw else 0
        except:
            avg_attendance = 0

        # 7. Material Stats
        try:
            cur.execute("""
                SELECT 
                    SUM(CASE WHEN uniform_given THEN 1 ELSE 0 END) as uniform,
                    SUM(CASE WHEN books_given THEN 1 ELSE 0 END) as books,
                    SUM(CASE WHEN shoes_given THEN 1 ELSE 0 END) as shoes,
                    SUM(CASE WHEN bag_given THEN 1 ELSE 0 END) as bag
                FROM material_distribution WHERE CAST(school_id AS VARCHAR) = %s
            """, (school_id,))
            mat_row = cur.fetchone()
            material_stats = {'uniform': mat_row[0] or 0, 'books': mat_row[1] or 0, 'shoes': mat_row[2] or 0, 'bag': mat_row[3] or 0} if mat_row else {'uniform':0, 'books':0, 'shoes':0, 'bag':0}
        except:
            material_stats = {'uniform':0, 'books':0, 'shoes':0, 'bag':0}

    except Exception as e:
        print("Analytics Error:", e)
        total_students, avg_percentage, avg_attendance = 0, 0, 0
        class_strength, grade_dist, gender_dist, material_stats = [], [], [], {}

    finally:
        cur.close()
        conn.close()

    return render_template('analytics.html',
                           active_page='analytics',
                           total_students=total_students,
                           avg_percentage=avg_percentage,
                           avg_attendance=avg_attendance,
                           class_strength=class_strength,
                           grade_dist=grade_dist,
                           gender_dist=gender_dist,
                           material_stats=material_stats)

import time
import psycopg2.extras
from flask import request, jsonify, session, render_template

# ==========================================
# 11. AI SMART ASSISTANT (TEXT-TO-SQL) - UPDATED
# ==========================================

@app.route('/ai-assistant', methods=['GET'])
@login_required
def ai_assistant_page():
    # Make sure this matches your HTML file name
    return render_template('ai_search.html', active_page='ai_assistant')

@app.route('/api/ai-search', methods=['POST'])
@login_required
def api_ai_search():
    user_query = request.json.get('query')
    school_id = session.get('school_id')

    if not user_query:
        return jsonify({"error": "Please enter a question."}), 400

    # System Prompt for Text-to-SQL (With New Rules Added)
    prompt = f"""
    You are an expert SQL developer for a school PostgreSQL database.
    Here is the exact schema:
    1. students (student_id, name, roll_no, class_name, gender, school_id)
    2. monthly_attendance (student_id, present_days, total_working_days, school_id)
    3. exam_results (student_id, percentage, grade, school_id)

    User Request: "{user_query}"
    
    CRITICAL RULES FOR SQL GENERATION:
    1. For class names, ALWAYS use the exact format: 'Class 1', 'Class 2', 'Class 3', 'Class 4', 'Class 5'. If the user says "class 1" or "first class", convert it to 'Class 1'.
    2. Use ILIKE instead of '=' for all text searches to ignore case sensitivity (e.g., name ILIKE '%Aryan%').
    3. ALWAYS filter every query with: CAST(school_id AS VARCHAR) = '{school_id}'
    4. Use JOINs on student_id if the data spans multiple tables.
    5. Only use SELECT statements. Never use INSERT, UPDATE, DROP, or DELETE.
    6. RETURN ONLY THE RAW SQL QUERY. Do not include markdown formatting like ```sql or any explanations.
    """

    sql_query = ""
    max_retries = 3
    
    # ... Iske neeche aapka baaki ka Gemini API call wala code waisa hi rahega ...

    # ==========================================
    # RETRY LOGIC FOR 503 SERVER ERRORS
    # ==========================================
    for attempt in range(max_retries):
        try:
            # NAYA SYNTAX (google.genai ke hisaab se)
            response = ai_client.models.generate_content(
                model='gemini-3.6-flash', 
                contents=prompt
            )
            sql_query = response.text.strip()
            break # Success, loop se bahar niklo

        except Exception as e:
            error_msg = str(e).lower()
            if "503" in error_msg and attempt < max_retries - 1:
                # Agar 503 error hai, toh wait karke dobara try karein
                time.sleep(2 * (attempt + 1)) # Wait 2s, then 4s
                continue
            else:
                # Agar 3 baar me bhi na chale ya koi aur error ho
                return jsonify({"error": "AI Server abhi bohot busy hai (High Demand). Kripya 10 seconds baad dobara try karein."}), 500

    # Remove markdown if the AI accidentally adds it
    if sql_query.startswith("```sql"):
        sql_query = sql_query[6:-3].strip()
    elif sql_query.startswith("```"):
        sql_query = sql_query[3:-3].strip()

    # Security Check
    if not sql_query.lower().startswith("select"):
        return jsonify({"error": "Query blocked. Only SELECT queries allowed."}), 403

    # ==========================================
    # SAFE DATABASE EXECUTION
    # ==========================================
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(sql_query)
        results = cursor.fetchall()
        
        # Get column names dynamically
        columns = list(results[0].keys()) if results else []

        cursor.close()
        conn.close()

        return jsonify({
            "success": True, 
            "columns": columns, 
            "data": results, 
            "sql_used": sql_query
        })

    except Exception as db_error:
        # Catching SQL syntax errors generated by AI
        if 'conn' in locals() and conn:
            conn.close()
        return jsonify({"error": "AI ne data fetch karne me galti ki. Kripya apna sawal thoda badal kar puchein."}), 500





if __name__ == '__main__':
    app.run(debug=True, port=5000)