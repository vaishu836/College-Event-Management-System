import logging
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import render_template, redirect, url_for, flash, Blueprint, request, current_app,jsonify
from flask_login import login_user, logout_user, login_required, current_user 
from .forms import RegistrationForm, LoginForm, EventForm, MessageForm
from .models import db, User, Event , new_event ,Message
from functools import wraps
from flask_bcrypt import Bcrypt

main = Blueprint('main', __name__)
bcrypt = Bcrypt()
logging.basicConfig(level=logging.DEBUG)

@main.route('/')
def index():
    return render_template('index.html', user=current_user)

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('An account with this email already exists. Please log in or use a different email.', 'danger')
            return redirect(url_for('main.register'))

        # Hash password and add new user
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password, role=form.role.data)
        
        try:
            logging.debug("Received registration data: %s", form.data)
            db.session.add(new_user)
            db.session.commit()
            logging.info("User registered successfully: %s", new_user.username)
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            logging.error("Error saving user: %s", e)
            flash('An error occurred while creating the account.', 'danger')
    else:
        logging.debug("Form validation failed: %s", form.errors)
    
    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            role_redirects = {
                'admin': 'main.create_event',
                'faculty': 'main.message_admin',
                'student': 'main.view_events'
            }
            logging.debug(f"{user.role.capitalize()} {user.username} logged in.")
            return redirect(url_for(role_redirects.get(user.role, 'main.view_events')))
        else:
            flash('Invalid username or password.', 'danger')
            logging.debug(f"Failed login attempt for {form.username.data}")
    return render_template('login.html', form=form)

def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

@main.route('/message_admin', methods=['GET', 'POST'])
@login_required
@role_required('faculty')
def message_admin():
    form = MessageForm()
    
    if form.validate_on_submit():
        # Create a new message and store in the database
        new_message = Message(
            sender_id=current_user.id,  # Assuming current_user is a faculty member
            content=form.content.data,
            is_read= True# Admin will read the message later
        )
        db.session.add(new_message)
        db.session.commit()
        
        flash('Message sent to admin!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('message_admin.html', form=form)

@main.route('/create_event', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        date_str = form.date.data
 
        # Check for required fields
        if not title or not description or not date_str:
            flash('All fields are required!', 'danger')
            return render_template('create_event.html', form=form)

        try:
            # Create a new event instance
            new_event = Event(title=title, description=description, date=date_str, user_id=current_user.id)

            # Save the event to the database
            db.session.add(new_event)
            db.session.commit()
            flash('Event created successfully!', 'success')
            return redirect(url_for('main.view_events'))  # Redirect to events list
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating event: {e}', 'danger')
            logging.error(f"Error saving event: {e}")
            return render_template('create_event.html', form=form)

    return render_template('create_event.html', form=form)

@main.route('/view_events')
@login_required
def view_events():
    try:
        events = Event.query.all()
        logging.debug("Fetched %d events.", len(events))
    except Exception as e:
        logging.error(f"Error fetching events: {e}")
        flash('An error occurred while fetching events.', 'danger')
        return redirect(url_for('main.index'))

    return render_template('view_events.html', events=events)
    

@main.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Ensure that the current user is the creator of the event
    if event.user_id != current_user.id:
        flash('You cannot edit this event!', 'danger')
        return redirect(url_for('main.view_events'))

    # Pre-fill form with event data
    form = EventForm(obj=event)
    
    if form.validate_on_submit():
        # Update event details from the form
        event.title = form.title.data
        event.description = form.description.data
        event.date = form.date.data
        
        try:
            db.session.commit()
            logging.debug("Event updated successfully: %s", event.title)
            flash('Event updated successfully!', 'success')
            return redirect(url_for('main.view_events'))
        except Exception as e:
            db.session.rollback()
            logging.error("Error updating event: %s", e)
            flash('An error occurred while updating the event.', 'danger')
    
    # Render the edit event template with the form
    return render_template('edit_event.html', form=form, event=event)
@main.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    try:
        # Delete the event
        db.session.delete(event)
        db.session.commit()
        flash('Event deleted successfully', 'success')
    except Exception as e:
        # Rollback in case of any errors
        db.session.rollback()
        flash(f'Error deleting event: {e}', 'danger')

    # Redirect back to the event list or a suitable page
    return redirect(url_for('main.view_events'))

@main.route('/admin_dashboard', methods=['GET'], endpoint='admin')
@login_required
@role_required('admin')
def admin_dashboard():
    if current_user.role != 'admin':  # Assuming you have an is_admin attribute
        return redirect(url_for('main.index'))
    
    users = User.query.all()
    events = Event.query.all()
    messages = Message.query.all()
    
    return render_template('admin.html', users=users, events=events, messages=messages)
   
@main.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')  # Ensure you have this template created

@main.route('/get_events', methods=['GET'])
def get_events():
    events = Event.query.all()
    events_list = []
    for event in events:
        events_list.append({
            'title': event.title,
            'start': event.date.isoformat(),  # Ensure dates are formatted correctly
            'description': event.description
        })
    return jsonify(events_list)
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.login'))
