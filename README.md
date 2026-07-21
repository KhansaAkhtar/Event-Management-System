# Event Management System

A full-stack **Flask REST API** application for managing events, bookings, vendors, and payments, with role-based access control and automated report generation.

---

## Overview

This system allows an organization to create and manage events, let users browse and book events (or request fully custom private events), coordinate vendors, track payments, and generate downloadable reports — all secured behind JWT authentication and a four-tier role system.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | Flask |
| Database | SQLite |
| ORM | SQLAlchemy (Flask-SQLAlchemy) |
| Migrations | Flask-Migrate (Alembic) |
| Authentication | Flask-JWT-Extended (JWT) |
| Password Security | Werkzeug (password hashing) |
| Validation | Marshmallow |
| Report Generation | ReportLab (PDF), openpyxl (Excel) |
| Frontend | Bootstrap 5, Bootstrap Icons, vanilla JavaScript (fetch API) |
| Templating | Jinja2 |

---

## User Roles

| Role | Access |
|---|---|
| **Super Admin** | Full system access — manages all events (regardless of creator), all users (view/delete/change role), all bookings/payments, and all reports |
| **Admin** | Manages their own events (create/edit/delete), views/approves bookings and payments for their own events, generates reports for their own events |
| **Vendor** | Registers services and links them to specific events; manages own service listings |
| **User** | Browses public events, books events, makes payments, and can submit a **custom private event request** (with their own capacity/venue/date) for Admin review and pricing |

---

## Core Modules

1. **Authentication** — Registration, login, JWT issuance, password hashing
2. **Event Management** — Full CRUD, public/private event distinction, custom event requests with admin approval workflow
3. **Booking** — Event registration, cancellation, duplicate-booking prevention
4. **Vendor** — Service management linked to events
5. **Payment** — Payment creation, admin approval flow, duplicate-payment prevention
6. **Report Generation** — Revenue, attendance, vendor, and payment reports (PDF/Excel)

---

## Key Features

- Role-based access control enforced at the API level via a custom decorator, independent of frontend behavior
- JWT-based stateless authentication
- Automatic event status updates (events past their date are marked "completed")
- Custom/private event request flow: a user submits event details, an Admin sets the price and approves it, and the event is automatically booked for that user only — it never appears in the public events list
- Duplicate-prevention logic for both bookings and payments
- Downloadable PDF/Excel reports generated in-memory and streamed directly to the client
- Fully synced frontend — no page reloads; all data flows through `fetch()` calls against the REST API

---

## Project Structure

```
event_management/
├── app/
│   ├── models/          # SQLAlchemy models (User, Event, Booking, Vendor, Payment)
│   ├── routes/           # Blueprints: auth, events, bookings, vendors, payments, reports, users, views
│   ├── schemas/          # Marshmallow validation schemas
│   ├── utils/             # Custom role-based access decorator
│   ├── templates/         # Jinja2 HTML pages
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── __init__.py        # App factory
├── migrations/            # Flask-Migrate version history
├── config.py
├── run.py
├── requirements.txt
└── .env                   # Not committed — holds secrets
```

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd event_management
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the project root:
```
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

### 5. Set up the database
```bash
flask db upgrade
```

### 6. Run the application
```bash
flask run
```
Visit `http://127.0.0.1:5000/` — the login page is the entry point for the whole system.

### 7. Create a Super Admin (manual, one-time)
Registration is limited to `user` and `vendor` roles for security. To create the first Super Admin:
```bash
python
>>> from werkzeug.security import generate_password_hash
>>> print(generate_password_hash("your-password"))
```
Then insert a row into the `user` table (e.g. via DB Browser for SQLite) with `role = 'super_admin'` and the generated hash as `password_hash`. Once created, the Super Admin can promote/demote other users' roles directly from the Admin Dashboard.

---

## API Endpoints

### Auth
```
POST   /auth/register
POST   /auth/login
```

### Events
```
GET    /events
GET    /events/<id>
POST   /events                       (admin, super_admin)
PUT    /events/<id>                  (admin: own only, super_admin: any)
DELETE /events/<id>                  (admin: own only, super_admin: any)
POST   /events/request                (user — custom private event request)
GET    /events/pending                (admin, super_admin)
PUT    /events/<id>/approve           (admin, super_admin — sets price, publishes, auto-books requester)
PUT    /events/<id>/reject            (admin, super_admin)
```

### Bookings
```
POST   /bookings
GET    /bookings/my
GET    /bookings/event/<event_id>     (admin, super_admin)
PUT    /bookings/<id>/cancel
```

### Vendors
```
POST   /vendors                       (vendor)
GET    /vendors/my                    (vendor)
GET    /vendors/event/<event_id>
DELETE /vendors/<id>                  (vendor: own only)
```

### Payments
```
POST   /payments
GET    /payments/my
GET    /payments/event/<event_id>     (admin, super_admin)
PUT    /payments/<id>                 (admin, super_admin)
```

### Reports
```
GET    /reports/revenue/<event_id>     (admin, super_admin)
GET    /reports/attendance/<event_id>  (admin, super_admin)
GET    /reports/vendors/<event_id>     (admin, super_admin)
GET    /reports/payments/<event_id>    (admin, super_admin)
```

### User Management
```
GET    /users                         (super_admin)
PUT    /users/<id>/role                (super_admin)
DELETE /users/<id>                     (super_admin)
```

---

## Security Notes

- Passwords are never stored in plain text (Werkzeug hashing)
- `.env` holds all secrets and is excluded from version control via `.gitignore`
- Every protected route is enforced server-side via JWT verification and role decorators — frontend role checks exist only for UX (hiding irrelevant navigation), not as a security boundary
- Admin-level ownership rules ("own vs. any") are enforced at the database-query level, not just in the UI

---

## Future Improvements

- Event capacity enforcement (block bookings once an event is full)
- Refresh tokens and automatic session expiry handling on the frontend
- Vendor payout/settlement tracking
- Rate limiting and HTTPS enforcement for production deployment
