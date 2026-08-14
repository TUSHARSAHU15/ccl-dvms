# Deployment & Live Hosting Guide – CCL Digital Visitor Management System

This guide explains how to make your **Central Coalfields Limited (CCL) DVMS** live—both for **Local Network / Gate Intranet Deployment** and **Public Cloud Deployment**.

---

## 📱 1. Live Local Network / Intranet Deployment (Active Right Now!)

The application server is configured to bind to `0.0.0.0:5000`. This means **any phone, tablet, gate guard computer, or laptop** connected to the same Wi-Fi / Local Network can access the live application!

### Live Intranet URL:
👉 **`http://10.64.161.251:5000`**

- **Gate Guards**: Open `http://10.64.161.251:5000/security` on mobile/tablet at gate entrances.
- **Employees**: Open `http://10.64.161.251:5000/employee` on office PCs to approve visitor requests.
- **Admin**: Open `http://10.64.161.251:5000/dashboard` on HQ administrative desktops.

---

## ☁️ 2. Free Public Cloud Deployment Options

### Option A: Render.com (Recommended - 100% Free Public SSL URL)

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial CCL DVMS commit"
   git remote add origin https://github.com/YOUR_USERNAME/ccl-dvms.git
   git branch -M main
   git push -u origin main
   ```

2. **Deploy on Render**:
   - Log into [Render.com](https://render.com) (sign up with GitHub).
   - Click **New +** -> **Web Service**.
   - Connect your `ccl-dvms` GitHub repository.
   - Configure the following settings:
     - **Name**: `ccl-dvms`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn wsgi:application`
   - Click **Create Web Service**.
   - Your live public URL will be generated (e.g., `https://ccl-dvms.onrender.com`).

---

### Option B: PythonAnywhere.com (Free Python Hosting)

1. Sign up for a free account at [PythonAnywhere.com](https://www.pythonanywhere.com).
2. Upload the `ccl-dvms-flask` folder via the **Files** tab.
3. Open the **Web** tab -> Click **Add a new web app**.
4. Select **Manual Configuration** -> **Python 3.11**.
5. Set:
   - **Source Code**: `/home/yourusername/ccl-dvms-flask`
   - **WSGI configuration file**: Edit file to point to `from app import application`.
6. Click **Reload**. Your live site will be: `https://yourusername.pythonanywhere.com`.

---

### Option C: Railway.app

1. Sign up at [Railway.app](https://railway.app).
2. Click **New Project** -> **Deploy from GitHub Repo**.
3. Select `ccl-dvms`. Railway automatically detects the `Procfile` (`web: gunicorn wsgi:application`) and deploys automatically!

---

## 🛠️ Pre-Configured Production Files Included in Project

- [`wsgi.py`](file:///c:/Users/tusha/OneDrive/Desktop/Project/ccl-dvms-flask/wsgi.py): Production WSGI application launcher.
- [`Procfile`](file:///c:/Users/tusha/OneDrive/Desktop/Project/ccl-dvms-flask/Procfile): Process file for Gunicorn cloud deployments.
- [`requirements.txt`](file:///c:/Users/tusha/OneDrive/Desktop/Project/ccl-dvms-flask/requirements.txt): Dependencies file (`Flask`, `Flask-SQLAlchemy`, `qrcode`, `reportlab`, etc.).
- [`database.py`](file:///c:/Users/tusha/OneDrive/Desktop/Project/ccl-dvms-flask/database.py): Relational database seeder (SQLite with JSON fallback).
- [`run_app.bat`](file:///c:/Users/tusha/OneDrive/Desktop/Project/ccl-dvms-flask/run_app.bat): 1-click local launcher.
