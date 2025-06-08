# College Academic Management System

A web-based academic management system built with Django and Tailwind CSS.

## Features
- User authentication (Teachers and Students)
- Admin panel for user management
- Teacher features:
  - View all students
  - Set subject results
  - Make announcements
- Student features:
  - View personal results
  - View announcements

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Unix/MacOS:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

7. Access the application at http://localhost:8000