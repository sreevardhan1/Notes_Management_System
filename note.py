"""
============================================================
FLASH NOTES - Flask Notes Management System
------------------------------------------------------------
A full-stack web application for creating, viewing, updating,
deleting, and recording notes using Flask + MySQL.
Includes authentication, email reset, dark mode, and attachments.
------------------------------------------------------------
Tech Stack:
  Backend : Python (Flask)
  Frontend: HTML, CSS, JS, Bootstrap
  Database: MySQL
Author: Sreevardhan
============================================================
"""

# ---------- Imports ----------
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import mysql.connector
from mysql.connector import Error
from flask_mail import Mail, Message
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from datetime import timedelta
import os
from captcha_utils import generate_captcha_image, generate_captcha_text
# from otp_utils import generate_otp, save_otp, verify_otp, get_stored_otp


# ---------- Configuration ----------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev_secret_please_change")
app.permanent_session_lifetime = timedelta(days=7)

# Mail setup
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER=("Flash Notes", os.getenv("MAIL_USERNAME"))
)
mail = Mail(app)
tokens = URLSafeTimedSerializer(app.secret_key)

# File upload config
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ---------- Database Connection ----------
def get_db_connection():
    """Connect to MySQL and return the connection."""
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", ""),
            database=os.getenv("DB_NAME", "flaskdb")
        )
    except Error as e:
        print(f"❌ Database error: {e}")
        return None


# ---------- Routes ----------

@app.route('/')
def home():
    """Redirect user to dashboard or login page."""
    return redirect(url_for('view_all') if 'user_id' in session else url_for('login'))


# ========== AUTH ==========
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        mobile = request.form.get('mobile','').strip()

        if not all([email, username, password, mobile]):
            flash("Please fill all the fields", "warning")
            return redirect(url_for('register'))

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM noteusers WHERE email=%s OR username=%s OR mobile = %s", (email, username,mobile))
        if cursor.fetchone():
            flash("User already exists", "danger")
            cursor.close(); db.close()
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        cursor.execute("INSERT INTO noteusers (email, username, password,mobile) VALUES (%s, %s, %s,%s)",
                       (email, username, hashed_pw,mobile))
        db.commit()
        cursor.close(); db.close()
        flash("✅ Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


# ========== CAPTCHA ==========
@app.route('/captcha')
def captcha():
    text = generate_captcha_text()
    session['captcha_text'] = text
    img_buf = generate_captcha_image(text)
    return send_file(img_buf, mimetype='image/png')

'''
# ========== SEND & VALIDATE CAPTCHA ==========
@app.route('/send_otp',methods=['POST'])
def send_otp():
    """
    Expected POST form fields:
      - mobile : phone number string (must match registered user)
      - captcha : user-entered captcha text
    """

    mobile = request.form.get('mobile',"").strip()
    user_captcha = request.form.get('captcha','').strip()

    if not mobile:
        flash("Please Enter your mobile number", 'warning')
        return redirect(url_for('login'))
    
    # verify the captcha
    real = session.get('captcha_text', '')
    if not real or user_captcha.upper() != real.upper():
        flash("Incorrect CAPTCHA. Try again.", "danger")
        return redirect(url_for('login'))

    # verifying user mobile number
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM noteusers WHERE mobile = %s", (mobile,))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    if not user:
        flash("Mobile Number not Registered", "danger")
        return redirect(url_for('login'))
    
    # Generate and Save the OTP
    otp = generate_otp()
    save_otp(mobile, otp, validity_seconds=300)

    session['otp_mobile'] = mobile

    # send OTP via email if mail is configured (otherwise show flash for dev)
    try:
        if app.config.get('MAIL_USERNAME'):
            # send to registered email (for dev convenience)
            msg = Message("Your Flash Notes OTP", recipients=[user['email']])
            msg.body = f"Your OTP is: {otp} (valid 5 minutes)."
            mail.send(msg)
            flash("OTP sent to your registered email address.", "info")
        else:
            # dev fallback: show OTP in flash (not for production)
            flash(f"[DEV OTP] {otp}", "info")
    except Exception as e:
        flash(f"Failed to send OTP: {e}", "danger")
        # still allow dev flow but it's safer to abort; choose to show dev OTP
        flash(f"[DEV OTP] {otp}", "info")

    # redirect to login page where user can enter OTP and verify
    return redirect(url_for('login'))


# OTP Verification Route
@app.route('/verify_otp', methods=['POST'])
def verify_otp_route():
    mobile = request.form.get('mobile','').strip()
    user_otp = request.form.get('otp','').strip()

    if not mobile or not user_otp:
        flash("Please provide mobile and OTP", "warning")
        return redirect(url_for('login'))

    if not verify_otp(mobile, user_otp):   # using verify_otp() from your OTP module
        flash("Invalid or expired OTP.", "danger")
        return redirect(url_for('login'))

    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM noteusers WHERE mobile = %s", (mobile,))
    user = cursor.fetchone()
    cursor.close(); db.close()

    if not user:
        flash("User not found. Please register.", "danger")
        return redirect(url_for('register'))

    session['user_id'] = user['id']
    session['username'] = user['username']
    
    flash("Logged in Successfully", "success")
    return redirect(url_for('view_all'))
'''       

# ========== LOGIN & LOGOUT ==========
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Authenticate user and start session."""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        user_captcha = request.form.get('captcha','').strip()

        # Validate CAPTCHA
        real_captcha = session.get('captcha_text','')
        if not real_captcha or user_captcha.lower() != real_captcha.lower():
            flash("Incorrect CAPTCHA. Try again.", "danger")
            return redirect(url_for('login'))
        
        # Checking DB for the user
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM noteusers WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.close(); db.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f"Welcome {user['username']}!", "success")
            return redirect(url_for('view_all'))
        
        flash("Invalid credentials", "danger")
        
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logs out user."""
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))


# ========== PASSWORD RESET ==========
@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    """Send password reset link."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            flash("Please enter your email", "warning")
            return redirect(url_for('forgot'))

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM noteusers WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close(); db.close()

        if not user:
            flash("Email not registered", "danger")
            return redirect(url_for('forgot'))

        token = tokens.dumps(email, salt='reset-password')
        reset_link = url_for('reset_password', token=token, _external=True)

        msg = Message("Password Reset - Flash Notes", recipients=[email])
        msg.body = f"Hello {user['username']},\n\nClick below to reset your password:\n{reset_link}\n\nLink valid for 5 minutes.\n\n- Flash Notes Team"

        try:
            mail.send(msg)
            flash("Reset link sent to your email.", "info")
        except Exception as e:
            flash(f"Failed to send email: {e}", "danger")
        return redirect(url_for('login'))
    return render_template('forgot.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password using emailed token."""
    try:
        email = tokens.loads(token, salt='reset-password', max_age=300)
    except SignatureExpired:
        flash("Reset link expired. Please try again.", "danger")
        return redirect(url_for('forgot'))

    if request.method == 'POST':
        pw = request.form['password'].strip()
        conf = request.form['confpass'].strip()
        if pw != conf:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('reset_password', token=token))

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE noteusers SET password=%s WHERE email=%s",
                       (generate_password_hash(pw), email))
        db.commit()
        cursor.close(); db.close()
        flash("Password reset successfully.", "success")
        return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)


# ========== NOTES ==========
@app.route('/add_note', methods=['GET', 'POST'])
def add_note():
    """Add new note with optional file attachments."""
    if 'user_id' not in session:
        flash("Please login to add notes", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        user_id = session['user_id']

        if not title:
            flash("Title is required", "warning")
            return redirect(url_for('add_note'))

        uploaded_files = request.files.getlist('attachments')
        saved_files = []
        for file in uploaded_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                saved_files.append(filename)

        attachments_str = ','.join(saved_files) if saved_files else None

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO notes (title, content, user_id, attachments, create_at) VALUES (%s, %s, %s, %s, NOW())",
                       (title, content, user_id, attachments_str))
        db.commit()
        cursor.close(); db.close()
        flash("Note added successfully!", "success")
        return redirect(url_for('view_all'))

    return render_template('addnote.html')


@app.route('/view_all')
def view_all():
    """View all notes belonging to the logged-in user."""
    if 'user_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM notes WHERE user_id=%s ORDER BY create_at DESC", (session['user_id'],))
    notes = cursor.fetchall()
    cursor.close(); db.close()
    return render_template('viewnote.html', notes=notes)


@app.route('/note/<int:note_id>')
def single_note(note_id):
    """View a single note."""
    if 'user_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM notes WHERE id=%s AND user_id=%s", (note_id, session['user_id']))
    note = cursor.fetchone()
    cursor.close(); db.close()

    if not note:
        flash("Note not found.", "danger")
        return redirect(url_for('view_all'))
    return render_template('singlenote.html', note=note)


@app.route('/edit_note/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    """Edit an existing note and manage attachments."""
    if 'user_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM notes WHERE id=%s AND user_id=%s", (note_id, session['user_id']))
    note = cursor.fetchone()

    if not note:
        flash("Unauthorized or invalid note.", "danger")
        cursor.close(); db.close()
        return redirect(url_for('view_all'))

    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()

        # ✅ Step 1: Update title and content
        cursor.execute(
            "UPDATE notes SET title=%s, content=%s WHERE id=%s AND user_id=%s",
            (title, content, note_id, session['user_id'])
        )

        # ✅ Step 2: Handle file deletions (safe and clean)
        files_to_delete = request.form.getlist('delete_files')

        # Existing attachments (split safely even if None)
        existing_files = note['attachments'].split(',') if note.get('attachments') else []

        # Delete the selected files from storage
        if files_to_delete:
            for filename in files_to_delete:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
            # Remove deleted files from attachment list
            remaining_files = [f for f in existing_files if f not in files_to_delete]
        else:
            # If no files marked for deletion, keep all
            remaining_files = existing_files

        # Update database with new attachments list
        new_attachments = ','.join(remaining_files)
        cursor.execute("UPDATE notes SET attachments = %s WHERE id=%s", (new_attachments, note_id))
        note['attachments'] = new_attachments  # Update local variable


        # ✅ Step 3: Handle new uploads
        uploaded_files = request.files.getlist('attachments')
        saved_files = []
        for file in uploaded_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                saved_files.append(filename)

        if saved_files:
            if note['attachments']:
                updated_list = note['attachments'].split(',') + saved_files
            else:
                updated_list = saved_files

            cursor.execute("UPDATE notes SET attachments = %s WHERE id=%s", (','.join(updated_list), note_id))

        db.commit()
        cursor.close(); db.close()

        flash("✅ Note updated successfully", "success")
        return redirect(url_for('view_all'))

    cursor.close(); db.close()
    return render_template('updatenote.html', note=note)



@app.route('/delete_note/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    """Delete note and its attachments."""
    if 'user_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT attachments FROM notes WHERE id=%s AND user_id=%s",
                   (note_id, session['user_id']))
    note = cursor.fetchone()

    if note and note.get('attachments'):
        for filename in note['attachments'].split(','):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                os.remove(filepath)

    cursor.execute("DELETE FROM notes WHERE id=%s AND user_id=%s", (note_id, session['user_id']))
    db.commit()
    cursor.close(); db.close()
    flash("🗑️ Note deleted successfully", "success")
    return redirect(url_for('view_all'))


# ========== SEARCH ==========
@app.route('/search')
def search_notes():
    """Search notes by title or content."""
    if 'user_id' not in session:
        flash("Please login to search notes", "warning")
        return redirect(url_for('login'))

    keyword = request.args.get('q', '').strip()
    if not keyword:
        return redirect(url_for('view_all'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    like = f"%{keyword}%"
    cursor.execute("""
        SELECT * FROM notes
        WHERE user_id=%s AND (title LIKE %s OR content LIKE %s)
        ORDER BY create_at DESC
    """, (session['user_id'], like, like))
    notes = cursor.fetchall()
    cursor.close(); db.close()

    if not notes:
        flash(f"No results found for '{keyword}'", "info")

    return render_template('viewnote.html', notes=notes, search_term=keyword)


# ========== STATIC PAGES ==========
@app.route('/about')
def about():
    """About page."""
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form."""
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        message = request.form['message'].strip()
        if not all([name, email, message]):
            flash("Please fill all fields", "warning")
            return redirect(url_for('contact'))

        msg = Message(f"Contact from {name}", recipients=[app.config['MAIL_USERNAME']])
        msg.body = f"From: {name} <{email}>\n\n{message}"
        try:
            mail.send(msg)
            flash("Message sent successfully!", "success")
        except Exception as e:
            flash(f"Failed to send message: {e}", "danger")

    return render_template('contact.html')


# ========== ERROR HANDLER ==========
@app.errorhandler(404)
def not_found(e):
    """Custom 404 page."""
    return render_template('404.html'), 404


# ========== MAIN ==========
if __name__ == '__main__':
    app.run(debug=True)
