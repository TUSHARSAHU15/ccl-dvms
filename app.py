import os
import sys
import json
import datetime
import urllib.parse
import hashlib
import re
from wsgiref.simple_server import make_server
from database import get_db, init_db, generate_qr_svg, HAS_SQLITE, JSON_DB_PATH

# Initialize database on startup
init_db()

PORT = 5000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_data_store():
    if not HAS_SQLITE:
        with open(JSON_DB_PATH, 'r') as f:
            return json.load(f)
    return None

def save_data_store(data):
    if not HAS_SQLITE:
        with open(JSON_DB_PATH, 'w') as f:
            json.dump(data, f, indent=2)

def parse_post_data(environ):
    try:
        content_length = int(environ.get('CONTENT_LENGTH', 0))
    except ValueError:
        content_length = 0
        
    body = environ['wsgi.input'].read(content_length).decode('utf-8')
    
    content_type = environ.get('CONTENT_TYPE', '')
    if 'application/json' in content_type:
        return json.loads(body) if body else {}
    else:
        parsed = urllib.parse.parse_qs(body)
        result = {}
        for k, v in parsed.items():
            result[k] = v[0] if len(v) == 1 else v
        return result

def get_session_role(environ):
    cookie_header = environ.get('HTTP_COOKIE', '')
    cookies = urllib.parse.parse_qs(cookie_header.replace('; ', '&'))
    role = cookies.get('ccl_role', ['Admin'])[0]
    return role

def render_template(template_name, context={}):
    template_path = os.path.join(BASE_DIR, 'templates', template_name)
    base_path = os.path.join(BASE_DIR, 'templates', 'base.html')
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    with open(base_path, 'r', encoding='utf-8') as f:
        base = f.read()

    # Clean Jinja block & extends tags from child template content
    content = re.sub(r'\{%\s*extends\s+.*?%\s*\}', '', content)
    content = re.sub(r'\{%\s*block\s+content\s*%\s*\}', '', content)
    content = re.sub(r'\{%\s*endblock\s*%\s*\}', '', content)
    
    # Process Jinja IF conditions (simple boolean/string match evaluation)
    def eval_if(match):
        true_val = match.group(1).strip("'\"")
        cond_var = match.group(2).strip()
        op = match.group(3).strip()
        target_val = match.group(4).strip("'\"")
        false_val = match.group(5).strip("'\"")
        
        actual_val = str(context.get(cond_var, ''))
        if op == '==' and actual_val == target_val:
            return true_val
        elif op == '!=' and actual_val != target_val:
            return true_val
        return false_val

    if_pattern = r'\{\{\s*([\'"].*?[\'"])\s+if\s+(\w+)\s*(==|!=)\s*([\'"].*?[\'"])\s+else\s+([\'"].*?[\'"])\s*\}\}'
    base = re.sub(if_pattern, eval_if, base)
    content = re.sub(if_pattern, eval_if, content)

    # Perform value replacements
    for key, val in context.items():
        if isinstance(val, (dict, list)):
            val_str = json.dumps(val)
        else:
            val_str = str(val) if val is not None else ''
            
        content = content.replace(f'{{{{ {key} }}}}', val_str)
        content = content.replace(f'{{{{ {key}|safe }}}}', val_str)
        base = base.replace(f'{{{{ {key} }}}}', val_str)
        base = base.replace(f'{{{{ {key}|safe }}}}', val_str)

    # Clean leftover unhandled variables
    content = re.sub(r'\{\{\s*.*?\s*\}\}', '', content)
    base = re.sub(r'\{\{\s*.*?\s*\}\}', '', base)

    # Substitute content into base.html's block content section (handling any whitespace)
    full_page = re.sub(r'\{%\s*block\s+content\s*%\s*\}[\s\S]*?\{%\s*endblock\s*%\s*\}', content, base)
    return full_page

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    role = get_session_role(environ)
    
    # Static files serving
    if path.startswith('/static/'):
        file_rel = path[len('/static/'):]
        file_path = os.path.join(BASE_DIR, 'static', file_rel)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            ext = os.path.splitext(file_path)[1]
            content_type = 'text/css' if ext == '.css' else 'application/javascript' if ext == '.js' else 'image/svg+xml' if ext == '.svg' else 'text/plain'
            with open(file_path, 'rb') as f:
                content = f.read()
            start_response('200 OK', [('Content-Type', content_type), ('Content-Length', str(len(content)))])
            return [content]
            
    # API: Export CSV
    if path == '/api/export-csv':
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
            
        csv_body = "\n".join(csv_lines).encode('utf-8')
        start_response('200 OK', [
            ('Content-Type', 'text/csv'),
            ('Content-Disposition', 'attachment; filename="CCL_Visitor_Log_Report.csv"'),
            ('Content-Length', str(len(csv_body)))
        ])
        return [csv_body]

    # POST: Role Switcher
    if path == '/role-switch' and method == 'POST':
        form = parse_post_data(environ)
        new_role = form.get('role', 'Admin')
        target_page = '/dashboard' if new_role == 'Admin' else '/security' if new_role == 'Security' else '/employee' if new_role == 'Employee' else '/visitor'
        start_response('302 Found', [('Location', target_page), ('Set-Cookie', f'ccl_role={new_role}; Path=/')])
        return [b'']

    # POST: Register Visitor
    if path == '/api/register-visitor' and method == 'POST':
        form = parse_post_data(environ)
        data = get_data_store()
        
        v_id = len(data['visitors']) + 1
        vis_record = {
            "id": v_id,
            "name": form.get('name', ''),
            "mobile": form.get('mobile', ''),
            "email": form.get('email', ''),
            "gender": form.get('gender', 'Male'),
            "address": form.get('address', ''),
            "id_type": form.get('id_type', 'Aadhaar Card'),
            "id_number": form.get('id_number', ''),
            "photo_data": form.get('photo_data', '')
        }
        data['visitors'].append(vis_record)
        
        pass_code = f"CCL-PASS-{800 + len(data['visits']) + 1}"
        today_str = datetime.date.today().strftime('%Y-%m-%d')
        
        visit_record = {
            "id": len(data['visits']) + 1,
            "pass_code": pass_code,
            "visitor_id": v_id,
            "employee_id": int(form.get('employee_id', 1)),
            "department_id": int(form.get('department_id', 1)),
            "purpose": form.get('purpose', 'Official Meeting'),
            "visit_date": today_str,
            "expected_duration": form.get('expected_duration', '2 Hours'),
            "vehicle_number": form.get('vehicle_number', ''),
            "gate_number": form.get('gate_number', 'Gate 1 (Main Entrance)'),
            "status": "Pending",
            "entry_time": None,
            "exit_time": None,
            "qr_code_svg": generate_qr_svg(pass_code),
            "created_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        data['visits'].append(visit_record)
        save_data_store(data)
        
        response = json.dumps({"success": True, "pass_code": pass_code, "visit_id": visit_record["id"]}).encode('utf-8')
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [response]

    # POST: Visit Action (Approve, Reject, Check-In, Check-Out)
    if path == '/api/visit-action' and method == 'POST':
        form = parse_post_data(environ)
        data = get_data_store()
        
        v_id = int(form.get('visit_id', 0)) if form.get('visit_id') else 0
        pass_code = form.get('pass_code', '')
        action = form.get('action', '')
        
        target_visit = None
        for v in data['visits']:
            if v['id'] == v_id or v['pass_code'] == pass_code:
                target_visit = v
                break
                
        if target_visit:
            now_time = datetime.datetime.now().strftime('%H:%M:%S')
            today_str = datetime.date.today().strftime('%Y-%m-%d')
            
            if action == 'APPROVE':
                target_visit['status'] = 'Approved'
            elif action == 'REJECT':
                target_visit['status'] = 'Rejected'
                target_visit['rejection_reason'] = form.get('reason', 'Security Policy Discrepancy')
            elif action == 'CHECK_IN':
                target_visit['status'] = 'Inside'
                target_visit['entry_time'] = now_time
                data['gate_logs'].append({
                    "id": len(data['gate_logs']) + 1,
                    "visit_id": target_visit['id'],
                    "gate_number": target_visit['gate_number'],
                    "action": "ENTRY",
                    "timestamp": f"{today_str} {now_time}",
                    "guard_name": "Security Guard"
                })
            elif action == 'CHECK_OUT':
                target_visit['status'] = 'Completed'
                target_visit['exit_time'] = now_time
                data['gate_logs'].append({
                    "id": len(data['gate_logs']) + 1,
                    "visit_id": target_visit['id'],
                    "gate_number": target_visit['gate_number'],
                    "action": "EXIT",
                    "timestamp": f"{today_str} {now_time}",
                    "guard_name": "Security Guard"
                })
                
            save_data_store(data)
            resp = json.dumps({"success": True, "visit": target_visit}).encode('utf-8')
        else:
            resp = json.dumps({"success": False, "error": "Visit pass not found"}).encode('utf-8')
            
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [resp]

    # POST: Add Employee
    if path == '/api/add-employee' and method == 'POST':
        form = parse_post_data(environ)
        data = get_data_store()
        emp_id = len(data['employees']) + 1
        emp = {
            "id": emp_id,
            "emp_code": f"CCL{1000 + emp_id}",
            "name": form.get('name'),
            "department_id": int(form.get('department_id', 1)),
            "designation": form.get('designation'),
            "phone": form.get('phone'),
            "email": form.get('email')
        }
        data['employees'].append(emp)
        save_data_store(data)
        resp = json.dumps({"success": True, "employee": emp}).encode('utf-8')
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [resp]

    # GET: Emergency Roll call
    if path == '/api/emergency-rollcall':
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
        resp = json.dumps({"count": len(result), "visitors": result}).encode('utf-8')
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [resp]

    # HTML Page Views
    data = get_data_store()
    
    depts_map = {d['id']: d for d in data.get('departments', [])}
    emp_map = {e['id']: e for e in data.get('employees', [])}
    vis_map = {v['id']: v for v in data.get('visitors', [])}

    # Pass View
    if path.startswith('/pass/'):
        pass_code = path[len('/pass/'):]
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
        
        ctx = {
            "path": path,
            "role": role,
            "pass_code": target_visit['pass_code'],
            "status": target_visit['status'],
            "visitor_name": vis.get('name', 'N/A'),
            "mobile": vis.get('mobile', 'N/A'),
            "id_type": vis.get('id_type', 'N/A'),
            "id_number": vis.get('id_number', 'N/A'),
            "host_name": emp.get('name', 'N/A'),
            "host_phone": emp.get('phone', 'N/A'),
            "department": dep.get('name', 'N/A'),
            "purpose": target_visit['purpose'],
            "visit_date": target_visit['visit_date'],
            "expected_duration": target_visit['expected_duration'],
            "gate_number": target_visit['gate_number'],
            "qr_code_svg": target_visit['qr_code_svg']
        }
        body = render_template('pass.html', ctx).encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
        return [body]

    # Dashboard / Home
    if path in ['/', '/dashboard']:
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
            
        ctx = {
            "path": path,
            "role": role,
            "total_today": total_today,
            "inside_count": inside_count,
            "pending_count": pending_count,
            "completed_count": completed_count,
            "total_employees": len(data.get('employees', [])),
            "visits_json": json.dumps(enriched_visits),
            "employees_json": json.dumps(data.get('employees', [])),
            "departments_json": json.dumps(data.get('departments', []))
        }
        body = render_template('dashboard.html', ctx).encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
        return [body]

    # Security Portal
    if path == '/security':
        ctx = {
            "path": path,
            "role": role,
            "employees_json": json.dumps(data.get('employees', [])),
            "departments_json": json.dumps(data.get('departments', [])),
            "visits_json": json.dumps(data.get('visits', []))
        }
        body = render_template('security.html', ctx).encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
        return [body]

    # Employee Portal
    if path == '/employee':
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
        ctx = {
            "path": path,
            "role": role,
            "pending_requests_json": json.dumps(pending_requests)
        }
        body = render_template('employee.html', ctx).encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
        return [body]

    # Visitor Kiosk
    if path == '/visitor':
        ctx = {
            "path": path,
            "role": role,
            "employees_json": json.dumps(data.get('employees', [])),
            "departments_json": json.dumps(data.get('departments', []))
        }
        body = render_template('visitor.html', ctx).encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
        return [body]

    # Default redirect
    start_response('302 Found', [('Location', '/dashboard')])
    return [b'']

if __name__ == '__main__':
    print(f"============================================================")
    print(f" Central Coalfields Limited - Digital Visitor Management System")
    print(f" Server running on http://127.0.0.1:{PORT}")
    print(f"============================================================")
    httpd = make_server('0.0.0.0', PORT, application)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)
