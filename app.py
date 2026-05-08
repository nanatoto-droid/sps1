import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json

# Load environment variables
load_dotenv()

# Setup logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///sps.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Rate limiting for contact form
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Initialize database
db.init_app(app)

# Database Models
class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    email: Mapped[str] = mapped_column(db.String(200), nullable=False)
    phone: Mapped[str] = mapped_column(db.String(50), nullable=True)
    company: Mapped[str] = mapped_column(db.String(200), nullable=True)
    message: Mapped[str] = mapped_column(db.Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)
    is_read: Mapped[bool] = mapped_column(db.Boolean, default=False)

class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'
    
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    email: Mapped[str] = mapped_column(db.String(200), unique=True, nullable=False)
    subscribed_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)

# Load product data
def load_products():
    with open('data/products.json', 'r') as f:
        return json.load(f)

# Context processor for all templates
@app.context_processor
def inject_globals():
    products = load_products()
    return {
        'current_year': datetime.utcnow().year,
        'contact_email': os.getenv('CONTACT_EMAIL', 'sales@spssupplies.com'),
        'phone_numbers': ['+254783545455', '+254795545438'],
        'address': '2nd Floor Grey Park Heights, Off Eastern Bypass, Utawala, Nairobi, Kenya'
    }

# Routes
@app.route('/')
def home():
    products = load_products()
    featured_products = []
    
    # Get featured products (first 2 from each category)
    for category in ['atm', 'banknote_sorters', 'ccdm']:
        if products.get(category):
            featured_products.extend(products[category][:2])
    
    return render_template('index.html', featured_products=featured_products[:6])

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/products')
def products():
    products = load_products()
    category = request.args.get('category', 'all')
    return render_template('products.html', products=products, active_category=category)

@app.route('/product/<category>/<product_id>')
def product_detail(category, product_id):
    products = load_products()
    product = None
    
    if category in products:
        for p in products[category]:
            if p.get('id') == product_id:
                product = p
                product['category_name'] = category
                break
    
    if not product:
        return render_template('404.html'), 404
    
    return render_template('product-detail.html', product=product)

@app.route('/services')
def services():
    services_list = [
        {
            'id': 'atm-maintenance',
            'title': 'Multivendor ATM Maintenance',
            'description': 'Single Point of Contact for all ATM manufacturers including NCR, Diebold Nixdorf, Hyosung',
            'features': [
                'Corrective and Preventive Maintenance',
                'ATM Parts Repairs',
                'Spare Parts Supply',
                '24/7 Onsite and Remote Support'
            ],
            'icon': 'atm'
        },
        {
            'id': 'installation',
            'title': 'Professional Installation',
            'description': 'End-to-end installation services for all our equipment',
            'features': [
                'Site survey and preparation',
                'Professional installation',
                'User training',
                'Documentation'
            ],
            'icon': 'install'
        },
        {
            'id': 'consulting',
            'title': 'Security Consulting',
            'description': 'Security and cryptographic solutions for your cash operations',
            'features': [
                'Security assessment',
                'Cryptographic solutions',
                'Compliance readiness',
                'Ongoing monitoring'
            ],
            'icon': 'security'
        },
        {
            'id': 'training',
            'title': 'User Training',
            'description': 'Comprehensive training for your staff on all equipment',
            'features': [
                'On-site training',
                'Remote training options',
                'Documentation provided',
                'Refresher courses available'
            ],
            'icon': 'training'
        }
    ]
    return render_template('services.html', services=services_list)

@app.route('/contact', methods=['GET', 'POST'])
@limiter.limit("5 per hour")  # Limit contact form submissions
def contact():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            company = request.form.get('company')
            message = request.form.get('message')
            
            # Basic validation
            if not name or not email or not message:
                return render_template('contact.html', error="Please fill in all required fields.")
            
            # Save to database
            contact = ContactMessage(
                name=name,
                email=email,
                phone=phone,
                company=company,
                message=message
            )
            db.session.add(contact)
            db.session.commit()
            
            logger.info(f"New contact message from {email}")
            
            return render_template('contact.html', success="Thank you! We will get back to you within 24 hours.")
        
        except Exception as e:
            logger.error(f"Error saving contact message: {e}")
            return render_template('contact.html', error="An error occurred. Please try again or call us directly.")
    
    return render_template('contact.html')

@app.route('/newsletter/subscribe', methods=['POST'])
@limiter.limit("10 per hour")
def subscribe_newsletter():
    try:
        email = request.form.get('email')
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Check if already subscribed
        existing = NewsletterSubscriber.query.filter_by(email=email).first()
        if existing:
            return jsonify({'message': 'Already subscribed!'}), 200
        
        subscriber = NewsletterSubscriber(email=email)
        db.session.add(subscriber)
        db.session.commit()
        
        return jsonify({'message': 'Successfully subscribed!'}), 200
    
    except Exception as e:
        logger.error(f"Newsletter error: {e}")
        return jsonify({'error': 'Subscription failed'}), 500

# API endpoint for product search
@app.route('/api/search')
def search_products():
    query = request.args.get('q', '').lower()
    if not query or len(query) < 2:
        return jsonify({'results': []})
    
    products = load_products()
    results = []
    
    for category, items in products.items():
        for item in items:
            if (query in item.get('name', '').lower() or 
                query in item.get('description', '').lower()):
                results.append({
                    'id': item.get('id'),
                    'name': item.get('name'),
                    'category': category,
                    'url': f"/product/{category}/{item.get('id')}"
                })
    
    return jsonify({'results': results[:10]})

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"500 error: {e}")
    return render_template('500.html'), 500

# Create tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created")

if __name__ == '__main__':
    # For production, use gunicorn instead
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)