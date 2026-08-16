import os
import hashlib
import json
import datetime
import uuid

JSON_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ccl_dvms.json')
HAS_SQLITE = False

def generate_qr_svg(content):
    import hashlib
    h = hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    size = 21
    def is_finder(r, c):
        if (r < 7 and c < 7) or (r < 7 and c >= size - 7) or (r >= size - 7 and c < 7):
            if (r == 0 or r == 6 or c == 0 or c == 6 or (2 <= r <= 4 and 2 <= c <= 4)) and (r < 7 and c < 7): return True
            if (r == 0 or r == 6 or c == size-7 or c == size-1 or (2 <= r <= 4 and size-5 <= c <= size-3)) and (r < 7 and c >= size-7): return True
            if (r == size-7 or r == size-1 or c == 0 or c == 6 or (size-5 <= r <= size-3 and 2 <= c <= 4)) and (r >= size-7 and c < 7): return True
            if (1 <= r <= 5 and 1 <= c <= 5) or (1 <= r <= 5 and size-6 <= c <= size-2) or (size-6 <= r <= size-2 and 1 <= c <= 5):
                if not (2 <= r <= 4 and 2 <= c <= 4) and not (2 <= r <= 4 and size-5 <= c <= size-3) and not (size-5 <= r <= size-3 and 2 <= c <= 4):
                    return False
                return True
        return False

    svg_rects = []
    cell_size = 10
    
    for r in range(size):
        for c in range(size):
            fill = False
            if is_finder(r, c):
                fill = True
            else:
                idx = (r * size + c) % len(h)
                fill = (int(h[idx], 16) % 2 == 0)
            
            if fill:
                svg_rects.append(f'<rect x="{c * cell_size}" y="{r * cell_size}" width="{cell_size}" height="{cell_size}" fill="#0F172A" />')

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size * cell_size} {size * cell_size}" width="160" height="160">
    <rect width="100%" height="100%" fill="#FFFFFF" />
    {''.join(svg_rects)}
    </svg>'''
    return svg_content

def get_default_seed_dataset():
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    def hash_pw(pw):
        return hashlib.sha256(pw.encode()).hexdigest()

    depts = [
        {"id": 1, "name": "Central Headquarters (Ranchi)", "area_name": "HQ Ranchi", "code": "CCL-HQ"},
        {"id": 2, "name": "Piparwar Open Cast Project", "area_name": "Piparwar Area", "code": "CCL-PIP"},
        {"id": 3, "name": "Barka-Sayal Area Office", "area_name": "Barka-Sayal Area", "code": "CCL-BSK"},
        {"id": 4, "name": "Rajrappa Coal Washery & Mines", "area_name": "Rajrappa Area", "code": "CCL-RAJ"},
        {"id": 5, "name": "Central Workshop Barkakana", "area_name": "Barkakana Area", "code": "CCL-CWB"},
        {"id": 6, "name": "N K Area Office", "area_name": "North Karanpura", "code": "CCL-NKA"}
    ]
    
    employees = [
        {"id": 1, "emp_code": "CCL1001", "name": "Rajesh Kumar", "department_id": 1, "designation": "General Manager (Mining)", "phone": "9431102938", "email": "rajesh.k@ccl.gov.in"},
        {"id": 2, "emp_code": "CCL1002", "name": "Sunita Sharma", "department_id": 5, "designation": "Chief Mechanical Engineer", "phone": "9431108273", "email": "sunita.sharma@ccl.gov.in"},
        {"id": 3, "emp_code": "CCL1003", "name": "Amit Varma", "department_id": 2, "designation": "Safety & Security Officer", "phone": "9431105642", "email": "amit.v@ccl.gov.in"},
        {"id": 4, "emp_code": "CCL1004", "name": "Priyadarshini Rao", "department_id": 1, "designation": "Senior HR Manager", "phone": "9431101129", "email": "p.rao@ccl.gov.in"},
        {"id": 5, "emp_code": "CCL1005", "name": "Vikram Singh", "department_id": 4, "designation": "Procurement Lead", "phone": "9431107741", "email": "vikram.s@ccl.gov.in"},
        {"id": 6, "emp_code": "CCL1006", "name": "Manoj Tiwari", "department_id": 3, "designation": "Area Finance Officer", "phone": "9431104482", "email": "manoj.t@ccl.gov.in"}
    ]

    users = [
        {"id": 1, "username": "admin", "password_hash": hash_pw("admin123"), "role": "Admin", "name": "System Administrator", "emp_id": None},
        {"id": 2, "username": "guard1", "password_hash": hash_pw("guard123"), "role": "Security", "name": "Security Officer - Gate 1", "emp_id": None},
        {"id": 3, "username": "guard2", "password_hash": hash_pw("guard123"), "role": "Security", "name": "Security Officer - Gate 2", "emp_id": None},
        {"id": 4, "username": "rajesh.k", "password_hash": hash_pw("emp123"), "role": "Employee", "name": "Rajesh Kumar", "emp_id": 1},
        {"id": 5, "username": "sunita.s", "password_hash": hash_pw("emp123"), "role": "Employee", "name": "Sunita Sharma", "emp_id": 2},
        {"id": 6, "username": "visitor", "password_hash": hash_pw("pass123"), "role": "Visitor", "name": "Guest Visitor", "emp_id": None}
    ]

    visitors = [
        {"id": 1, "name": "Ramesh Chand", "mobile": "9876543210", "email": "ramesh@vendor.com", "gender": "Male", "address": "Ranchi Industrial Park, Phase II", "id_type": "Aadhaar Card", "id_number": "8374-9201-4451"},
        {"id": 2, "name": "Anjali Gupta", "mobile": "9812345678", "email": "anjali@inspection.org", "gender": "Female", "address": "CMPDI Campus, Kanke Road, Ranchi", "id_type": "PAN Card", "id_number": "ABCDE1234F"},
        {"id": 3, "name": "Suresh Yadav", "mobile": "9934567890", "email": "suresh@equipment.in", "gender": "Male", "address": "Ramgarh Cantt, Jharkhand", "id_type": "Driving License", "id_number": "JH01-202200192"},
        {"id": 4, "name": "Deepak Mahato", "mobile": "9701234567", "email": "deepak@coalcontractor.com", "gender": "Male", "address": "Birkuri Village, Piparwar", "id_type": "Govt Photo ID", "id_number": "CCL-CONT-9912"}
    ]

    visits = [
        {
            "id": 1,
            "pass_code": "CCL-PASS-801",
            "visitor_id": 1,
            "employee_id": 1,
            "department_id": 1,
            "purpose": "Official Machinery Procurement Meeting",
            "visit_date": today_str,
            "expected_duration": "2 Hours",
            "vehicle_number": "JH01-AZ-4412",
            "gate_number": "Gate 1 (Main Entrance)",
            "status": "Inside",
            "entry_time": "09:30:00",
            "exit_time": None,
            "qr_code_svg": generate_qr_svg("CCL-PASS-801"),
            "rejection_reason": None,
            "created_at": f"{today_str} 09:15:00"
        },
        {
            "id": 2,
            "pass_code": "CCL-PASS-802",
            "visitor_id": 2,
            "employee_id": 2,
            "department_id": 5,
            "purpose": "Workshop Safety Audit",
            "visit_date": today_str,
            "expected_duration": "4 Hours",
            "vehicle_number": "JH02-B-9901",
            "gate_number": "Gate 2 (Workshop Gate)",
            "status": "Completed",
            "entry_time": "08:15:00",
            "exit_time": "12:45:00",
            "qr_code_svg": generate_qr_svg("CCL-PASS-802"),
            "rejection_reason": None,
            "created_at": f"{today_str} 08:00:00"
        },
        {
            "id": 3,
            "pass_code": "CCL-PASS-803",
            "visitor_id": 3,
            "employee_id": 3,
            "department_id": 2,
            "purpose": "Heavy Earthmoving Equipment Inspection",
            "visit_date": today_str,
            "expected_duration": "3 Hours",
            "vehicle_number": "JH24-C-3388",
            "gate_number": "Gate 1 (Main Entrance)",
            "status": "Pending",
            "entry_time": None,
            "exit_time": None,
            "qr_code_svg": generate_qr_svg("CCL-PASS-803"),
            "rejection_reason": None,
            "created_at": f"{today_str} 10:00:00"
        },
        {
            "id": 4,
            "pass_code": "CCL-PASS-804",
            "visitor_id": 4,
            "employee_id": 5,
            "department_id": 4,
            "purpose": "Contractor Gate Pass Verification",
            "visit_date": today_str,
            "expected_duration": "5 Hours",
            "vehicle_number": "JH01-X-1234",
            "gate_number": "Gate 3 (Mines Entrance)",
            "status": "Inside",
            "entry_time": "10:15:00",
            "exit_time": None,
            "qr_code_svg": generate_qr_svg("CCL-PASS-804"),
            "rejection_reason": None,
            "created_at": f"{today_str} 10:10:00"
        }
    ]

    gate_logs = [
        {"id": 1, "visit_id": 1, "gate_number": "Gate 1 (Main Entrance)", "action": "ENTRY", "timestamp": f"{today_str} 09:30:00", "guard_name": "Guard Gate 1"},
        {"id": 2, "visit_id": 2, "gate_number": "Gate 2 (Workshop Gate)", "action": "ENTRY", "timestamp": f"{today_str} 08:15:00", "guard_name": "Guard Gate 2"},
        {"id": 3, "visit_id": 2, "gate_number": "Gate 2 (Workshop Gate)", "action": "EXIT", "timestamp": f"{today_str} 12:45:00", "guard_name": "Guard Gate 2"},
        {"id": 4, "visit_id": 4, "gate_number": "Gate 3 (Mines Entrance)", "action": "ENTRY", "timestamp": f"{today_str} 10:15:00", "guard_name": "Guard Gate 3"}
    ]

    return {
        "departments": depts,
        "employees": employees,
        "visitors": visitors,
        "visits": visits,
        "users": users,
        "gate_logs": gate_logs
    }

def get_db():
    return None

def init_db():
    pass
