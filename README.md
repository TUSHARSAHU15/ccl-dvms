# Central Coalfields Limited (CCL) – Digital Visitor Management System (DVMS)

A complete, production-ready **Digital Visitor Management System (DVMS)** developed specifically for **Central Coalfields Limited (CCL)** (a Miniratna Subsidiary of Coal India Limited). 

This system digitizes the traditional paper-based visitor registers used across CCL headquarters, mine offices, central workshops, and regional areas—automating visitor registration, host employee approval, QR pass generation, entry/exit tracking, emergency roll call, and audit reporting.

---

## 🚀 Recommended Tech Stack (BCA Internship Project)

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+) | Structure, styling, and client-side interactivity |
| **UI Framework** | Bootstrap 5 + FontAwesome / Bootstrap Icons | Enterprise responsive design & clean UI components |
| **Backend** | Python + Flask / WSGI | Server-side routing, REST APIs, session & role management |
| **Database** | SQLite / MySQL | Store visitors, host employees, departments, gate logs, and pass statuses |
| **QR Code Engine**| Python QRCode SVG generator + JS Scanner | Generate scannable QR passes & scan passes at security gates |
| **Dashboard Charts**| Chart.js | Real-time visitor traffic analytics & department distribution graphs |
| **Emergency Audit**| Real-Time Roll Call Engine | 1-Click safety evacuation tracking listing everyone inside CCL premises |
| **Data Export** | CSV Exporter | Export daily/monthly visitor logs for official audit & security compliance |

---

## 🏢 System Architecture & Roles

```
                      VISITOR / SECURITY GUARD / EMPLOYEE / ADMIN
                                           │
                                           ▼
                                 Web Browser Interface
                        (Bootstrap 5 + Chart.js + HTML5-QRCode)
                                           │
                                           ▼
                                Python + Flask Backend
                                           │
                     ┌─────────────────────┴─────────────────────┐
                     ▼                                           ▼
         SQLite / MySQL Database                      Python QR Pass Engine
  (Users, Depts, Emps, Visitors, Visits)                  (Scannable SVG/PNG)
```

### 1. Admin Control Center (`/dashboard`)
- Real-Time KPI Cards (Visitors Today, Currently Inside, Pending Approvals, Completed Visits, Total Host Employees).
- Chart.js Hourly Traffic Trends & Department Breakdown.
- Master Visitor Register with search, status filtering, and CSV export.
- Employee & Department Directory CRUD management.
- 1-Click **Emergency Evacuation Roll Call** for mine safety compliance.

### 2. Security Guard Gate Portal (`/security`)
- Express Visitor Registration form (Name, Mobile, Email, Address, Govt ID type & number).
- Live Camera Photo Snap simulation / file preview.
- Host Employee selection & automatic department resolution.
- Live QR Pass Scanner & manual pass code entry for express Check-In and Check-Out.
- Active Gate Monitor showing all visitors currently inside premises.

### 3. Employee Approval Inbox (`/employee`)
- Real-time visitor approval request cards.
- 1-Click **Approve** or **Reject** (with security reason input).
- Visitor host history.

### 4. Visitor Self-Service Kiosk (`/visitor` & `/pass/<pass_code>`)
- Pass status lookup by mobile number or pass ID.
- Printable Digital QR Pass Badge with visitor badge layout, host details, gate number, emergency helpline, and mine safety rules.

---

## 📁 Project File Structure

```
ccl-dvms-flask/
├── app.py                  # Main Flask application & WSGI REST API server
├── database.py             # Database engine & auto-seeder (SQLite + JSON fallback)
├── requirements.txt        # Python dependencies
├── run_app.bat             # One-click Windows batch launcher
├── README.md               # Project documentation
├── static/
│   ├── css/
│   │   └── style.css      # CCL Enterprise theme stylesheet
│   └── js/
│       └── main.js        # Live clock, photo capture, Chart.js & API handlers
└── templates/
    ├── base.html           # Shared layout, navbar, live clock & emergency roll call modal
    ├── dashboard.html      # Admin Control Center
    ├── security.html       # Security Guard Gate Pass & Scanner Portal
    ├── employee.html       # Employee Visitor Approval Portal
    ├── visitor.html        # Visitor Self-Service Kiosk
    └── pass.html           # Printable Digital QR Pass Badge
```

---

## ⚙️ How to Run the Application

### Option A: Direct Python Execution
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

### Option B: Windows Batch Launcher
Double-click **`run_app.bat`** in the project folder.

---

## 🗄️ Pre-Populated Seed Data

The project comes pre-seeded with realistic CCL data for immediate presentation:
- **Departments**: Central Headquarters Ranchi, Piparwar Open Cast Project, Barka-Sayal Area, Rajrappa Area, Central Workshop Barkakana, N K Area.
- **Host Employees**: Rajesh Kumar (GM Mining), Sunita Sharma (Chief Engineer), Amit Varma (Safety Officer), etc.
- **Visits**: Pre-populated active visitors inside premises, completed visits, and pending approvals.

---

## 🏆 Ideal for BCA Internship Project
This project showcases full-stack web development skills, database design, REST API construction, QR code generation/scanning, role-based workflows, and real-world safety compliance—making it an outstanding BCA internship submission for Central Coalfields Limited.
