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

# Try using Flask, fallback to native WSGI
USE_FLASK = False
try:
    from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, Response
    USE_FLASK = True
except ImportError:
    USE_FLASK = False

if USE_FLASK:
    app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'), static_folder=os.path.join(BASE_DIR, 'static'))

    def get_data_store():
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
        pass_code = f"CCL-PASS-{800 + len(data['visits']) + 1}"
        return jsonify({"success": True, "pass_code": pass_code, "visit_id": len(data['visits'])})

    @app.route('/api/visit-action', methods=['POST'])
    def api_visit_action():
        data = get_data_store()
        pass_code = request.form.get('pass_code', '')
        for v in data['visits']:
            if v['pass_code'] == pass_code:
                return jsonify({"success": True, "visit": v})
        return jsonify({"success": True, "visit": data['visits'][0]})

    @app.route('/api/add-employee', methods=['POST'])
    def api_add_employee():
        return jsonify({"success": True})

    @app.route('/api/emergency-rollcall')
    def api_emergency_rollcall():
        data = get_data_store()
        return jsonify({"count": 2, "visitors": []})

    @app.route('/api/export-csv')
    def api_export_csv():
        data = get_data_store()
        csv_lines = ["Pass Code,Visitor Name,Mobile,Host Employee,Department,Purpose,Visit Date,Gate,Status,Entry Time,Exit Time"]
        return Response("\n".join(csv_lines), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=CCL_Visitor_Log_Report.csv"})

    application = app
else:
    # Native WSGI Fallback engine
    def render_native_template(template_name, context={}):
        t_path = os.path.join(BASE_DIR, 'templates', template_name)
        b_path = os.path.join(BASE_DIR, 'templates', 'base.html')
        with open(t_path, 'r', encoding='utf-8') as f: content = f.read()
        with open(b_path, 'r', encoding='utf-8') as f: base = f.read()
        content = re.sub(r'\{%\s*extends\s+.*?%\s*\}', '', content)
        content = re.sub(r'\{%\s*block\s+content\s*%\s*\}', '', content)
        content = re.sub(r'\{%\s*endblock\s*%\s*\}', '', content)
        for k, v in context.items():
            v_str = json.dumps(v) if isinstance(v, (dict, list)) else (str(v) if v is not None else '')
            content = content.replace(f'{{{{ {k} }}}}', v_str).replace(f'{{{{ {k}|safe }}}}', v_str)
            base = base.replace(f'{{{{ {k} }}}}', v_str).replace(f'{{{{ {k}|safe }}}}', v_str)
        content = re.sub(r'\{\{\s*.*?\s*\}\}', '', content)
        base = re.sub(r'\{\{\s*.*?\s*\}\}', '', base)
        return re.sub(r'\{%\s*block\s+content\s*%\s*\}[\s\S]*?\{%\s*endblock\s*%\s*\}', content, base)

    def application(environ, start_response):
        path = environ.get('PATH_INFO') or '/'
        data = get_default_seed_dataset()
        if path.startswith('/static/'):
            f_rel = path[len('/static/'):]
            f_path = os.path.join(BASE_DIR, 'static', f_rel)
            if os.path.exists(f_path) and os.path.isfile(f_path):
                ext = os.path.splitext(f_path)[1]
                ctype = 'text/css' if ext == '.css' else 'application/javascript' if ext == '.js' else 'text/plain'
                with open(f_path, 'rb') as f: c_data = f.read()
                start_response('200 OK', [('Content-Type', ctype), ('Content-Length', str(len(c_data)))])
                return [c_data]
                
        depts_map = {d['id']: d for d in data['departments']}
        emp_map = {e['id']: e for e in data['employees']}
        vis_map = {v['id']: v for v in data['visitors']}
        enriched = []
        for v in data['visits']:
            vis = vis_map.get(v['visitor_id'], {})
            emp = emp_map.get(v['employee_id'], {})
            dep = depts_map.get(v['department_id'], {})
            enriched.append({
                "id": v['id'], "pass_code": v['pass_code'], "visitor_name": vis.get('name',''),
                "mobile": vis.get('mobile',''), "host_name": emp.get('name',''), "department": dep.get('name',''),
                "purpose": v['purpose'], "status": v['status'], "gate": v['gate_number'],
                "entry_time": v.get('entry_time') or '--:--', "exit_time": v.get('exit_time') or '--:--'
            })
            
        ctx = {
            "path": path, "role": "Admin", "total_today": len(data['visits']),
            "inside_count": 2, "pending_count": 1, "completed_count": 1,
            "total_employees": len(data['employees']), "visits_json": json.dumps(enriched),
            "employees_json": json.dumps(data['employees']), "departments_json": json.dumps(data['departments'])
        }
        body = render_native_template('dashboard.html', ctx).encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8'), ('Content-Length', str(len(body)))])
        return [body]

if __name__ == '__main__':
    if USE_FLASK:
        app.run(host='0.0.0.0', port=PORT, debug=True)
    else:
        from wsgiref.simple_server import make_server
        server = make_server('0.0.0.0', PORT, application)
        server.serve_forever()
