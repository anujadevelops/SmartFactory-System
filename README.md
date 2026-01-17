# Smart Manufacturing Management System

An integrated industrial AI platform designed to manage manufacturing workflows through real-time telemetry and predictive analytics. This system facilitates collaboration between three core operational roles: the **Operator**, the **Manager**, and the **Analyst**.

## 🏭 Core Features

* **Real-Time Monitoring:** High-fidelity Operator HUD with 3D digital twin visualization for monitoring engine RPM and core temperatures.
* **Intelligent Workflow:** Automated Kanban system for managing production tasks from "Pending" to "Completed" status.
* **Predictive AI:** Cortex-AI engine that monitors system health and provides autonomous repair alerts or material restock suggestions.
* **Financial Intelligence:** Live tracking of revenue, operational costs, and net profit margins based on production yield.
* **Role-Based Access:** Secure authentication portal with dedicated dashboards for different user designations.

## 🛠️ Technology Stack

* **Backend:** Python (Flask) with Flask-SocketIO for real-time bidirectional communication.
* **Frontend:** HTML5, CSS3 (Glassmorphism UI), and JavaScript (ES6+).
* **Visualization:** Three.js for 3D digital twins and Chart.js for analytical data streaming.
* **Security:** Werkzeug security for hashed password authentication.

## 📋 System Architecture

1.  **Operator Node:** Manages the factory floor, executes production orders, and reports system health.
2.  **Manager Node:** Oversees financial performance, manages client orders, and dispatches material restocks.
3.  **Analyst Node:** Performs deep spectral scans, tunes AI logic, and provides QA authorization for completed goods.
4.  **e-Dukaan Portal:** A public-facing e-commerce interface for direct factory ordering by customers.

## 🚀 Getting Started

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/anujadevelops/SmartFactory-System.git](https://github.com/anujadevelops/SmartFactory-System.git)
    ```
2.  **Install dependencies:**
    ```bash
    pip install flask flask-socketio
    ```
3.  **Run the application:**
    ```bash
    python app.py
    ```
4.  **Access the portal:** Navigate to `http://127.0.0.1:5000/login.html` in your browser.
