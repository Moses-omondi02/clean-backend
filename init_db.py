#!/usr/bin/env python3
"""
Database initialization script for production deployment.
This script creates all database tables and initializes sample data.
"""
import os
import sys

# Ensure we're using production config
os.environ['FLASK_ENV'] = 'production'

from app import create_app, db
from app.models import User, Crop, Disease, Treatment, Report

def init_database():
    """Initialize database tables and sample data"""
    app = create_app()
    
    with app.app_context():
        try:
            # Log database URI (masked)
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')
            if db_uri and db_uri != 'Not set':
                import re
                masked_uri = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', db_uri)
                print(f"📊 Database URI: {masked_uri}")
            else:
                print("❌ ERROR: SQLALCHEMY_DATABASE_URI is not set!")
                sys.exit(1)
            
            # Test database connection
            print("🔍 Testing database connection...")
            db.session.execute(db.text('SELECT 1'))
            print("✅ Database connection successful!")
            
            # Create all tables
            print("📝 Creating database tables...")
            db.create_all()
            print("✅ Database tables created!")
            
            # Initialize sample crops
            print("🌱 Initializing sample data...")
            crops = [
                Crop(name='Maize', scientific_name='Zea mays', common_names='Corn,Maize'),
                Crop(name='Cassava', scientific_name='Manihot esculenta', common_names='Cassava,Manioc'),
                Crop(name='Tomato', scientific_name='Solanum lycopersicum', common_names='Tomato'),
                Crop(name='Bean', scientific_name='Phaseolus vulgaris', common_names='Bean,Common Bean')
            ]
            
            for crop in crops:
                if not Crop.query.filter_by(name=crop.name).first():
                    db.session.add(crop)
                    print(f"  ➕ Added crop: {crop.name}")
            
            db.session.commit()
            print("✅ Sample data initialized!")
            
            # Verify tables exist
            print("🔍 Verifying tables...")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Tables found: {', '.join(tables)}")
            
            expected_tables = ['user', 'crop', 'disease', 'treatment', 'report']
            missing_tables = [t for t in expected_tables if t not in tables]
            if missing_tables:
                print(f"⚠️ WARNING: Missing tables: {', '.join(missing_tables)}")
            else:
                print("✅ All expected tables exist!")
            
            print("\n🎉 Database initialization completed successfully!")
            return 0
            
        except Exception as e:
            import traceback
            print(f"\n❌ Database initialization failed!")
            print(f"Error: {e}")
            print(f"\nTraceback:\n{traceback.format_exc()}")
            return 1

if __name__ == '__main__':
    exit_code = init_database()
    sys.exit(exit_code)
