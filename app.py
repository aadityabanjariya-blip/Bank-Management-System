import sqlite3
from datetime import datetime
import streamlit as st

# --- DATABASE SETUP ---
DB_FILE = "bank_system.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create Accounts Table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            acc_no TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            pin TEXT NOT NULL,
            balance REAL NOT NULL
        )
    """
    )

    # Create Transactions Table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            acc_no TEXT NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            balance_after REAL NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (acc_no) REFERENCES accounts (acc_no)
        )
    """
    )

    conn.commit()
    conn.close()


# --- DATABASE FUNCTIONS ---
def create_account(acc_no, name, pin, initial_deposit):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO accounts (acc_no, name, pin, balance) VALUES (?, ?, ?, ?)",
            (acc_no, name, pin, initial_deposit),
        )

        # Log initial deposit as a transaction if > 0
        if initial_deposit > 0:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                INSERT INTO transactions (acc_no, type, amount, balance_after, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """,
                (acc_no, "Initial Deposit", initial_deposit, initial_deposit, timestamp),
            )

        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Account number already exists. Please choose a different one."
    finally:
        conn.close()


def authenticate_user(acc_no, pin):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT acc_no, name, balance FROM accounts WHERE acc_no = ? AND pin = ?",
        (acc_no, pin),
    )
    user = cursor.fetchone()
    conn.close()
    return user


def get_account_info(acc_no):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT acc_no, name, balance FROM accounts WHERE acc_no = ?", (acc_no,)
    )
    user = cursor.fetchone()
    conn.close()
    return user


def deposit_money(acc_no, amount):
    if amount <= 0:
        return False, "Deposit amount must be greater than zero."

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM accounts WHERE acc_no = ?", (acc_no,))
    current_balance = cursor.fetchone()[0]

    new_balance = current_balance + amount
    cursor.execute(
        "UPDATE accounts SET balance = ? WHERE acc_no = ?", (new_balance, acc_no)
    )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        INSERT INTO transactions (acc_no, type, amount, balance_after, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """,
        (acc_no, "Deposit", amount, new_balance, timestamp),
    )

    conn.commit()
    conn.close()
    return True, f"Successfully deposited ₹{amount:.2f}. New Balance: ₹{new_balance:.2f}"


def withdraw_money(acc_no, amount):
    if amount <= 0:
        return False, "Withdrawal amount must be greater than zero."

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM accounts WHERE acc_no = ?", (acc_no,))
    current_balance = cursor.fetchone()[0]

    if amount > current_balance:
        conn.close()
        return False, "Insufficient balance!"

    new_balance = current_balance - amount
    cursor.execute(
        "UPDATE accounts SET balance = ? WHERE acc_no = ?", (new_balance, acc_no)
    )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        INSERT INTO transactions (acc_no, type, amount, balance_after, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """,
        (acc_no, "Withdrawal", amount, new_balance, timestamp),
    )

    conn.commit()
    conn.close()
    return True, f"Successfully withdrew ₹{amount:.2f}. New Balance: ₹{new_balance:.2f}"


def get_transaction_history(acc_no):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT type, amount, balance_after, timestamp
        FROM transactions
        WHERE acc_no = ?
        ORDER BY id DESC
    """,
        (acc_no,),
    )
    history = cursor.fetchall()
    conn.close()
    return history


# --- STREAMLIT UI ---
def main():
    st.set_page_config(page_title="Bank Management System", page_icon="🏦", layout="centered")
    init_db()

    st.title("🏦 Bank Management System")

    # Session State Initialization
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "acc_no" not in st.session_state:
        st.session_state.acc_no = None

    # Sidebar Navigation
    menu = ["Login", "Create Account"]
    if st.session_state.logged_in:
        menu = ["Dashboard", "Deposit", "Withdraw", "Transaction History", "Logout"]

    choice = st.sidebar.selectbox("Navigation", menu)

    # --- CREATE ACCOUNT ---
    if choice == "Create Account":
        st.subheader("📝 Create New Account")
        with st.form("create_account_form", clear_on_submit=True):
            acc_no = st.text_input("Email ID")
            name = st.text_input("Full Name")
            pin = st.text_input("Set 4-Digit PIN", type="password", max_chars=4)
            initial_deposit = st.number_input(
                "Initial Deposit (₹)", min_value=0.0, step=10.0, format="%.2f"
            )
            submit = st.form_submit_button("Register")

            if submit:
                if not acc_no or not name or not pin:
                    st.error("Please fill in all fields.")
                elif len(pin) != 4 or not pin.isdigit():
                    st.error("PIN must be a 4-digit number.")
                else:
                    success, message = create_account(acc_no, name, pin, initial_deposit)
                    if success:
                        st.success(f"{message} Your account number is: **{acc_no}**")
                        st.success(f"{message} Your pin is: **{pin}**" )
                    else:
                        st.error(message)

    # --- LOGIN ---
    elif choice == "Login":
        st.subheader("🔑 Account Login")
        with st.form("login_form"):
            acc_no = st.text_input("Account Number")
            pin = st.text_input("PIN", type="password", max_chars=4)
            submit = st.form_submit_button("Login")

            if submit:
                user = authenticate_user(acc_no, pin)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.acc_no = user[0]
                    st.success(f"Welcome back, {user[1]}!")
                    st.rerun()
                else:
                    st.error("Invalid Account Number or PIN.")

    # --- DASHBOARD (LOGGED IN) ---
    elif choice == "Dashboard":
        user = get_account_info(st.session_state.acc_no)
        st.subheader("📊 Account Overview")
        st.info(f"**Account Holder:** {user[1]}")
        st.info(f"**Account Number:** {user[0]}")
        st.metric(label="Current Balance", value=f"₹{user[2]:,.2f}")

    # --- DEPOSIT ---
    elif choice == "Deposit":
        st.subheader("💵 Deposit Funds")
        user = get_account_info(st.session_state.acc_no)
        st.write(f"Current Balance: **₹{user[2]:,.2f}**")

        amount = st.number_input(
            "Enter amount to deposit (₹)", min_value=1.0, step=10.0, format="%.2f"
        )
        if st.button("Deposit"):
            success, message = deposit_money(st.session_state.acc_no, amount)
            if success:
                st.success(message)
            else:
                st.error(message)

    # --- WITHDRAW ---
    elif choice == "Withdraw":
        st.subheader("💸 Withdraw Funds")
        user = get_account_info(st.session_state.acc_no)
        st.write(f"Current Balance: **₹{user[2]:,.2f}**")

        amount = st.number_input(
            "Enter amount to withdraw (₹)", min_value=1.0, step=10.0, format="%.2f"
        )
        if st.button("Withdraw"):
            success, message = withdraw_money(st.session_state.acc_no, amount)
            if success:
                st.success(message)
            else:
                st.error(message)

    # --- TRANSACTION HISTORY ---
    elif choice == "Transaction History":
        st.subheader("📜 Transaction Statement")
        history = get_transaction_history(st.session_state.acc_no)

        if history:
            import pandas as pd

            df = pd.DataFrame(
                history,
                columns=["Type", "Amount (₹)", "Balance After (₹)", "Date & Time"],
            )
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No transaction history found.")

    # --- LOGOUT ---
    elif choice == "Logout":
        st.session_state.logged_in = False
        st.session_state.acc_no = None
        st.success("You have logged out successfully.")
        st.rerun()


if __name__ == "__main__":
    main()