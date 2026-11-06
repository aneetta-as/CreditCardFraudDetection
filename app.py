from flask import Flask, render_template, request, redirect, url_for, session, url_for
import joblib
import pandas as pd
import numpy as np
import mysql.connector

app = Flask(__name__)

# Secret key for login sessions
app.secret_key = "credit-card-fraud-detection-secret"


# ==========================================
# MySQL Database Connection
# ==========================================

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root@2005",
    database="credit_card_fraud"
)


# ==========================================
# Load Machine Learning Model
# ==========================================

model = joblib.load("model/fraud_model.pkl")

feature_columns = joblib.load("model/feature_columns.pkl")

print("Random Forest model loaded successfully!")
print("Number of model features:", len(feature_columns))


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# REGISTER
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    cursor = db.cursor()

    # Check if email already exists
    cursor.execute(
        "SELECT user_id FROM users WHERE email = %s",
        (email,)
    )

    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        return "An account with this email already exists."

    # Insert new user
    cursor.execute(
        """
        INSERT INTO users (name, email, password)
        VALUES (%s, %s, %s)
        """,
        (name, email, password)
    )

    db.commit()
    cursor.close()

    return redirect(url_for("login"))


# ==========================================
# LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    email = request.form["email"]
    password = request.form["password"]

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT user_id, name, email
        FROM users
        WHERE email = %s AND password = %s
        """,
        (email, password)
    )

    user = cursor.fetchone()

    cursor.close()

    if user:

        session["user_id"] = user[0]
        session["user_name"] = user[1]
        session["user_email"] = user[2]

        return redirect(url_for("dashboard"))

    return "Invalid email or password."

@app.route("/admin/dashboard")
def admin_dashboard():

    # Check whether an admin is logged in
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    cursor = db.cursor()

    # Total transactions
    cursor.execute(
        "SELECT COUNT(*) FROM transactions"
    )
    total_transactions = cursor.fetchone()[0]

    # Fraud transactions
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE prediction = 'Fraud'
        """
    )
    fraud_transactions = cursor.fetchone()[0]

    # Genuine transactions
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE prediction = 'Genuine'
        """
    )
    genuine_transactions = cursor.fetchone()[0]

    # Recent transactions
    cursor.execute(
        """
        SELECT
            transaction_id,
            amount,
            category,
            state,
            prediction,
            fraud_probability,
            created_at
        FROM transactions
        ORDER BY transaction_id DESC
        LIMIT 20
        """
    )

    transactions = cursor.fetchall()

    cursor.close()

    return render_template(
        "admin_dashboard.html",
        total_transactions=total_transactions,
        fraud_transactions=fraud_transactions,
        genuine_transactions=genuine_transactions,
        transactions=transactions
    )

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "GET":
        return render_template("admin_login.html")

    email = request.form["email"]
    password = request.form["password"]

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT admin_id, name, email
        FROM admins
        WHERE email = %s AND password = %s
        """,
        (email, password)
    )

    admin = cursor.fetchone()
    cursor.close()

    if admin:
        session["admin_id"] = admin[0]
        session["admin_name"] = admin[1]
        session["admin_email"] = admin[2]

        return redirect(url_for("admin_dashboard"))

    return "Invalid admin email or password."

# ==========================================
# USER DASHBOARD
# ==========================================

@app.route("/dashboard")
def dashboard():

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user_name = session["user_name"]

    cursor = db.cursor()

    # Get transactions belonging to this user
    cursor.execute(
        """
        SELECT
            transaction_id,
            amount,
            category,
            prediction,
            fraud_probability,
            created_at
        FROM transactions
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

    transactions = cursor.fetchall()

    # Count total transactions
    total_transactions = len(transactions)

    # Count fraud transactions
    fraud_transactions = sum(
        1
        for transaction in transactions
        if transaction[3] == "Fraud"
    )

    # Count genuine transactions
    genuine_transactions = sum(
        1
        for transaction in transactions
        if transaction[3] == "Genuine"
    )

    cursor.close()

    return render_template(
        "dashboard.html",
        user_name=user_name,
        transactions=transactions,
        total_transactions=total_transactions,
        fraud_transactions=fraud_transactions,
        genuine_transactions=genuine_transactions
    )


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    # Clear login session
    session.clear()

    # Return to login page
    return redirect(url_for("login"))

# ==========================================
# FRAUD ALERTS
# ==========================================

@app.route("/alerts")
def alerts():

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT
            alert_id,
            transaction_id,
            fraud_probability,
            alert_message,
            status,
            created_at
        FROM fraud_alerts
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

    alerts = cursor.fetchall()

    cursor.close()

    return render_template(
        "alerts.html",
        alerts=alerts
    )
# ==========================================
# FRAUD PREDICTION
# ==========================================

@app.route("/predict", methods=["GET", "POST"])
def predict():

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Open prediction form
    if request.method == "GET":
        return render_template("predict.html")

    # ======================================
    # Get values from HTML form
    # ======================================

    amt = float(request.form["amt"])

    category = request.form["category"]

    gender = request.form["gender"]

    state = request.form["state"]

    city_pop = float(request.form["city_pop"])

    lat = float(request.form["lat"])

    long = float(request.form["long"])

    merch_lat = float(request.form["merch_lat"])

    merch_long = float(request.form["merch_long"])

    transaction_hour = int(
        request.form["transaction_hour"]
    )

    transaction_day = int(
        request.form["transaction_day"]
    )

    transaction_month = int(
        request.form["transaction_month"]
    )

    transaction_dayofweek = int(
        request.form["transaction_dayofweek"]
    )

    customer_age = int(
        request.form["customer_age"]
    )


    # ======================================
    # Calculate location distance
    # ======================================

    location_distance = np.sqrt(
        (lat - merch_lat) ** 2 +
        (long - merch_long) ** 2
    )


    # ======================================
    # Create input dataframe
    # ======================================

    input_data = pd.DataFrame([{

        "category": category,

        "amt": amt,

        "gender": gender,

        "state": state,

        "city_pop": city_pop,

        "lat": lat,

        "long": long,

        "merch_lat": merch_lat,

        "merch_long": merch_long,

        "transaction_hour": transaction_hour,

        "transaction_day": transaction_day,

        "transaction_month": transaction_month,

        "transaction_dayofweek": transaction_dayofweek,

        "customer_age": customer_age,

        "location_distance": location_distance

    }])


    # ======================================
    # Convert categorical values
    # ======================================

    input_data = pd.get_dummies(
        input_data,
        columns=[
            "category",
            "gender",
            "state"
        ]
    )


    # Make columns exactly match training
    input_data = input_data.reindex(
        columns=feature_columns,
        fill_value=0
    )


    # ======================================
    # Make ML prediction
    # ======================================

    prediction = model.predict(input_data)[0]

    probability = model.predict_proba(
        input_data
    )[0][1]

    probability_percentage = round(
        probability * 100,
        2
    )


    # ======================================
    # Save transaction to MySQL
    # ======================================

   # ======================================
    # Save transaction to MySQL
    # ======================================

    user_id = session["user_id"]

    cursor = db.cursor()

    sql = """
        INSERT INTO transactions (
            user_id,
            amount,
            category,
            gender,
            state,
            city_population,
            customer_age,
            latitude,
            longitude,
            merchant_latitude,
            merchant_longitude,
            transaction_hour,
            transaction_day,
            transaction_month,
            transaction_dayofweek,
            location_distance,
            prediction,
            fraud_probability
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s,%s
        )
    """

    values = (
        user_id,
        amt,
        category,
        gender,
        state,
        city_pop,
        customer_age,
        lat,
        long,
        merch_lat,
        merch_long,
        transaction_hour,
        transaction_day,
        transaction_month,
        transaction_dayofweek,
        location_distance,
        "Fraud" if prediction == 1 else "Genuine",
        probability_percentage
    )

    cursor.execute(sql, values)

    transaction_id = cursor.lastrowid

    # ======================================
    # Create Fraud Alert
    # ======================================

    if prediction == 1:

        alert_message = (
            "Suspicious transaction detected. "
            "Please review this transaction."
        )

        cursor.execute(
            """
            INSERT INTO fraud_alerts (
                transaction_id,
                user_id,
                alert_message,
                fraud_probability,
                status
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                transaction_id,
                user_id,
                alert_message,
                probability_percentage,
                "Unread"
            )
        )

    db.commit()

    cursor.close()
    # ======================================
    # Prepare result
    # ======================================

    if prediction == 1:

        result = "Fraud"

        result_message = (
            "This transaction has been identified "
            "as potentially fraudulent."
        )

    else:

        result = "Genuine"

        result_message = (
            "This transaction appears to be genuine."
        )


    # ======================================
    # Show result page
    # ======================================

    return render_template(
        "result.html",
        result=result,
        probability=probability_percentage,
        message=result_message
    )


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)