Akaris Backend (Prototype)
===========================

This project is the backend API for the Akaris mobile farming system, built using FastAPI and PostgreSQL.

How to Run the Project
----------------------

Follow the steps below:

1. Activate your virtual environment (in Terminal):
   
   - Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   - .\venv\Scripts\Activate.ps1

2. Install required packages:

   pip install -r requirements.txt

3. Create a PostgreSQL database on your local machine:
   - Set up a new database manually (e.g., using pgAdmin or Dbeaver).
   - Note: Since localhost cannot be shared, the database location will be updated later when deploying.

4. Create the database tables using the provided structure:

   python src/models/createTable.py

5. Run the FastAPI app with Uvicorn:

   uvicorn src.main:app --reload

6. Test API endpoints using a tool like Postman:

   Example:
   http://127.0.0.1:8000/{route-name}

Notes
-----
- Make sure PostgreSQL service is running before creating tables.
- Default database credentials are currently set for local development.
- After creating your local database, update your DATABASE_URL inside src/database.py file according to your own PostgreSQL username, password, and database name.
- Database connection settings can be changed later for production or shared testing.
