# UP Govt School Management Portal (UP Shiksha Parishad)

![Platform](https://img.shields.io/badge/Platform-Web-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![Flask](https://img.shields.io/badge/Framework-Flask-black)
![Database](https://img.shields.io/badge/Database-PostgreSQL%20(Supabase)-336791)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange)

A modern, full-stack, AI-powered School Management System designed specifically for Uttar Pradesh Government Schools. It features a unique custom UI theme, providing administrators with a secure, centralized dashboard to manage student records, attendance, exam results, government material distribution, and visual analytics.

### Live Demo
**Access the live portal here:** [https://govt-school-portal.onrender.com/](https://govt-school-portal.onrender.com/)

---

## 1. Technical Architecture

The application follows a monolithic client-server architecture with a decoupled AI service layer, engineered to digitize administrative and academic operations.

*   **Presentation Layer (Frontend):** Developed using HTML5, Tailwind CSS, and Alpine.js. The interface employs a custom "Blackboard & Register" theme, utilizing CSS radial gradients and SVG displacement filters to simulate physical classroom elements without relying on heavy background images. State management for toggles, voice-recognition states, and bulk-selection (e.g., the Student Promotion module) is handled client-side via Alpine.js.
*   **Application Layer (Backend):** Powered by Python and Flask. The backend handles HTTP routing, server-side business logic (e.g., dynamic grade calculations, percentage formatting), session management, and cryptographic functions using Werkzeug Security.
*   **Data Layer (Database):** Hosted on Supabase (PostgreSQL). It acts as the single source of truth, heavily relying on relational constraints (Foreign Keys) to link all modules back to a central student directory.

---

## 2. Core Functional Modules

*   **Master Student Directory:** A central repository handling student admissions, demographics, and unique roll number assignments.
*   **Academic Performance Engine:** Records subject-wise marks against dynamic `max_marks` parameters. The Python backend automatically computes total scores, calculates percentages, and assigns academic grades before committing the record to the database.
*   **Monthly Attendance & Analytics:** Tracks total working days versus present days per student per month. This data is aggregated by SQL and visualized on the administrative dashboard using Chart.js.
*   **Material Distribution Tracker:** A specialized administrative module to monitor the disbursement of government-provided schemes (uniforms, textbooks, shoes, and bags) using boolean tracking.
*   **Bulk Student Promotion:** Allows administrators to filter students by their current class, select multiple records simultaneously, and execute a bulk database update to promote them to the next academic tier.

---

## 3. Database Schema & Architecture

The system utilizes a secure PostgreSQL relational database with 5 core tables. Data integrity is maintained using Foreign Keys linking back to the master `students` table.

### Table 1: schools (Admin Authentication)
Handles administrative credentials and portal access.
```sql
CREATE TABLE schools (
    school_id SERIAL PRIMARY KEY,
    school_code VARCHAR UNIQUE NOT NULL,
    school_name VARCHAR,
    email VARCHAR UNIQUE,
    password VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_admin BOOLEAN DEFAULT FALSE
);
