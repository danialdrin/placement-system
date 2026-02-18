# HireSync - Placement Management System

HireSync is a modern, full-stack placement management system designed to streamline the recruitment process for educational institutions. It provides a professional, high-end experience for both administrators and students using cutting-edge design principles.

## 📸 Dashboard Preview

![Admin Dashboard](https://raw.githubusercontent.com/danialdrin/placement-system/main/static/css/image/image.png)
*(Note: Replace with actual image path if hosted, or see local DOCUMENTATION.md for more visuals)*

---

## 📖 Project Documentation
For a complete **A - Z breakdown** of the technical stack, project architecture, and feature implementations, please refer to the:

👉 **[Detailed Project Documentation (DOCUMENTATION.md)](./DOCUMENTATION.md)**

---

## ✨ Key Features

- **💎 Premium Glassmorphism UI**: A stunning dark-themed interface with semi-transparent elements and smooth animations.
- **📊 Interactive Admin Hub**: Real-time tracking of students, companies, and placement metrics with clickable analytics.
- **🎥 Interview Pipeline**: A dedicated stage for tracking ongoing interview calls with specialized visual indicators.
- **📥 Smart Excel Import**: Bulk onboard students and companies with an intelligent error-correction interface.
- **🔍 Advanced Search & Filter**: Powerful, multi-parameter search for students, companies, and job offers.
- **🎓 Student Portal**: Personalized dashboards for students to track applications and discover opportunities.

## 🛠️ Tech Stack

- **Frontend**: HTML5, Vanilla CSS3 (Custom Design System), JavaScript (ES6+), Lucide Icons.
- **Backend**: Python 3.12, Flask.
- **Data Handling**: Pandas, OpenPyXL (Excel processing).
- **Database**: MySQL (Relational Schema).

## 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   pip install flask mysql-connector-python pandas openpyxl
   ```

2. **Database Setup**:
   - Create a database `placement_db` in MySQL.
   - Core tables: `users`, `students`, `companies`, `offers`.

3. **Run Application**:
   ```bash
   python app.py
   ```

---
Created with ❤️ for professional placement management.
