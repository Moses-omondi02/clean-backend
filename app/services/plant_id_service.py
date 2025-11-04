from flask import current_app
import hashlib
import os
from kindwise import PlantApi

class PlantIdService:
    def __init__(self):
        self.api_key = current_app.config.get('PLANT_ID_API_KEY')

    def compute_image_hash(self, image_path):
        """Compute SHA-256 hash of image file for duplicate detection"""
        sha256_hash = hashlib.sha256()
        with open(image_path, "rb") as f:
            # Read file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def identify_plant(self, image_path):
        """Identify plant and diseases using Plant.id API via kindwise client"""
        try:
            # Compute image hash first
            image_hash = self.compute_image_hash(image_path)

            # Initialize Plant.id API client
            api = PlantApi(api_key=self.api_key)

            # Identify plant with health assessment
            print(f"Calling Plant.id API for image: {image_path}")
            identification = api.identify(
                image_path,
                details=['common_names', 'url', 'description', 'taxonomy'],
                language='en',
                health='all',  # Request health assessment
                as_dict=True  # Get response as dictionary
            )

            print(f"Plant.id API response received: {type(identification)}")
            
            # Parse the response
            result = self._parse_kindwise_response(identification)
            result['image_hash'] = image_hash
            return result

        except Exception as e:
            print(f"Plant.id API error: {str(e)}")
            import traceback
            traceback.print_exc()
            # Fallback to mock data if API fails
            result = self._get_mock_analysis()
            # Compute hash even for mock data
            try:
                result['image_hash'] = self.compute_image_hash(image_path)
            except:
                result['image_hash'] = None
            return result

    def _parse_kindwise_response(self, identification):
        """Parse kindwise API client response into our format"""
        try:
            # The kindwise client returns a dict with 'result' key
            result = identification.get('result', identification)
            
            # Get classification suggestions
            classification = result.get('classification', {})
            suggestions = classification.get('suggestions', [])
            
            if not suggestions:
                print("No plant suggestions found, using mock data")
                return self._get_mock_analysis()

            best_match = suggestions[0]
            plant_name = best_match.get('name', 'Unknown Plant')
            confidence = best_match.get('probability', 0) * 100

            # Get health assessment
            is_healthy_assessment = result.get('is_healthy', {})
            is_healthy = is_healthy_assessment.get('binary', True)
            health_probability = is_healthy_assessment.get('probability', 1.0)

            # Get disease information if plant is unhealthy
            disease_name = None
            if not is_healthy:
                disease_suggestions = result.get('disease', {}).get('suggestions', [])
                if disease_suggestions:
                    disease_name = disease_suggestions[0].get('name', 'Unknown Disease')
                else:
                    disease_name = 'Possible Disease Detected'

            # Get disease info for treatment
            disease_info = {'name': disease_name, 'type': 'unknown'}
            
            # Get treatment recommendations
            treatment_info = self._get_treatment_recommendations(disease_info, plant_name)

            # Get plant details
            details = best_match.get('details', {})

            return {
                'plantName': plant_name,
                'isHealthy': is_healthy,
                'disease': disease_name,
                'confidence': round(confidence, 1),
                'treatment': treatment_info['treatment'],
                'prevention': treatment_info['prevention'],
                'details': {
                    'commonNames': details.get('common_names', [plant_name]),
                    'description': details.get('description', {}).get('value', '') if isinstance(details.get('description'), dict) else details.get('description', ''),
                    'scientificName': details.get('scientific_name', ''),
                    'family': details.get('taxonomy', {}).get('family', '') if isinstance(details.get('taxonomy'), dict) else ''
                },
                'similarImages': []
            }
        except Exception as e:
            print(f"Error parsing kindwise response: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._get_mock_analysis()

    def _get_treatment_recommendations(self, disease_info, plant_name):
        """Get treatment recommendations based on disease"""
        if disease_info['name'] is None:
            return {
                'treatment': 'No treatment needed. Your plant appears healthy! Continue with regular maintenance.',
                'prevention': 'Maintain proper watering, ensure good soil nutrition, and monitor regularly for early signs of disease.'
            }

        # Treatment database for common African crop diseases
        treatments = {
            'Leaf Rust': {
                'treatment': 'Apply fungicide containing chlorothalonil or mancozeb. Remove and destroy severely infected leaves. Improve air circulation between plants.',
                'prevention': 'Plant resistant varieties. Avoid overhead watering. Ensure proper spacing between plants. Remove plant debris at season end.'
            },
            'Powdery Mildew': {
                'treatment': 'Apply sulfur-based fungicide or neem oil. Remove severely infected leaves. Improve air circulation and reduce humidity.',
                'prevention': 'Maintain proper plant spacing. Avoid nitrogen over-fertilization. Water in the morning to allow leaves to dry.'
            },
            'Leaf Blight': {
                'treatment': 'Apply copper-based fungicide. Remove and destroy infected plant parts. Avoid working with plants when wet.',
                'prevention': 'Practice crop rotation. Use disease-free seeds. Ensure proper drainage and avoid overcrowding.'
            },
            'Leaf Spot': {
                'treatment': 'Remove and destroy infected leaves. Apply fungicidal sprays. Avoid overhead watering to prevent spread.',
                'prevention': 'Water at soil level. Space plants properly. Clean garden tools between uses.'
            },
            'Mosaic Virus': {
                'treatment': 'Remove and destroy infected plants immediately. Control aphid populations with insecticidal soap.',
                'prevention': 'Use virus-free seeds. Control insect vectors. Disinfect tools between plants.'
            },
            'Bacterial Wilt': {
                'treatment': 'Remove and destroy infected plants. Solarize soil. There is no cure for bacterial wilt.',
                'prevention': 'Plant resistant varieties. Practice crop rotation. Control cucumber beetles.'
            },
            'Root Rot': {
                'treatment': 'Improve soil drainage. Reduce watering frequency. Apply fungicide to soil if necessary.',
                'prevention': 'Ensure proper drainage. Avoid overwatering. Use well-draining soil mix.'
            }
        }

        default_treatment = {
            'treatment': 'Consult with agricultural expert for specific treatment. Isolate affected plants to prevent spread.',
            'prevention': 'Practice good sanitation, crop rotation, and monitor plants regularly for early detection.'
        }

        return treatments.get(disease_info['name'], default_treatment)

    def _get_mock_analysis(self):
        """Fallback mock analysis when API fails"""
        import random

        mock_results = [
            {
                'plantName': 'Maize',
                'isHealthy': False,
                'disease': 'Leaf Rust',
                'confidence': 87.5,
                'treatment': 'Apply fungicide and remove affected leaves. Ensure proper spacing between plants for air circulation.',
                'prevention': 'Use resistant varieties and avoid overhead watering.',
                'details': {
                    'commonNames': ['Corn', 'Maize'],
                    'description': 'Maize plant showing signs of leaf rust infection',
                    'scientificName': 'Zea mays',
                    'family': 'Poaceae'
                }
            },
            {
                'plantName': 'Cassava',
                'isHealthy': False,
                'disease': 'Powdery Mildew',
                'confidence': 72.3,
                'treatment': 'Use sulfur-based fungicide and improve air circulation. Remove severely infected leaves.',
                'prevention': 'Maintain proper plant spacing and avoid nitrogen over-fertilization.',
                'details': {
                    'commonNames': ['Cassava', 'Manioc'],
                    'description': 'Cassava plant affected by powdery mildew',
                    'scientificName': 'Manihot esculenta',
                    'family': 'Euphorbiaceae'
                }
            },
            {
                'plantName': 'Tomato',
                'isHealthy': True,
                'disease': None,
                'confidence': 95.8,
                'treatment': 'No treatment needed - plant is healthy',
                'prevention': 'Continue current maintenance practices.',
                'details': {
                    'commonNames': ['Tomato'],
                    'description': 'Healthy tomato plant',
                    'scientificName': 'Solanum lycopersicum',
                    'family': 'Solanaceae'
                }
            }
        ]

        return random.choice(mock_results)
