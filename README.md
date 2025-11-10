# 📝 Flash Notes - Note Management System

A full-stack web application built with Flask and MySQL for creating, managing, and recording notes with audio support.

## ✨ Features
- 🔐 User authentication with password reset
- 📝 Create, edit, delete notes
- 🎙️ Record audio notes
- 📎 File attachments (images, PDFs, videos)
- 🔍 Search functionality
- 🌓 Dark/Light theme
- 📱 Responsive design
- 🏷️ Note categories

## 🚀 Installation

1. Clone repository
```bash
git clone https://github.com/yourusername/flash-notes.git
cd flash-notes
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Setup database
```sql
CREATE DATABASE flaskdb;
USE flaskdb;
-- Run schema.sql
```

4. Configure environment
Create `.env` file:
```
DB_HOST=localhost
DB_USER=root
DB_PASS=yourpassword
DB_NAME=flaskdb
FLASK_SECRET=your-secret-key
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

5. Run application
```bash
python note.py
```

## 📦 Tech Stack
- Backend: Python, Flask
- Database: MySQL
- Frontend: HTML, CSS, Bootstrap, JavaScript
- Authentication: Werkzeug, itsdangerous
- Email: Flask-Mail

## 📄 License
MIT License

## 👤 Author
Sreevardhan
