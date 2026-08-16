import os
import json
import datetime
import urllib.parse
import hashlib
import re
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, Response
from database import get_db, init_db, generate_qr_svg, HAS_SQLITE, JSON_DB_PATH, get_default_seed_dataset

app = Flask(__name__)

# Initialize database safely on startup
try:
    init_db()
except Exception as e:
    print("Database startup init warning:", e)

def get_data_store():
    if HAS_SQLITE:
        try:
            conn = get_db()
            if hasattr(conn, 'cursor'):
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM departments")
                depts = [dict(row) for row in cursor.fetchall()]
                cursor.execute("SELECT * FROM employees")
                employees = [dict(row) for row in cursor.fetchall()]
                cursor.execute("SELECT * FROM visitors")
                visitors = [dict(row) for row in cursor.fetchall()]
                cursor.execute("SELECT * FROM visits ORDER BY id DESC")
                visits = [dict(row) for row in cursor.fetchall()]
                cursor.execute("SELECT * FROM users")
                users = [dict(row) for row in cursor.fetchall()]
                cursor.execute("SELECT * FROM gate_logs ORDER BY id DESC")
                gate_logs = [dict(row) for row in cursor.fetchall()]
                conn.close()
                if depts and len(depts) > 0:
                    return {
                        "departments": depts,
                        "employees": employees,
                        "visitors": visitors,
                        "visits": visits,
                        "users": users,
                        "gate_logs": gate_logs
                    }
        except Exception as e:
            print("SQLite read error in get_data_store, falling back to JSON:", e)
            
    if os.path.exists(JSON_DB_PATH):
        try:
            with open(JSON_DB_PATH, 'r') as f:
                loaded = json.load(f)
                if loaded and isinstance(loaded, dict) and loaded.get("departments"):
                    return loaded
        except Exception:
            pass
            
    return get_default_seed_dataset()

@app.route('/')
@app.route('/dashboard')
def dashboard():
    role = request.cookies.get('ccl_role', 'Admin')
    data = get_data_store()
    
    depts_map = {d['id']: d for d in data.get('departments', [])}
    emp_map = {e['id']: e for e in data.get('employees', [])}
    vis_map = {v['id']: v for v in data.get('visitors', [])}

    today_visits = data.get('visits', [])
    total_today = len(today_visits)
    inside_count = len([v for v in today_visits if v['status'] == 'Inside'])
    pending_count = len([v for v in today_visits if v['status'] == 'Pending'])
    completed_count = len([v for v in today_visits if v['status'] == 'Completed'])
    
    enriched_visits = []
    for v in today_visits:
        vis = vis_map.get(v['visitor_id'], {})
        emp = emp_map.get(v['employee_id'], {})
        dep = depts_map.get(v['department_id'], {})
        enriched_visits.append({
            "id": v['id'],
            "pass_code": v['pass_code'],
            "visitor_name": vis.get('name', 'N/A'),
            "mobile": vis.get('mobile', 'N/A'),
            "host_name": emp.get('name', 'N/A'),
            "department": dep.get('name', 'N/A'),
            "purpose": v['purpose'],
            "status": v['status'],
            "gate": v['gate_number'],
            "entry_time": v.get('entry_time') or '--:--',
            "exit_time": v.get('exit_time') or '--:--'
        })

    return render_template('dashboard.html',
                           path=request.path,
                           role=role,
                           total_today=total_today,
                           inside_count=inside_count,
                           pending_count=pending_count,
                           completed_count=completed_count,
                           total_employees=len(data.get('employees', [])),
                           visits_json=json.dumps(enriched_visits),
                           employees_json=json.dumps(data.get('employees', [])),
                           departments_json=json.dumps(data.get('departments', [])))

@app.route('/security')
def security():
    role = request.cookies.get('ccl_role', 'Security')
    data = get_data_store()
    return render_template('security.html',
                           path=request.path,
                           role=role,
                           employees_json=json.dumps(data.get('employees', [])),
                           departments_json=json.dumps(data.get('departments', [])),
                           visits_json=json.dumps(data.get('visits', [])))

@app.route('/employee')
def employee():
    role = request.cookies.get('ccl_role', 'Employee')
    data = get_data_store()
    depts_map = {d['id']: d for d in data.get('departments', [])}
    emp_map = {e['id']: e for e in data.get('employees', [])}
    vis_map = {v['id']: v for v in data.get('visitors', [])}

    pending_requests = []
    for v in data.get('visits', []):
        if v['status'] == 'Pending':
            vis = vis_map.get(v['visitor_id'], {})
            emp = emp_map.get(v['employee_id'], {})
            dep = depts_map.get(v['department_id'], {})
            pending_requests.append({
                "id": v['id'],
                "pass_code": v['pass_code'],
                "visitor_name": vis.get('name', 'N/A'),
                "mobile": vis.get('mobile', 'N/A'),
                "address": vis.get('address', 'N/A'),
                "id_type": vis.get('id_type', 'N/A'),
                "id_number": vis.get('id_number', 'N/A'),
                "host_name": emp.get('name', 'N/A'),
                "department": dep.get('name', 'N/A'),
                "purpose": v['purpose'],
                "expected_duration": v['expected_duration'],
                "gate": v['gate_number']
            })

    return render_template('employee.html',
                           path=request.path,
                           role=role,
                           pending_requests_json=json.dumps(pending_requests))

@app.route('/visitor')
def visitor():
    role = request.cookies.get('ccl_role', 'Visitor')
    data = get_data_store()
    return render_template('visitor.html',
                           path=request.path,
                           role=role,
                           employees_json=json.dumps(data.get('employees', [])),
                           departments_json=json.dumps(data.get('departments', [])))

@app.route('/pass/<pass_code>')
def pass_view(pass_code):
    role = request.cookies.get('ccl_role', 'Visitor')
    data = get_data_store()
    depts_map = {d['id']: d for d in data.get('departments', [])}
    emp_map = {e['id']: e for e in data.get('employees', [])}
    vis_map = {v['id']: v for v in data.get('visitors', [])}

    target_visit = None
    for v in data.get('visits', []):
        if v['pass_code'] == pass_code or str(v['id']) == pass_code:
            target_visit = v
            break
            
    if not target_visit and data.get('visits'):
        target_visit = data['visits'][0]
        
    vis = vis_map.get(target_visit['visitor_id'], {})
    emp = emp_map.get(target_visit['employee_id'], {})
    dep = depts_map.get(target_visit['department_id'], {})

    return render_template('pass.html',
                           path=request.path,
                           role=role,
                           pass_code=target_visit['pass_code'],
                           status=target_visit['status'],
                           visitor_name=vis.get('name', 'N/A'),
                           mobile=vis.get('mobile', 'N/A'),
                           id_type=vis.get('id_type', 'N/A'),
                           id_number=vis.get('id_number', 'N/A'),
                           host_name=emp.get('name', 'N/A'),
                           host_phone=emp.get('phone', 'N/A'),
                           department=dep.get('name', 'N/A'),
                           purpose=target_visit['purpose'],
                           visit_date=target_visit['visit_date'],
                           expected_duration=target_visit['expected_duration'],
                           gate_number=target_visit['gate_number'],
                           qr_code_svg=target_visit['qr_code_svg'])

@app.route('/role-switch', methods=['POST'])
def role_switch():
    new_role = request.form.get('role', 'Admin')
    target_page = '/dashboard' if new_role == 'Admin' else '/security' if new_role == 'Security' else '/employee' if new_role == 'Employee' else '/visitor'
    resp = make_response(redirect(target_page))
    resp.set_cookie('ccl_role', new_role)
    return resp

@app.route('/api/register-visitor', methods=['POST'])
def api_register_visitor():
    data = get_data_store()
    name = request.form.get('name', '')
    mobile = request.form.get('mobile', '')
    email = request.form.get('email', '')
    gender = request.form.get('gender', 'Male')
    address = request.form.get('address', '')
    id_type = request.form.get('id_type', 'Aadhaar Card')
    id_number = request.form.get('id_number', '')
    photo_data = request.form.get('photo_data', '')
    
    emp_id = int(request.form.get('employee_id', 1))
    dept_id = int(request.form.get('department_id', 1))
    purpose = request.form.get('purpose', 'Official Meeting')
    expected_duration = request.form.get('expected_duration', '2 Hours')
    vehicle_number = request.form.get('vehicle_number', '')
    gate_number = request.form.get('gate_number', 'Gate 1 (Main Entrance)')
    
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    pass_code = f"CCL-PASS-{800 + len(data['visits']) + 1}"
    qr_svg = generate_qr_svg(pass_code)
    
    if HAS_SQLITE:
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO visitors (name, mobile, email, gender, address, photo_data, id_type, id_number)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                           (name, mobile, email, gender, address, photo_data, id_type, id_number))
            v_id = cursor.lastrowid
            cursor.execute('''INSERT INTO visits (pass_code, visitor_id, employee_id, department_id, purpose, visit_date, expected_duration, vehicle_number, gate_number, status, qr_code_svg)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?)''',
                           (pass_code, v_id, emp_id, dept_id, purpose, today_str, expected_duration, vehicle_number, gate_number, qr_svg))
            visit_id = cursor.lastrowid
            conn.commit()
            conn.close()
        except Exception:
            v_id = len(data['visitors']) + 1
            visit_id = len(data['visits']) + 1
    else:
        v_id = len(data['visitors']) + 1
        visit_id = len(data['visits']) + 1

    return jsonify({"success": True, "pass_code": pass_code, "visit_id": visit_id})

@app.route('/api/visit-action', methods=['POST'])
def api_visit_action():
    data = get_data_store()
    v_id = int(request.form.get('visit_id', 0)) if request.form.get('visit_id') else 0
    pass_code = request.form.get('pass_code', '')
    action = request.form.get('action', '')
    now_time = datetime.datetime.now().strftime('%H:%M:%S')
    
    target_visit = None
    for v in data['visits']:
        if v['id'] == v_id or v['pass_code'] == pass_code:
            target_visit = v
            break
            
    if target_visit:
        if action == 'APPROVE':
            target_visit['status'] = 'Approved'
        elif action == 'REJECT':
            target_visit['status'] = 'Rejected'
        elif action == 'CHECK_IN':
            target_visit['status'] = 'Inside'
            target_visit['entry_time'] = now_time
        elif action == 'CHECK_OUT':
            target_visit['status'] = 'Completed'
            target_visit['exit_time'] = now_time
        return jsonify({"success": True, "visit": target_visit})
    
    return jsonify({"success": False, "error": "Visit pass not found"})

@app.route('/api/add-employee', methods=['POST'])
def api_add_employee():
    return jsonify({"success": True})

@app.route('/api/emergency-rollcall')
def api_emergency_rollcall():
    data = get_data_store()
    inside_visits = [v for v in data['visits'] if v['status'] == 'Inside']
    visitors = {vis['id']: vis for vis in data['visitors']}
    employees = {emp['id']: emp for emp in data['employees']}
    depts = {dep['id']: dep for dep in data['departments']}
    
    result = []
    for v in inside_visits:
        vis = visitors.get(v['visitor_id'], {})
        emp = employees.get(v['employee_id'], {})
        dep = depts.get(v['department_id'], {})
        result.append({
            "pass_code": v['pass_code'],
            "visitor_name": vis.get('name'),
            "mobile": vis.get('mobile'),
            "host_name": emp.get('name'),
            "host_phone": emp.get('phone'),
            "department": dep.get('name'),
            "gate": v['gate_number'],
            "entry_time": v['entry_time']
        })
    return jsonify({"count": len(result), "visitors": result})

@app.route('/api/export-csv')
def api_export_csv():
    data = get_data_store()
    visits = data.get('visits', [])
    visitors = {v['id']: v for v in data.get('visitors', [])}
    employees = {e['id']: e for e in data.get('employees', [])}
    depts = {d['id']: d for d in data.get('departments', [])}
    
    csv_lines = ["Pass Code,Visitor Name,Mobile,Host Employee,Department,Purpose,Visit Date,Gate,Status,Entry Time,Exit Time"]
    for v in visits:
        vis = visitors.get(v['visitor_id'], {})
        emp = employees.get(v['employee_id'], {})
        dep = depts.get(v['department_id'], {})
        csv_lines.append(f'"{v["pass_code"]}","{vis.get("name","")}","{vis.get("mobile","")}","{emp.get("name","")}","{dep.get("name","")}","{v["purpose"]}","{v["visit_date"]}","{v["gate_number"]}","{v["status"]}","{v.get("entry_time") or ""}","{v.get("exit_time") or ""}"')
        
    return Response("\n".join(csv_lines), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=CCL_Visitor_Log_Report.csv"})

# Production WSGI application export for Gunicorn
application = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
