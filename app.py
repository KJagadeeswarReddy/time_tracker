import streamlit as st
import time
import datetime
import sqlite3
import plotly.express as px
import pandas as pd
import streamlit_authenticator as stauth

# --- Database Functions (SQLite) --- (remains the same)
def create_database():
    conn = sqlite3.connect('time_tracker.db')  # Connect or create if it doesn't exist
    cursor = conn.cursor()

    # Create the 'categories' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    # Create the 'session_log' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            duration TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            work_done TEXT,
            efficiency INTEGER,
            user_id TEXT NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    ''')

    # Create 'total_times' table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS total_times (
        category_id INTEGER PRIMARY KEY,
        total_seconds INTEGER NOT NULL,
        user_id TEXT NOT NULL,
        FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    conn.commit()
    conn.close()

# --- Data Loading (SQLite) --- (modified to load data for a specific user)

def load_data(username):
    create_database()  # Ensure tables exist

    categories = []
    session_log = []
    total_times = {}

    conn = sqlite3.connect('time_tracker.db')
    cursor = conn.cursor()

    # Load Categories (all categories are still global)
    for row in cursor.execute("SELECT id, name FROM categories"):
        categories.append(row[1])

    # Load Session Log (for the specific user)
    for row in cursor.execute('''
        SELECT sl.date, sl.start_time, sl.end_time, sl.duration, c.name, sl.work_done, sl.efficiency
        FROM session_log sl
        JOIN categories c ON sl.category_id = c.id
        WHERE sl.user_id = ?
        ORDER BY sl.date DESC, sl.start_time DESC
    ''', (username,)):
        session_log.append({
            "date": row[0],
            "start_time": row[1],
            "end_time": row[2],
            "duration": row[3],
            "category": row[4],
            "work_done": row[5],
            "efficiency": row[6]
        })

  # Load total_times (for the specific user)
    for row in cursor.execute("SELECT category_id, total_seconds FROM total_times WHERE user_id = ?", (username,)):
        category_id = row[0]
        category_name = get_category_name_by_id(category_id)  # Fetch category name
        if category_name:
            total_times[category_name] = row[1]


    conn.close()
    return {"categories": categories, "session_log": session_log, "total_times": total_times}
def get_category_name_by_id(category_id):
    conn = sqlite3.connect('time_tracker.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def add_category_to_db(category_name):
    if category_name:
        conn = sqlite3.connect('time_tracker.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
            conn.commit()
            # Get the newly inserted category's ID
            category_id = cursor.lastrowid

            #Initialize the total time spent to zero for all users
            for username in st.secrets["credentials"]["usernames"]:
                cursor.execute("INSERT INTO total_times (category_id, total_seconds, user_id) VALUES(?,?,?)", (category_id,0, username))
                conn.commit()
            st.success(f"Category '{category_name}' added!")

        except sqlite3.IntegrityError:
            st.error(f"Category '{category_name}' already exists.")
        finally:
            conn.close()
def log_session_to_db(session_data):
    conn = sqlite3.connect('time_tracker.db')
    cursor = conn.cursor()
    try:
        # Get category ID
        cursor.execute("SELECT id FROM categories WHERE name = ?", (session_data['category'],))
        category_id = cursor.fetchone()[0]

        cursor.execute('''
            INSERT INTO session_log (date, start_time, end_time, duration, category_id, work_done, efficiency, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session_data['date'], session_data['start_time'], session_data['end_time'], session_data['duration'],
              category_id, session_data['work_done'], session_data['efficiency'], session_data['user_id']))

        # Update total time
        cursor.execute('''
            UPDATE total_times
            SET total_seconds = total_seconds + ?
            WHERE category_id = ? AND user_id = ?
        ''', (session_data['duration_seconds'], category_id, session_data['user_id']))
        conn.commit()
        st.success("Session logged!")
    except Exception as e:
        st.error(f"Error logging session: {e}")
    finally:
        conn.close()


# --- Authentication Setup ---

# Load credentials from Streamlit Secrets
credentials = st.secrets["credentials"]
cookie_config = st.secrets["cookie"]

authenticator = stauth.Authenticate(
    credentials,
    cookie_config["name"],
    cookie_config["key"],
    cookie_config["expiry_days"],
)

# --- Login Form ---
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")

if authentication_status:
    # --- Initialization (using st.session_state) ---
    data = load_data(username) # Load data for the logged-in user

    if 'categories' not in st.session_state:
        st.session_state.categories = data["categories"]
    if 'session_log' not in st.session_state:
        st.session_state.session_log = data["session_log"]
    if 'current_category' not in st.session_state:
        st.session_state.current_category = None
    if 'timer_running' not in st.session_state:
        st.session_state.timer_running = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    if 'elapsed_time' not in st.session_state:
        st.session_state.elapsed_time = 0
    if 'session_length' not in st.session_state:
        st.session_state.session_length = 50
    if 'total_times' not in st.session_state:
        st.session_state.total_times = data["total_times"]  # {category: total_seconds}
    if "work_done" not in st.session_state:
        st.session_state.work_done = ""
    if "efficiency" not in st.session_state:
        st.session_state.efficiency = 0

    # --- Helper Functions ---

    def add_category(category_name):
        if category_name and category_name not in st.session_state.categories:
            add_category_to_db(category_name)
            st.session_state.categories = load_data(username)["categories"]
            st.session_state.total_times = load_data(username)["total_times"]

    def format_time(seconds):
        units = seconds // (100 * 3600)
        seconds %= (100*3600)
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return f"{int(units):02d} : {int(hours):02d} : {int(minutes):02d} : {int(seconds):02d}"

    def calculate_elapsed_time():
        if st.session_state.start_time:
            return time.time() - st.session_state.start_time
        return 0

    def start_timer():
        if not st.session_state.timer_running:
            st.session_state.timer_running = True
            if st.session_state.elapsed_time == 0 :
                st.session_state.start_time = time.time()
            else:
                st.session_state.start_time = time.time() - st.session_state.elapsed_time

    def pause_timer():
        if st.session_state.timer_running:
            st.session_state.timer_running = False
            st.session_state.elapsed_time = calculate_elapsed_time()

    def reset_timer():
        st.session_state.timer_running = False
        st.session_state.elapsed_time = 0
        st.session_state.start_time = None
        st.session_state.work_done = ""
        st.session_state.efficiency= 0

    def log_session():
        if st.session_state.current_category:
            end_time = datetime.datetime.now()
            duration = st.session_state.elapsed_time
            session_data = {
                "date": end_time.strftime("%Y-%m-%d"),
                "start_time": (end_time - datetime.timedelta(seconds=duration)).strftime("%H:%M:%S"),
                "end_time": end_time.strftime("%H:%M:%S"),
                "duration": format_time(duration),
                "duration_seconds": int(duration),
                "category": st.session_state.current_category,
                "work_done": st.session_state.work_done,
                "efficiency": st.session_state.efficiency,
                "user_id": username, # Use the logged in user's name
            }
            log_session_to_db(session_data)
            st.session_state.session_log = load_data(username)["session_log"]  # Refresh log
            st.session_state.total_times = load_data(username)["total_times"]
            reset_timer()

    # --- Sidebar --- (moved inside the authentication check)
    with st.sidebar:
        authenticator.logout("Logout", "sidebar") #Logout moved to sidebar
        st.title("Category Management")
        new_category = st.text_input("Add New Category")
        if st.button("Add"):
            add_category(new_category)

        st.session_state.current_category = st.selectbox("Select Category", st.session_state.categories)
        st.session_state.session_length = st.slider("Session Length (minutes)", min_value=5, max_value=50, step=5, value = st.session_state.session_length)
    # --- Main Area --- (moved inside the authentication check)

    st.title(f"Time Management App - Welcome {name}")

    if st.session_state.current_category:
        # Timer Display
        if st.session_state.timer_running:
            st.session_state.elapsed_time = calculate_elapsed_time()

        total_seconds = st.session_state.total_times.get(st.session_state.current_category, 0) + st.session_state.elapsed_time
        formatted_total_time = format_time(total_seconds)

        st.metric("Elapsed Time", format_time(st.session_state.elapsed_time) )
        st.caption(f"Total time:  {formatted_total_time}")

        # Timer Controls
        col1, col2 = st.columns(2)
        if col1.button("Start/Pause"):
            if st.session_state.timer_running:
                pause_timer()
            else:
                start_timer()

        if col2.button("Reset"):
            log_session() #log on reset

        # Session Details Input (show only when timer is not running)
        if  not st.session_state.timer_running:
            with st.form("session_form"):
                st.session_state.work_done = st.text_area("Work Done", value=st.session_state.work_done)
                st.session_state.efficiency = st.number_input("Efficiency (0-100)", min_value=0, max_value=100, value=st.session_state.efficiency)
                submitted = st.form_submit_button("Log Session")
                if submitted:
                    if st.session_state.elapsed_time>= st.session_state.session_length*60:
                        log_session()
                        st.success("Session logged!")
                    else:
                        st.warning(f"Complete the session time, {format_time(st.session_state.session_length*60-st.session_state.elapsed_time)} left")

        # Session Log Display and Visualization (Combined)
        st.write("Session Log")

        if st.session_state.session_log:
            df = pd.DataFrame(st.session_state.session_log)
            # Convert duration to seconds for plotting
            df['duration_seconds'] = df['duration'].apply(lambda x: sum(int(t) * s for t, s in zip(x.split(' : '), [360000, 3600, 60, 1])))
            df['date_time'] = pd.to_datetime(df['date'] + ' ' + df['start_time'])
            fig = px.bar(df, x='date_time', y='duration_seconds',
                        title='Session Durations Over Time', labels={'date_time': 'Date and Time', 'duration_seconds':'Duration (seconds)'},
                        hover_data=['work_done', 'efficiency', 'category'])  # Add hover data
            st.plotly_chart(fig)
            st.dataframe(df[['date', 'start_time', 'end_time', 'duration', 'work_done', 'efficiency']])  # Display relevant columns


        else:
            st.write("No sessions logged yet for this category.")

        # ---place holder for updating values on the screen---
        if st.session_state.timer_running :
            time.sleep(1)
            st.rerun()
    else:
        st.write("Select a category to start tracking time.")
