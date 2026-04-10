# How to Run the Online Parking Booking System

To get the web application up and running on your local machine, please follow these steps carefully.

**Important:** Ensure you are in the `online_parking_app` directory when executing these commands.

## 1. Open the Web Page

### Step 1: Activate the Virtual Environment

Before running the application, activate the Python virtual environment you created earlier. This ensures all necessary dependencies are available.

*   **On Windows (Command Prompt):**
    ```bash
    .\venv\Scripts\activate
    ```
*   **On Windows (PowerShell):**
    ```powershell
    .\venv\Scripts\activate
    ```
*   **On macOS/Linux:**
    ```bash
    source venv/bin/activate
    ```

### Step 2: Set the FLASK_APP Environment Variable

This tells Flask where to find your application.

*   **On Windows (Command Prompt):**
    ```bash
    set FLASK_APP=run.py
    ```
*   **On Windows (PowerShell):**
    ```powershell
    $env:FLASK_APP = "run.py"
    ```
*   **On macOS/Linux:**
    ```bash
    export FLASK_APP=run.py
    ```

### Step 3: Run the Flask Development Server

Now you can start the web server.

```bash
flask run
```

### Step 4: Access the Application

Once the server is running, open your web browser and navigate to:

[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 2. Access the Database

The application uses an SQLite database, which stores all your data (users, spots, bookings). The database file is called `parking.db`.

### Database File Location:

You can find the database file at:
`online_parking_app/instance/parking.db`

### How to View the Database Contents:

I recommend using **DB Browser for SQLite**, a free and open-source visual tool that makes it easy to inspect SQLite databases.

1.  **Download DB Browser for SQLite:**
    *   Visit their official website: [http://sqlitebrowser.org/](http://sqlitebrowser.org/)
    *   Download and install the version appropriate for your operating system.

2.  **Open the `parking.db` file:**
    *   Launch DB Browser for SQLite.
    *   Click on the "Open Database" button (or go to `File > Open Database...`).
    *   Navigate to your project directory (`online_parking_app/instance/`).
    *   Select the `parking.db` file and click "Open".

3.  **Browse the data:**
    *   In DB Browser for SQLite, you will see a list of tables (e.g., `user`, `parking_spot`, `booking`) in the left-hand panel.
    *   Select a table to view its structure (schema).
    *   Go to the "Browse Data" tab to see the actual records stored in that table. You can observe updates as you interact with the web application.

---

**Admin Credentials for Testing:**

When you run the application, an admin user is automatically created for convenience:
*   **Username:** `admin`
*   **Password:** `admin`

You can use these credentials to log in and access the administrative features.
