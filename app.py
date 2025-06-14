from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'careerbuddysecret'

# 🔗 MySQL connection
def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",       # ← change this
        password="Nvsd1997@",   # ← change this
        database="career_buddy"
    )

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                           (username, password, email))
            conn.commit()
        except mysql.connector.IntegrityError:
            return "Username already exists!"
        conn.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/user_home')
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/user_home', methods=['GET', 'POST'])
def user_home():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT class_completed, marks, budget, interest, recommendation, timestamp
        FROM recommendations
        WHERE user_id = %s ORDER BY timestamp DESC
    """, (session['user_id'],))
    recommendations = cursor.fetchall()
    conn.close()
    return render_template('user_home.html', recommendations=recommendations)

@app.route('/recommend', methods=['POST'])
def recommend():
    if 'user_id' not in session:
        return redirect('/login')

    class_completed = request.form['class']
    marks = int(request.form['marks'])
    budget = int(request.form['budget'])
    interest = request.form['interest']

    icon = {
        'technology': '🖥️',
        'business': '📊',
        'law': '⚖️',
        'medical': '🩺',
        'design': '🎨'
    }.get(interest, '')

    recommendation = "Based on your input, here are some career suggestions: "

    if class_completed == '10':
        if interest == 'technology':
            recommendation += "Diploma in Engineering or ITI courses."
        elif interest == 'business':
            recommendation += "Diploma in Business Administration."
        elif interest == 'law':
            recommendation += "Choose +2 with Arts and explore legal studies later."
        elif interest == 'medical':
            recommendation += "Take Science with Biology and prepare for NEET."
        elif interest == 'design':
            recommendation += "Diploma in Graphic/Fashion Design."
    elif class_completed == '12':
        if interest == 'technology':
            if marks >= 75 and budget >= 100000:
                recommendation += "B.Tech in Computer Science."
            else:
                recommendation += "BCA or B.Sc IT."
        elif interest == 'business':
            recommendation += "BBA, B.Com or CA Foundation."
        elif interest == 'law':
            recommendation += "BA-LLB or CLAT coaching."
        elif interest == 'medical':
            recommendation += "MBBS if NEET qualified, else B.Sc Nursing or Paramedical."
        elif interest == 'design':
            recommendation += "B.Des or B.Sc in Design."

    full_reco = f"{icon} {recommendation}"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO recommendations (user_id, class_completed, marks, budget, interest, recommendation, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (session['user_id'], class_completed, marks, budget, interest, full_reco, datetime.now()))
    conn.commit()
    conn.close()

    return render_template('result.html', recommendation=full_reco)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin123':
            session['admin'] = True
            return redirect('/admin_dashboard')
        else:
            return "Invalid admin credentials"
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect('/admin_login')
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.username, r.class_completed, r.marks, r.budget, r.interest, r.recommendation, r.timestamp
        FROM recommendations r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.timestamp DESC
    ''')
    records = cursor.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', records=records)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
