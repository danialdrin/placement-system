# HireSync - Campus Placement Management System

## 🚀 Project Overview
**HireSync** is a premium, real-time campus placement management system designed to bridge the gap between students, companies, and placement officers. It features a modern **Glassmorphism UI**, robust backend logic, and automated data handling to streamline the recruitment process.

---

## 🛠 Technical Stack
### **Backend**
*   **Language:** Python 3.12
*   **Framework:** Flask (Web Framework)
*   **Database:** MySQL (Relational Database)
*   **Libraries:** 
    *   `mysql-connector-python`: For database connectivity.
    *   `pandas` & `openpyxl`: For high-speed Excel data processing.
    *   `flask-login`: For secure authentication and role-based access control.

### **Frontend**
*   **Structure:** Semantic HTML5
*   **Styling:** Vanilla CSS3 (Custom Design System)
*   **Aesthetics:** Dark Theme, Glassmorphism, Responsive Grid.
*   **Icons:** Lucide Icons (SVG-based, high performance).
*   **Interactivity:** Vanilla JavaScript (ES6+).

---

## 🏛 Architecture & Project Structure
```text
placement-system/
├── app.py                  # Core backend logic & routes
├── static/
│   ├── css/
│      └── style.css       # Unified design system & animations
│   
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Master layout
│   ├── admin.html          # Admin Activity Hub
│   ├── admin_students.html # Student Management
│   ├── companies.html      # Partner Portfolio
│   ├── admin_jobs.html     # Application & Interview Tracking
│   ├── student.html        # Student Dashboard
│   └── ...                 # Auth & Import templates
└── placement_db.sql        # Database schema
```

---

## 💎 Core Features (A - Z)

### **1. Authentication & Role-Based Access**
*   Secure login system for two distinct roles: **Admin** and **Student**.
*   Protected routes ensure students cannot access admin data and vice versa.

### **2. Admin Dashboard (The Activity Hub)**
*   **Real-Time Analytics**: Live counters for Total Students, Active Companies, Placed Students, and Ongoing Interviews.
*   **Interactive Stat Cards**: Click any metric to dive deep into the specific filtered data.
*   **Recent Activity Feed**: Tracks newly added companies, recent job applications, and successful placements.

### **3. Student Management**
*   **Comprehensive Profiles**: Tracks name, email, CGPA, Department, and Arrears.
*   **Dynamic Eligibility**: Automatically identifies students with arrears or low CGPA and marks them as "Not Eligible" for jobs.
*   **Detailed Tracking**: See exactly how many interview calls each student has received.

### **4. Company & Job Portfolio**
*   **Partner Management**: Add, update, or track corporate partners.
*   **Job Offer Logic**: Define roles, locations, and packages (LPA) for each company.

### **5. Automated Excel Import System**
*   **Bulk Onboarding**: Upload hundreds of student or company records at once via Excel.
*   **Intelligent Validation**: Checks for duplicates, missing fields, and data types (e.g., non-numeric CGPA).
*   **Data Correction UI**: If an Excel file has errors, the system highlights them and allows the admin to fix them directly on the web before saving.

### **6. Placement Status & Interview Tracking**
*   **Multi-Stage Pipeline**: Applications flow through `Pending` → `Interview` → `Selected` or `Rejected`.
*   **Interview Integration**: Dedicated icons and counters to highlight students currently "on call" with companies.
*   **Bulk Management**: Admins can update statuses with a single click.

### **7. Advanced Search & Filtering**
*   **Global Search**: Powerful search across names, emails, and company roles.
*   **Contextual Filters**: Filter students by department or placement status. Filter applications by current stage.

### **8. Premium UI/UX**
*   **Glassmorphism Design**: Semi-transparent containers with blurred backgrounds for a state-of-the-art look.
*   **Responsive Layout**: Fully functional on desktops, tablets, and phones.
*   **Micro-Animations**: Smooth hover effects, transitions, and landing animations.

---

## 🗄 Database Design
The system uses a highly normalized MySQL schema:
1.  **`users`**: Handles login credentials and hashed passwords.
2.  **`students`**: Stores educational details and profile information.
3.  **`companies`**: Stores job offer details and corporate metadata.
4.  **`offers`**: The junction table connecting students to companies, tracking application dates and placement statuses.

---

## 🎯 Development Highlights (What We Accomplished)
1.  **Refactored the Architecture**: Moved from static lists to a dynamic, inter-connected dashboard.
2.  **Built the Import Engine**: Created a custom logic to handle Excel files with real-time error correction.
3.  **Enhanced Aesthetics**: Implemented a dark-mode first design with custom-styled dropdowns and interactive cards.
4.  **Optimized Queries**: Used parameterized SQL for search to ensure performance and prevent SQL injection.
5.  **Placement Pipeline**: Introduced the "Interview" stage to provide better visibility into the recruitment funnel.

---

**HireSync** is now a production-ready, feature-rich tool for any educational institution.
