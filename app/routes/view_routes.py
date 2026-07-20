from flask import Blueprint, render_template

view_bp = Blueprint('views', __name__)

@view_bp.route('/')
def home_page():
    return render_template('login.html')

@view_bp.route('/home')
def events_page():
    return render_template('events_list.html')

@view_bp.route('/login')
def login_page():
    return render_template('login.html')

@view_bp.route('/register')
def register_page():
    return render_template('register.html')

@view_bp.route('/my-bookings')
def bookings_page():
    return render_template('my_bookings.html')

@view_bp.route('/admin-dashboard')
def admin_page():
    return render_template('admin_dashboard.html')

@view_bp.route('/vendor-dashboard')
def vendor_page():
    return render_template('vendor_dashboard.html')