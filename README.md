# UP Govt School Management Portal (UP Shiksha Parishad)

![Platform](https://img.shields.io/badge/Platform-Web-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![Flask](https://img.shields.io/badge/Framework-Flask-black)
![Database](https://img.shields.io/badge/Database-PostgreSQL%20(Supabase)-336791)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange)

A modern, full-stack, AI-powered School Management System designed specifically for Uttar Pradesh Government Schools. It features a unique "Blackboard & Register" UI theme, providing administrators with a secure, centralized dashboard to manage student records, attendance, exam results, government material distribution, and visual analytics.

### Live Demo
**Access the live portal here:** [https://govt-school-portal.onrender.com/](https://govt-school-portal.onrender.com/)

---

## Key Features

*   **Secure Admin Portal:** Multi-tenant architecture with encrypted passwords (`pbkdf2:sha256`) and strict session management isolated by `school_code`.
*   **Master Student Directory:** Complete CRUD operations for student admission, demographics, and record management.
*   **Visual Analytics & Dashboards:** Interactive charts (via Chart.js) tracking school strength, gender ratios, and overall attendance trends.
*   **Advanced Exam Results:** Dynamic result calculation including total marks, percentage, and automated grading systems.
*   **Govt Schemes Tracker:** Track the distribution of government-provided materials (Uniforms, Books, Shoes, Bags) for each student.
*   **Student Promotion Module:** Bulk promote students to the next academic session effortlessly.
*   **Smart AI Assistant (Voice & Text):** Integrated with Google Gemini API and Web Speech API. Administrators can ask questions in Hindi or English (e.g., "Class 5 ke bacche dikhao"), and the AI securely translates it into read-only SQL queries to fetch real-time data.

---

## Tech Stack

**Frontend:**
*   HTML5 & CSS3
*   Tailwind CSS (Custom Blackboard & Glassmorphism Design)
*   Alpine.js (Lightweight reactive UI components)
*   Chart.js (Data visualization)

**Backend:**
*   Python
*   Flask (Web Framework)
*   Werkzeug Security (Password Hashing)
*   Psycopg2 (PostgreSQL adapter)

**Database & AI:**
*   Supabase (PostgreSQL Database Hosting)
*   Google Gemini API (Text-to-SQL logic)

---

## Database Architecture

The system utilizes a secure PostgreSQL relational database with the following core tables:
1.  `schools` - Admin authentication and school details.
2.  `students` - Master record, linked via foreign keys to all other tables.
3.  `exam_results` - Academic performance tracking.
4.  `monthly_attendance` - Monthly present/working days records.
5.  `material_distribution` - Government schemes tracking.

*(Strict data isolation is enforced using `CAST(school_id AS VARCHAR)` across all backend queries to prevent cross-school data leaks).*

---

## Local Installation & Setup

Follow these steps to run the project on your local machine.

### 1. Clone the repository
```bash
git clone [https://github.com/your-username/govt-school-portal.git](https://github.com/your-username/govt-school-portal.git)
cd govt-school-portal
