from geopy.geocoders import Nominatim
import numpy as np
import logging
from datetime import datetime
from django.db.models import Avg
from ..models import Recipient, DonatedRecipient

logger = logging.getLogger('aidhub')

def get_coordinates(location):
    geolocator = Nominatim(user_agent="donation_ai")
    try:
        loc = geolocator.geocode(location)
        if loc:
            return loc.latitude, loc.longitude
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
    return None, None

def predict_urgency(location, donation_type):
    try:
        # Get average urgency from both current and historical data
        current_avg = Recipient.objects.filter(donation_type=donation_type).aggregate(Avg('urgency'))['urgency__avg'] or 0
        historical_avg = DonatedRecipient.objects.filter(donation_type=donation_type).aggregate(Avg('urgency'))['urgency__avg'] or 0
        
        # Combine averages with weights
        combined_avg = (current_avg * 0.7 + historical_avg * 0.3) if historical_avg > 0 else current_avg
        
        if combined_avg > 0:
            # Add some randomization
            urgency = max(1.5, min(5.0, combined_avg + np.random.normal(0, 0.3)))
            return urgency, 0.7
        
        # Default values if no history
        return 3.0, 0.5
        
    except Exception as e:
        logger.error(f"Error in urgency prediction: {e}")
        return 3.0, 0.5
