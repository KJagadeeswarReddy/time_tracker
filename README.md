# Time Management Web Application

This is a Streamlit-based web application for time management and tracking. It allows users to categorize their activities, track time spent on each category, log sessions, and visualize their progress.

## Features

*   **Category Management:** Add, select, and manage different categories for activities (e.g., Study, Work, Exercise).
*   **Timer:** A built-in timer to track time spent on the currently selected category.
*   **Session Logging:** Log sessions with details like date, start/end time, duration, work done, and efficiency.
*   **Data Visualization:** Visualize session durations over time using interactive charts.
*   **Data Persistence:** Uses SQLite database to store data, ensuring data is not lost between sessions.
*   **Units Tracking:** Tracks units in `UU:HH:MM:SS` format, incrementing UU by 1 for every 100 hours of work.

## How to Run (Locally)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/KJagadeeswarReddy/time_tracker.git
    cd time_tracker
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```bash
    streamlit run app.py
    ```

## Deployment (Streamlit Community Cloud)

This application is designed to be easily deployed on Streamlit Community Cloud:

1.  **Push your code to GitHub:**  Make sure this `README.md`, `app.py`, `requirements.txt`, `.gitignore`, and `LICENSE` files are in the root of your repository.
2.  **Connect Streamlit Community Cloud to your GitHub:**  Follow the instructions on the Streamlit Community Cloud website to connect your account.
3.  **Deploy:**  Select your repository and branch, and Streamlit will deploy your app.

## Dependencies

The following Python packages are required:

*   streamlit
*   plotly
*   pandas
*   sqlite3 (This is usually preinstalled, but we include it for completeness in `requirements.txt`)

These are listed in the `requirements.txt` file.

## Database

The application uses an SQLite database (`time_tracker.db`) to store data.  This file will be created automatically in the same directory as `app.py`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.