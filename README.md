# UP Govt School Management Portal (UP Shiksha Parishad)

![Platform](https://img.shields.io/badge/Platform-Web-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![Flask](https://img.shields.io/badge/Framework-Flask-black)
![Database](https://img.shields.io/badge/Database-PostgreSQL%20(Supabase)-336791)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange)

A modern, full-stack, AI-powered School Management System designed specifically for Uttar Pradesh Government Schools. It features a custom user interface, providing administrators with a secure, centralized dashboard to manage student records, attendance, exam results, government material distribution, and visual analytics.

### Live Demo
Access the live portal here: [https://govt-school-portal.onrender.com/](https://govt-school-portal.onrender.com/)

---

## 1. System Architecture & UI Design

The application follows a monolithic client-server architecture with a decoupled AI service layer.

*   **Frontend (UI/UX):** Developed using HTML5, Tailwind CSS, and Alpine.js. The interface employs a custom "Blackboard & Register" theme. It utilizes CSS radial gradients and SVG displacement filters to simulate physical classroom elements (chalk dust, register lines) without heavy background images. State management for UI toggles, voice-recognition states, and bulk-selection is handled client-side via Alpine.js.
*   **Backend (Server Logic):** Powered by Python and Flask. The backend application (`app.py`) handles HTTP routing, server-side business logic (e.g., dynamic grade calculations, percentage formatting), session management, and cryptographic functions.
*   **Database (Data Layer):** Hosted on Supabase (PostgreSQL). It acts as the single source of truth, heavily relying on relational constraints (Foreign Keys) to link all modules back to a central student directory.

---

## 2. Core Features & Modules

*   **Master Student Directory:** Complete CRUD operations for student admission, demographics, and unique roll number assignments.
*   **Academic Performance Engine:** Records subject-wise marks against dynamic maximum marks parameters. The backend automatically computes total scores, calculates percentages, and assigns academic grades.
*   **Monthly Attendance Tracker:** Tracks total working days versus present days per student per month.
*   **Material Distribution Tracker:** Monitors the disbursement of government-provided schemes (uniforms, textbooks, shoes, and bags) using boolean flags.
*   **Visual Analytics Dashboard:** Data is aggregated via SQL and visualized using Chart.js, rendering metrics like overall attendance health, class strength, and gender distribution.
*   **Bulk Student Promotion:** Allows administrators to filter students by their current class, select multiple records simultaneously, and execute a bulk database update to promote them to the next academic session.

---

## 3. Technology Stack

*   **Frontend:** HTML5, CSS3, Tailwind CSS, Alpine.js, Chart.js
*   **Backend:** Python, Flask, Werkzeug Security, Psycopg2 (Database Adapter)
*   **Database:** PostgreSQL (Hosted on Supabase)
*   **AI Integration:** Google Gemini API (LLM), Browser Web Speech API (Speech-to-Text)

---

## 4. Database Structure

The system utilizes a secure PostgreSQL relational database. Data integrity is maintained using Foreign Keys linking back to the master student table. The database consists of the following 6 core tables:

1.  **schools:** Handles administrative credentials, school codes, and portal access authorization logic.
2.  **students:** The core master directory. Stores basic demographics, roll numbers, and class details. All other records reference the `student_id` from this table.
3.  **exam_results:** Stores academic metrics dynamically calculated by the backend (subject marks, total marks, percentage, and grade).
4.  **monthly_attendance:** Tracks aggregate monthly attendance (working days vs. present days) used for generating visualization charts.
5.  **material_distribution:** Tracks the distribution status of state-sponsored materials (uniforms, books, bags, shoes) using boolean tracking.
6.  **teachers:** Designed for future expansion to manage faculty records and class assignments.

---

## 5. The AI & Voice Search Subsystem

The portal features a "Smart AI Query" module, allowing administrators to query the PostgreSQL database using spoken regional languages without writing SQL.

*   **Speech-to-Text Pipeline:** Utilizes the browser-native Web Speech API configured with the `hi-IN` language model. This enables real-time transcription of regional queries (Hindi/English/Hinglish) directly into text strings without requiring external audio processing servers.
*   **Context-Aware Prompt Engineering:** The transcribed text is sent to the Flask backend, where it is packaged into a strict system prompt. This prompt injects the exact database schema and the active `school_id` to provide the AI with total context.
*   **Text-to-SQL Generation:** The Google Gemini API processes the prompt and translates the natural language request into a raw PostgreSQL query, which is then executed and rendered as an HTML table dynamically.

---

## 6. Multi-Tenant Security & Data Isolation

Security is enforced at the application layer to ensure absolute data isolation across different registered schools:

*   **Session-Based Tenant Isolation:** Upon successful administrative authentication, the `school_id` is stored in a secure, encrypted server-side session. Every subsequent backend SQL query automatically injects this `school_id` as a strict `WHERE` clause filter, ensuring one school can never query or view another school's data.
*   **Strict Type Casting:** To prevent PostgreSQL type-mismatch errors between application strings and database integers, tenant filtering utilizes explicit SQL casting (`CAST(school_id AS VARCHAR)`).
*   **Cryptographic Hashing:** Passwords are never stored or transmitted in plaintext. The system utilizes `pbkdf2:sha256` hashing (via Werkzeug) to secure administrative credentials.
*   **AI Prompt Injection Prevention:** The system prompt explicitly restricts the AI to generate `SELECT` statements only. `INSERT`, `UPDATE`, `DELETE`, or `DROP` commands are structurally blocked by the backend execution engine to prevent accidental or malicious data corruption.
