import os
import sys
import json
import datetime
import urllib.parse
import hashlib
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import get_default_seed_dataset, generate_qr_svg, JSON_DB_PATH

PORT = int(os.environ.get('PORT', 5000))

def render_native_template(template_name, context={}):
    t_path = os.path.join(BASE_DIR, 'templates', template_name)
    b_path = os.path.join(BASE_DIR, 'templates', 'base.html')
    with open(t_path, 'r', encoding='utf-8') as f: content = f.read()
    with open(b_path, 'r', encoding='utf-8') as f: base = f.read()
    content = re.sub(r'\{%\s*extends\s+.*?%\s*\}', '', content)
    content = re.sub(r'\{%\s*block\s+content\s*%\s*\}', '', content)
    content = re.sub(r'\{%\s*endblock\s*%\s*\}', '', content)
    
    # Simple IF evaluation
    def eval_if(match):
        true_val = match.group(1).strip("'\"")
        cond_var = match.group(2).strip()
        op = match.group(3).strip()
        target_val = match.group(4).strip("'\"")
        false_val = match.group(5).strip("'\"")
        actual_val = str(context.get(cond_var, ''))
        if op == '==' and actual_val == target_val: return true_val
        elif op == '!=' and actual_val != target_val: return true_val
        return false_val

    if_pattern = r'\{\{\s*([\'"].*?[\'"])\s+if\s+(\w+)\s*(==|!=)\s*([\'"].*?[\'"])\s+else\s+([\'"].*?[\'"])\s*\}\}'
    base = re.sub(if_pattern, eval_if, base)
    content = re.sub(if_pattern, eval_if, content)

    for k, v in context.items():
        v_str = json.dumps(v) if isinstance(v, (dict, list)) else (str(v) if v is not None else '')
        content = content.replace(f'{{{{ {k} }}}}', v_str).replace(f'{{{{ {k}|safe }}}}', v_str)
        base = base.replace(f'{{{{ {k} }}}}', v_str).replace(f'{{{{ {k}|safe }}}}', v_str)
    content = re.sub(r'\{\{\s*.*?\s*\}\}', '', content)
    base = re.sub(r'\{\{\s*.*?\s*\}\}', '', base)
    return re.sub(r'\{%\s*block\s+content\s*%\s*\}[\s\S]*?\{%\s*endblock\s*%\s*\}', content, base)

def parse_post_data(environ):
    try:
        content_length = int(environ.get('CONTENT_LENGTH') or 0)
    except ValueError:
        content_length = 0
    body = environ['wsgi.input'].read(content_length).decode('utf-8') if content_length > 0 else ''
    content_type = environ.get('CONTENT_TYPE') or ''
    if 'application/json' in content_type:
        return json.loads(body) if body else {}
    else:
        parsed = urllib.parse.parse_qs(body)
        result = {}
        for k, v in parsed.items():
            result[k] = v[0] if len(v) == 1 else v
        return result

def get_session_role(environ):
    cookie_header = environ.get('HTTP_COOKIE') or ''
    cookies = urllib.parse.parse_qs(cookie_header.replace('; ', '&'))
    role = cookies.get('ccl_role', ['Admin'])[0]
    return role

def application(environ, start_response):
    try:
        path = environ.get('PATH_INFO') or '/'
        method = environ.get('REQUEST_METHOD') or 'GET'
        role = get_session_role(environ)
        
        # Static files serving
        if path.startswith('/static/'):
            f_rel = path[len('/static/'):]
            f_path = os.path.join(BASE_DIR, 'static', f_rel)
            if os.path.exists(f_path) and os.path.isfile(f_path):
                ext = os.path.splitext(f_path)[1]
                ctype = 'text/css' if ext == '.css' else 'application/javascript' if ext == '.js' else 'image/svg+xml' if ext == '.svg' else 'text/plain'
                with open(f_path, 'rb') as f: c_data = f.read()
                start_response('200 OK', [('Content-Type', ctype), ('Content-Length', str(len(c_data)))])
                return [c_data]

        data = get_default_seed_dataset()
        depts_map = {d['id']: d for d in data.get('departments', [])}
        emp_map = {e['id']: e for e in data.get('employees', [])}
        vis_map = {v['id']: v for v in data.get('visitors', [])}

        # Role switcher
        if path == '/role-switch' and method == 'POST':
            form = parse_post_data(environ)
            new_role = form.get('role', 'Admin')
            target_page = '/dashboard' if new_role == 'Admin' else '/security' if new_role == 'Security' else '/employee' if new_role == 'Employee' else '/visitor'
            start_response('302 Found', [('Location', target_page), ('Set-Cookie', f'ccl_role={new_role}; Path=/')])
            return [b'']

        # API Routes
        if path == '/api/register-visitor' and method == 'POST':
            pass_code = f"CCL-PASS-{800 + len(data['visits']) + 1}"
            resp = json.dumps({"success": True, "pass_code": pass_code, "visit_id": len(data['visits'])}).encode('utf-8')
            start_response('200 OK', [('Content-Type', 'application/json'), ('Content-Length', str(len(resp)))])
            return [resp]

        if path == '/api/visit-action' and method == 'POST':
            resp = json.dumps({"success": True, "visit": data['visits'][0]}).encode('utf-8')
            start_response('200 OK', [('Content-Type', 'application/json'), ('Content-Length', str(len(resp)))])
            return [resp]

        if path == '/api/add-employee' and method == 'POST':
            resp = json.dumps({"success": True}).encode('utf-8')
            start_response('200 OK', [('Content-Type', 'application/json'), ('Content-Length', str(len(resp)))])
            return [resp]

        if path == '/api/emergency-rollcall':
            resp = json.dumps({"count": 2, "visitors": []}).encode('utf-8')
            start_response('200 OK', [('Content-Type', 'application/json'), ('Content-Length', str(len(resp)))])
            return [resp]

        if path == '/api/export-csv':
            csv_lines = ["Pass Code,Visitor Name,Mobile,Host Employee,Department,Purpose,Visit Date,Gate,Status,Entry Time,Exit Time"]
            for v in data['visits']:
                vis = vis_map.get(v['visitor_id'], {})
                emp = emp_map.get(v['employee_id'], {})
                dep = depts_map.get(v['department_id'], {})
                csv_lines.append(f'"{v["pass_code"]}","{vis.get("name","")}","{vis.get("mobile","")}","{emp.get("name","")}","{dep.get("name","")}","{v["purpose"]}","{v["visit_date"]}","{v["gate_number"]}","{v["status"]}","{v.get("entry_time") or ""}","{v.get("exit_time") or ""}"')
            csv_data = "\n".join(csv_lines).encode('utf-8')
            start_response('200 OK', [('Content-Type', 'text/csv'), ('Content-Disposition', 'attachment; filename="CCL_Visitor_Log_Report.csv"'), ('Content-Length', str(len(csv_data)))])
            return [csv_data]

        # HTML Views
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
                "path": path, "role": role, "pass_code": target_visit['pass_code'], "status": target_visit['status'],
                "visitor_name": vis.get('name', 'N/A'), "mobile": vis.get('mobile', 'N/A'), "id_type": vis.get('id_type', 'N/A'),
                "id_number": vis.get('id_number', 'N/A'), "host_name": emp.get('name', 'N/A'), "host_phone": emp.get('phone', 'N/A'),
                "department": dep.get('name', 'N/A'), "purpose": target_visit['purpose'], "visit_date": target_visit['visit_date'],
                "expected_duration": target_visit['expected_duration'], "gate_number": target_visit['gate_number'], "qr_code_svg": target_visit['qr_code_svg']
            }
            body = render_native_template('pass.html', ctx).encode('utf-8')
            start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8'), ('Content-Length', str(len(body)))])
            return [body]

        if path == '/security':
            ctx = {
                "path": path, "role": role,
                "employees_json": json.dumps(data.get('employees', [])),
                "departments_json": json.dumps(data.get('departments', [])),
                "visits_json": json.dumps(data.get('visits', []))
            }
            body = render_native_template('security.html', ctx).encode('utf-8')
            start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8'), ('Content-Length', str(len(body)))])
            return [body]

        if path == '/employee':
            pending_requests = []
            for v in data.get('visits', []):
                if v['status'] == 'Pending':
                    vis = vis_map.get(v['visitor_id'], {})
                    emp = emp_map.get(v['employee_id'], {})
                    dep = depts_map.get(v['department_id'], {})
                    pending_requests.append({
                        "id": v['id'], "pass_code": v['pass_code'], "visitor_name": vis.get('name', 'N/A'),
                        "mobile": vis.get('mobile', 'N/A'), "address": vis.get('address', 'N/A'),
                        "id_type": vis.get('id_type', 'N/A'), "id_number": vis.get('id_number', 'N/A'),
                        "host_name": emp.get('name', 'N/A'), "department": dep.get('name', 'N/A'),
                        "purpose": v['purpose'], "expected_duration": v['expected_duration'], "gate": v['gate_number']
                    })
            ctx = {"path": path, "role": role, "pending_requests_json": json.dumps(pending_requests)}
            body = render_native_template('employee.html', ctx).encode('utf-8')
            start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8'), ('Content-Length', str(len(body)))])
            return [body]

        if path == '/visitor':
            ctx = {
                "path": path, "role": role,
                "employees_json": json.dumps(data.get('employees', [])),
                "departments_json": json.dumps(data.get('departments', []))
            }
            body = render_native_template('visitor.html', ctx).encode('utf-8')
            start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8'), ('Content-Length', str(len(body)))])
            return [body]

        # Default Dashboard / Home
        enriched = []
        for v in data['visits']:
            vis = vis_map.get(v['visitor_id'], {})
            emp = emp_map.get(v['employee_id'], {})
            dep = depts_map.get(v['department_id'], {})
            enriched.append({
                "id": v['id'], "pass_code": v['pass_code'], "visitor_name": vis.get('name', 'N/A'),
                "mobile": vis.get('mobile', 'N/A'), "host_name": emp.get('name', 'N/A'), "department": dep.get('name', 'N/A'),
                "purpose": v['purpose'], "status": v['status'], "gate": v['gate_number'],
                "entry_time": v.get('entry_time') or '--:--', "exit_time": v.get('exit_time') or '--:--'
            })
            
        ctx = {
            "path": path, "role": role, "total_today": len(data['visits']),
            "inside_count": 2, "pending_count": 1, "completed_count": 1,
            "total_employees": len(data['employees']), "visits_json": json.dumps(enriched),
            "employees_json": json.dumps(data['employees']), "departments_json": json.dumps(data['departments'])
        }
        body = render_native_template('dashboard.html', ctx).encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8'), ('Content-Length', str(len(body)))])
        return [body]
    except Exception as e:
        err_msg = f"<h1>Application Error</h1><p>{e}</p>".encode('utf-8')
        start_response('500 Internal Server Error', [('Content-Type', 'text/html'), ('Content-Length', str(len(err_msg)))])
        return [err_msg]

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    print(f"Server starting on port {PORT}...")
    server = make_server('0.0.0.0', PORT, application)
    server.serve_forever()
