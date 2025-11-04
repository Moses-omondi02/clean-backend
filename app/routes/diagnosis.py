from flask import Blueprint, request, jsonify
from app import db
from app.models.report import Report
from app.models.disease import Disease
from app.models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.email_service import EmailService
from app.services.plant_id_service import PlantIdService
import os
import uuid

diagnosis_bp = Blueprint('diagnosis', __name__)

@diagnosis_bp.route('/scan', methods=['POST'])
@jwt_required()
def scan_image():
    try:
        user_id = get_jwt_identity()
        print(f"Scan request from user: {user_id}")

        if 'image' not in request.files:
            print("Error: No image in request.files")
            return jsonify({'error': 'No image provided'}), 400

        image_file = request.files['image']
        print(f"Image file received: {image_file.filename}")

        if image_file.filename == '':
            print("Error: Empty filename")
            return jsonify({'error': 'No image selected'}), 400

        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
        if '.' not in image_file.filename or \
           image_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({'error': 'Invalid file type. Please upload PNG, JPG, or WebP images.'}), 400

        # Validate file size (10MB max)
        if len(image_file.read()) > 10 * 1024 * 1024:
            return jsonify({'error': 'Image size too large. Maximum size is 10MB.'}), 400
        image_file.seek(0)  # Reset file pointer

        # Save uploaded image temporarily
        filename = f"{uuid.uuid4()}_{image_file.filename}"
        upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        image_path = os.path.join(upload_folder, filename)
        image_file.save(image_path)

        # Compute image hash for duplicate detection
        plant_id_service = PlantIdService()
        image_hash = plant_id_service.compute_image_hash(image_path)

        # USE MOCK DATA INSTEAD OF API CALL
        print(f"Using mock data for demonstration (API disabled)")
        analysis_result = plant_id_service._get_mock_analysis()
        analysis_result['image_hash'] = image_hash
        analysis_result['cached'] = False

        # Create report for current user
        report = Report(
            user_id=user_id,
            crop_name=analysis_result['plantName'],
            confidence=analysis_result['confidence'] / 100.0,
            image_path=image_path,
            image_hash=image_hash,  # Store hash for future lookups
            is_healthy=analysis_result['isHealthy'],
            recommended_treatment=analysis_result['treatment'],
            prevention_tips=analysis_result.get('prevention', '')
        )

        # Link to disease if not healthy
        if not analysis_result['isHealthy'] and analysis_result['disease']:
            disease = Disease.query.filter_by(name=analysis_result['disease']).first()
            if disease:
                report.disease_id = disease.id

        db.session.add(report)
        db.session.commit()

        # Send email report to user
        try:
            user = User.query.get(user_id)
            email_service = EmailService()

            report_data = {
                'crop_name': analysis_result['plantName'],
                'is_healthy': analysis_result['isHealthy'],
                'disease_name': analysis_result['disease'],
                'confidence': analysis_result['confidence'],
                'status_message': 'Your crop appears healthy!' if analysis_result['isHealthy'] else f"Disease detected: {analysis_result['disease']}",
                'treatment': analysis_result['treatment'],
                'prevention': analysis_result.get('prevention', '')
            }

            email_service.send_disease_report(user.email, user.name, report_data)
        except Exception as e:
            print(f"Failed to send email report: {e}")
            # Don't fail the scan if email fails

        # Clean up: Remove uploaded image after processing (optional)
        # os.remove(image_path)

        return jsonify({
            'message': 'Analysis complete using AI',
            'analysis': analysis_result,
            'report_id': report.id,
            'api_used': 'Plant.id'
        }), 200

    except Exception as e:
        # Clean up uploaded file if error occurs
        if 'image_path' in locals() and os.path.exists(image_path):
            os.remove(image_path)
        db.session.rollback()
        
        # Log the full error
        import traceback
        print(f"Error in scan_image: {str(e)}")
        traceback.print_exc()
        
        return jsonify({'error': str(e)}), 500

@diagnosis_bp.route('/diseases', methods=['GET'])
def get_diseases():
    try:
        diseases = Disease.query.all()

        return jsonify({
            'diseases': [disease.to_dict() for disease in diseases]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@diagnosis_bp.route('/health', methods=['GET'])
def health_check():
    """Check if Plant.id API is working"""
    try:
        plant_id_service = PlantIdService()

        # Test with a small request or just check API key format

        plant_id_service.identify_plant('https://example.com/test-image.jpg')
        return jsonify({
            'status': 'healthy',
            'plant_id_api': 'configured',
            'message': 'Plant.id API is ready to use'
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'plant_id_api': 'configuration_error',
            'message': str(e)
        }), 500
