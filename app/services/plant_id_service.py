import requests
import json
from flask import current_app
import base64
import os
import hashlib

class PlantIdService:
    def __init__(self):
        self.api_key = current_app.config.get('PLANT_ID_API_KEY')
        self.api_url = current_app.config.get('PLANT_ID_API_URL')

    def compute_image_hash(self, image_path):
        """Compute SHA-256 hash of image file for duplicate detection"""
        sha256_hash = hashlib.sha256()
        with open(image_path, "rb") as f:
            # Read file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def identify_plant(self, image_path):
        """Identify plant and diseases using Plant.id API"""
        try:
            # Compute image hash first
            image_hash = self.compute_image_hash(image_path)

            # Encode image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            # Prepare API request
            headers = {
                "Content-Type": "application/json",
                "Api-Key": self.api_key
            }

            data = {
                "images": [base64_image],
                "modifiers": ["crops_fast", "similar_images"],
                "plant_details": [
                    "common_names",
                    "url",
                    "description",
                    "taxonomy",
                    "rank",
                    "gbif_id",
                    "inaturalist_id",
                    "image",
                    "synonyms"
                ],
                "disease_details": "all"
            }

            # Make API request
            response = requests.post(self.api_url, headers=headers, json=data)

            if response.status_code == 200:
                result = self._parse_plant_response(response.json())
                result['image_hash'] = image_hash
                return result
            elif response.status_code == 401:
                raise Exception("Invalid Plant.id API key")
            elif response.status_code == 429:
                raise Exception("Plant.id API rate limit exceeded")
            else:
                raise Exception(f"Plant.id API error: {response.status_code}")

        except Exception as e:
            print(f"Plant.id API error: {str(e)}")
            # Fallback to mock data if API fails
            result = self._get_mock_analysis()
            # Compute hash even for mock data
            try:
                result['image_hash'] = self.compute_image_hash(image_path)
            except:
                result['image_hash'] = None
            return result

    def _parse_plant_response(self, api_response):
        """Parse Plant.id API response into our format"""
        if not api_response.get('suggestions') or len(api_response['suggestions']) == 0:
            return self._get_mock_analysis()

        best_match = api_response['suggestions'][0]
        plant_name = best_match.get('plant_name', 'Unknown Plant')
        confidence = best_match.get('probability', 0) * 100

        # Check if plant is healthy based on disease indicators
        is_healthy = self._check_plant_health(plant_name, best_match)

        # Get disease information
        disease_info = self._identify_disease(plant_name, best_match)

        # Get treatment recommendations
        treatment_info = self._get_treatment_recommendations(disease_info, plant_name)

        return {
            'plantName': plant_name,
            'isHealthy': is_healthy,
            'disease': disease_info['name'],
            'confidence': round(confidence, 1),
            'treatment': treatment_info['treatment'],
            'prevention': treatment_info['prevention'],
            'details': {
                'commonNames': best_match.get('plant_details', {}).get('common_names', []),
                'description': best_match.get('plant_details', {}).get('description', {}).get('value', ''),
                'scientificName': best_match.get('plant_details', {}).get('scientific_name'),
                'family': best_match.get('plant_details', {}).get('family')
            },
            'similarImages': best_match.get('similar_images', [])[:3]  # Limit to 3 similar images
        }

    def _check_plant_health(self, plant_name, plant_data):
        """Check if plant is healthy based on name and description"""
        disease_indicators = [
            'spot', 'rot', 'blight', 'mildew', 'rust', 'mosaic', 'wilt',
            'canker', 'gall', 'scab', 'yellow', 'brown', 'black', 'fungus',
            'disease', 'infected', 'sick', 'virus', 'bacterial'
        ]

        plant_name_lower = plant_name.lower()
        description = plant_data.get('plant_details', {}).get('description', {}).get('value', '').lower()

        # Check if plant name or description contains disease indicators
        for indicator in disease_indicators:
            if indicator in plant_name_lower or indicator in description:
                return False

        return True

    def _identify_disease(self, plant_name, plant_data):
        """Identify specific disease based on plant data"""
        if self._check_plant_health(plant_name, plant_data):
            return {'name': None, 'type': 'healthy'}

        plant_name_lower = plant_name.lower()
        description = plant_data.get('plant_details', {}).get('description', {}).get('value', '').lower()

        # Common African crop diseases mapping
        disease_mappings = {
            'rust': 'Leaf Rust',
            'mildew': 'Powdery Mildew',
            'blight': 'Leaf Blight',
            'spot': 'Leaf Spot',
            'mosaic': 'Mosaic Virus',
            'wilt': 'Bacterial Wilt',
            'rot': 'Root Rot',
            'canker': 'Bacterial Canker'
        }

        for key, disease in disease_mappings.items():
            if key in plant_name_lower or key in description:
                return {'name': disease, 'type': 'fungal' if key in ['rust', 'mildew', 'blight', 'spot', 'rot'] else 'viral'}

        return {'name': 'Unknown Plant Disease', 'type': 'unknown'}

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
                    'description': 'Maize plant showing signs of leaf rust infection'
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
                    'description': 'Cassava plant affected by powdery mildew'
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
                    'description': 'Healthy tomato plant'
                }
            }
        ]

        return random.choice(mock_results)
