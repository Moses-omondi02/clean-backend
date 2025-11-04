import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import User, Crop, Disease, Treatment

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Crop': Crop,
        'Disease': Disease,
        'Treatment': Treatment
    }

def init_sample_data():
    """Initialize sample data matching frontend"""
    with app.app_context():
        # Create sample crops matching frontend
        crops = [
            Crop(name='Maize', scientific_name='Zea mays', common_names='Corn,Maize'),
            Crop(name='Cassava', scientific_name='Manihot esculenta', common_names='Cassava,Manioc'),
            Crop(name='Tomato', scientific_name='Solanum lycopersicum', common_names='Tomato'),
            Crop(name='Bean', scientific_name='Phaseolus vulgaris', common_names='Bean,Common Bean')
        ]
        
        for crop in crops:
            if not Crop.query.filter_by(name=crop.name).first():
                db.session.add(crop)
        
        db.session.commit()
        print("✅ Agri Smart Detect Backend initialized successfully!")

# Initialize database tables and sample data when app starts
with app.app_context():
    try:
        # Log database URI (without password) for debugging
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')
        if db_uri and db_uri != 'Not set':
            # Mask password in URI for logging
            import re
            masked_uri = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', db_uri)
            print(f"📊 Database URI: {masked_uri}")
        else:
            print("⚠️ WARNING: SQLALCHEMY_DATABASE_URI is not set!")
        
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        print("✅ Database connection successful!")
        
        # Create tables
        db.create_all()
        print("✅ Database tables created!")
        
        # Initialize sample data
        init_sample_data()
        print("✅ Database initialized successfully!")
    except Exception as e:
        import traceback
        print(f"❌ Database initialization error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        # Don't crash the app, but log the error
        print("⚠️ App will start but database operations may fail!")

if __name__ == '__main__':
    # This block only runs when using Flask dev server (not with gunicorn)
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    print(f"🚀 Agri Smart Detect Backend running on port {port} (debug={debug_mode})")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)