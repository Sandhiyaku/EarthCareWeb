from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from urllib.parse import quote

app = Flask(__name__)
app.secret_key = 'earthcare_secret_key'

# --- Database Connection ---
def get_db_connection():
    conn = sqlite3.connect('earthcare.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Jinja Filter for Google Maps URLs ---
@app.template_filter('urlencode')
def urlencode_filter(s):
    if s:
        return quote(s)
    return ""

# --- LOGIN / INDEX ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            # ROLE-BASED REDIRECTION
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'worker':
                return redirect(url_for('worker_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
            
    return render_template('login.html')

# --- REGISTRATION ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        phone = request.form['phone']
        address = request.form['address']
        role = request.form.get('role', 'user') # Grabs 'worker' or 'user'
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, role, phone, address) VALUES (?, ?, ?, ?, ?)',
                         (username, password, role, phone, address))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('Username already exists!', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

# --- USER DASHBOARD (Booking) ---
@app.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if session.get('role') != 'user': return redirect(url_for('index'))
    
    conn = get_db_connection()
    if request.method == 'POST':
        waste_type = request.form['waste_type']
        date = request.form['date']
        time = request.form['time']
        # Grabbing the address from the form
        form_address = request.form.get('address')
        
        user_id = session['user_id']
        
        # Optional: Update the user's default address in the users table if they changed it
        if form_address:
            conn.execute('UPDATE users SET address = ? WHERE id = ?', (form_address, user_id))

        conn.execute('INSERT INTO bookings (user_id, waste_type, booking_date, time_slot, status) VALUES (?, ?, ?, ?, ?)',
                     (user_id, waste_type, date, time, 'Pending'))
        conn.commit()
        flash('Pickup Scheduled Successfully!', 'success')

    bookings = conn.execute('SELECT * FROM bookings WHERE user_id = ? ORDER BY id DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('user_dashboard.html', bookings=bookings)

# --- ADMIN DASHBOARD (Assigning) ---
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    
    conn = get_db_connection()
    # Join bookings with users to get addresses and names
    bookings = conn.execute('''
        SELECT b.*, u.username as customer_name, u.address 
        FROM bookings b JOIN users u ON b.user_id = u.id 
        WHERE b.status != 'Completed'
    ''').fetchall()
    
    workers = conn.execute('SELECT id, username FROM users WHERE role = "worker"').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', bookings=bookings, workers=workers)

@app.route('/assign_worker', methods=['POST'])
def assign_worker():
    booking_id = request.form.get('booking_id')
    worker_id = request.form.get('worker_id')
    
    conn = get_db_connection()
    conn.execute('UPDATE bookings SET worker_id = ?, status = ? WHERE id = ?',
                 (worker_id, 'Assigned', booking_id))
    conn.commit()
    conn.close()
    flash('Worker Assigned Successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# --- WORKER DASHBOARD (Field View) ---
@app.route('/worker_dashboard')
def worker_dashboard():
    if session.get('role') != 'worker': return redirect(url_for('index'))
    
    conn = get_db_connection()
    # Get tasks assigned to THIS worker
    tasks = conn.execute('''
        SELECT b.*, u.username as customer_name, u.address, u.phone as customer_phone
        FROM bookings b JOIN users u ON b.user_id = u.id
        WHERE b.worker_id = ? AND b.status = 'Assigned'
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('worker_dashboard.html', tasks=tasks)

@app.route('/complete_task/<int:booking_id>', methods=['POST'])
def complete_task(booking_id):
    conn = get_db_connection()
    conn.execute('UPDATE bookings SET status = "Completed" WHERE id = ?', (booking_id,))
    conn.commit()
    conn.close()
    flash('Task marked as Completed!', 'success')
    return redirect(url_for('worker_dashboard'))

# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)