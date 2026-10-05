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

## Technical Architecture & System Overview

The application follows a monolithic client-server architecture with a decoupled AI service layer, engineered to digitize administrative and academic operations.

### 1. System Architecture
*   **Presentation Layer (Frontend):** Developed using HTML5, Tailwind CSS, and Alpine.js. The interface employs a custom "Blackboard & Register" theme, utilizing CSS radial gradients and SVG displacement filters to simulate physical classroom elements without relying on heavy background images. State management for toggles, voice-recognition states, and bulk-selection (e.g., the Student Promotion module) is handled client-side via Alpine.js.
*   **Application Layer (Backend):** Powered by Python and Flask. The backend handles HTTP routing, server-side business logic (e.g., dynamic grade calculations, percentage formatting), session management, and cryptographic functions using Werkzeug Security.
*   **Data Layer (Database):** Hosted on Supabase (PostgreSQL). It acts as the single source of truth, heavily relying on relational constraints (Foreign Keys) to link all modules back to a central student directory.

### 2. Multi-Tenant Security & Data Isolation
Security is enforced at the application layer to ensure absolute data isolation across different registered schools:
*   **Session-Based Tenant Isolation:** Upon successful administrative authentication, the `school_id` is stored in a secure, encrypted server-side session. Every subsequent backend SQL query automatically injects this `school_id` as a strict `WHERE` clause filter, ensuring School A can never query or view School B's data.
*   **Strict Type Casting:** To prevent PostgreSQL type-mismatch errors between application strings and database integers, tenant filtering utilizes explicit casting (`CAST(school_id AS VARCHAR)`).
*   **Cryptographic Hashing:** Passwords are never stored or transmitted in plaintext. The system utilizes PBKDF2 with SHA-256 hashing to secure administrative credentials.

### 3. The AI & Voice Search Subsystem
The portal features a "Smart AI Query" module, allowing administrators to query the PostgreSQL database using spoken Hindi, English, or Hinglish.
*   **Speech-to-Text Pipeline:** Utilizes the browser-native Web Speech API configured with the `hi-IN` language model. This enables real-time transcription of regional queries directly into text strings without requiring external audio processing servers.
*   **Context-Aware Prompt Engineering:** The transcribed text is sent to the Flask backend, where it is packaged into a strict prompt. This prompt injects the exact database schema (tables, columns, relationships) and the active `school_id` to provide the AI with total context.
*   **Text-to-SQL Generation:** The Google Gemini API processes the prompt and translates the natural language request into a raw PostgreSQL query.
*   **Execution Guardrails:** The system prompt explicitly restricts the AI to generate `SELECT` statements only. `INSERT`, `UPDATE`, `DELETE`, or `DROP` commands are structurally blocked to prevent accidental or malicious data corruption. 

### 4. Core Functional Modules
*   **Master Student Directory:** A central repository handling student admissions, demographics, and unique roll number assignments.
*   **Academic Performance Engine:** Records subject-wise marks against dynamic `max_marks` parameters. The Python backend automatically computes total scores, calculates percentages, and assigns academic grades before committing the record to the database.
*   **Monthly Attendance & Analytics:** Tracks total working days versus present days per student per month. This data is aggregated by SQL and visualized on the administrative dashboard using Chart.js.
*   **Material Distribution Tracker:** A specialized administrative module to monitor the disbursement of government-provided schemes (uniforms, textbooks, shoes, and bags) using boolean tracking.
*   **Bulk Student Promotion:** Allows administrators to filter students by their current class, select multiple records simultaneously, and execute a bulk database update to promote them to the next academic tier.

---

## Tech Stack
*   **Frontend:** HTML5, CSS3, Tailwind CSS, Alpine.js, Chart.js
*   **Backend:** Python, Flask, Werkzeug Security, Psycopg2
*   **Database:** PostgreSQL (Supabase)
*   **AI Integration:** Google Gemini API, Web Speech API

---

## Application Security Note
*   **AI Prompt Injection Prevention:** The Gemini AI prompt is hardcoded at the backend level to strictly allow `SELECT` statements only. The backend execution engine acts as a secondary firewall to ensure no destructive operations can be processed, keeping the database fully secure.
