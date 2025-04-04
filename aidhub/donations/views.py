from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.db.models import Count, Avg
from django.core.exceptions import ObjectDoesNotExist
from .models import Recipient, Donation, DonatedRecipient
from .ml.predictor import predict_urgency, get_coordinates
from .ml.trainer import train_model, train_trend_model
from geopy.distance import geodesic
import json
import logging
from .ml.image_classifier import classifier  # Add this import
from .utils.text_matcher import match_donation_text  # Add this import
from django.views.decorators.csrf import csrf_exempt  # Add this import
from django.db import transaction  # Add this import

logger = logging.getLogger('aidhub')

class IndexView(View):
    def get(self, request):
        return render(request, 'donations/index.html')

class TrendingView(View):
    def get(self, request):
        try:
            trends = Recipient.objects.values('donation_type') \
                                   .annotate(count=Count('id')) \
                                   .order_by('-count')[:3]
            
            trend_list = []
            for trend in trends:
                trend_list.append({
                    "type": trend['donation_type'].capitalize(),
                    "count": trend['count'],
                    "message": f"{trend['donation_type'].capitalize()} (requested {trend['count']} times)"
                })
            
            return JsonResponse({
                "message": "Current Donation Needs",
                "trends": trend_list
            })
        except Exception as e:
            logger.error(f"Error getting trends: {e}")
            return JsonResponse({
                "message": "Error getting trends",
                "trends": []
            })

class RecipientListView(View):
    def get(self, request):
        donation_type = request.GET.get('type', '').lower()
        donor_location = request.GET.get('location', '')
        
        if not donation_type or not donor_location:
            return JsonResponse({"error": "Missing donation type or location"}, status=400)
        
        try:
            donor_lat, donor_lon = get_coordinates(donor_location)
            if donor_lat is None:
                return JsonResponse({"error": "Invalid location"}, status=400)
            
            recipients = Recipient.objects.filter(donation_type=donation_type)
            if not recipients:
                return JsonResponse({"error": "No matching recipients found"}, status=404)
            
            recipient_list = []
            for recipient in recipients:
                confidence = predict_urgency(recipient.location, recipient.donation_type)[1]
                # Calculate distance
                distance = geodesic(
                    (donor_lat, donor_lon),
                    (recipient.latitude, recipient.longitude)
                ).km
                
                recipient_list.append({
                    'id': recipient.id,
                    'name': recipient.name,
                    'location': recipient.location,
                    'latitude': recipient.latitude,
                    'longitude': recipient.longitude,
                    'donation_type': recipient.donation_type,
                    'urgency': recipient.urgency,
                    'contact': recipient.contact,
                    'confidence': confidence,
                    'distance': distance  # Add distance to response
                })
            
            # Sort by distance and urgency
            recipient_list.sort(key=lambda x: (x['distance'] * 0.3) - (x['urgency'] * 0.7))
            
            return JsonResponse({
                "recipients": recipient_list,
                "donor_coordinates": {
                    "latitude": donor_lat,
                    "longitude": donor_lon
                },
                "donor_location": donor_location
            })
        except Exception as e:
            logger.error(f"Error listing recipients: {e}")
            return JsonResponse({"error": str(e)}, status=500)

class DonationView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['donor_name', 'donor_contact', 'donation_type', 'pickup_location', 'recipient_id']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }, status=400)

            try:
                with transaction.atomic():
                    # Get recipient first
                    recipient = Recipient.objects.get(id=data['recipient_id'])
                    
                    # Create DonatedRecipient record
                    donated = DonatedRecipient.objects.create(
                        name=recipient.name,
                        location=recipient.location,
                        latitude=recipient.latitude,
                        longitude=recipient.longitude,
                        donation_type=recipient.donation_type,
                        urgency=recipient.urgency,
                        donor_name=data['donor_name'],
                        recipient_contact=recipient.contact,
                        donor_contact=data['donor_contact'],
                        pickup_location=data['pickup_location']
                    )
                    
                    # Create Donation record with new fields
                    donation = Donation.objects.create(
                        donor_name=data['donor_name'],
                        donor_contact=data['donor_contact'],
                        donation_type=data['donation_type'].lower(),
                        pickup_location=data['pickup_location'],
                        recipient=recipient,
                        suggested_type=data.get('suggested_type', ''),
                        text_pattern_match=data.get('text_pattern_match', '')
                    )
                    
                    # Delete recipient only after successful creation
                    recipient.delete()

                    return JsonResponse({
                        "success": True,
                        "message": "Donation successful",
                        "details": {
                            "donor": data['donor_name'],
                            "recipient": recipient.name,
                            "type": data['donation_type']
                        }
                    })
                    
            except ObjectDoesNotExist:
                return JsonResponse({
                    "success": False,
                    "error": "Recipient not found"
                }, status=404)
                
            except Exception as e:
                logger.error(f"Database transaction error: {str(e)}")
                return JsonResponse({
                    "success": False,
                    "error": f"Database error occurred while processing donation: {str(e)}"
                }, status=500)

        except json.JSONDecodeError:
            return JsonResponse({
                "success": False,
                "error": "Invalid JSON data"
            }, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in donation processing: {str(e)}")
            return JsonResponse({
                "success": False,
                "error": "An unexpected error occurred while processing your donation"
            }, status=500)

class AddRecipientView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            required = ['name', 'location', 'donation_type', 'contact']
            
            if not all(field in data for field in required):
                return JsonResponse({"error": "Missing required fields"}, status=400)
            
            latitude, longitude = get_coordinates(data['location'])
            if latitude is None:
                return JsonResponse({"error": "Invalid location"}, status=400)
            
            urgency, confidence = predict_urgency(data['location'], data['donation_type'])
            
            recipient = Recipient.objects.create(
                name=data['name'],
                location=data['location'],
                latitude=latitude,
                longitude=longitude,
                donation_type=data['donation_type'].lower(),
                urgency=urgency,
                contact=data['contact']
            )
            
            # Retrain models
            train_model()
            train_trend_model()
            
            return JsonResponse({
                "success": True,
                "message": f"Recipient added successfully! Urgency level {urgency:.2f}/5.0 (confidence: {confidence:.2%})",
                "urgency": urgency,
                "confidence": confidence
            })
            
        except Exception as e:
            logger.error(f"Error adding recipient: {e}")
            return JsonResponse({"error": str(e)}, status=500)

class HistoryView(View):
    def get(self, request):
        try:
            transactions = DonatedRecipient.objects.all().order_by('-transaction_date')
            type_stats = DonatedRecipient.objects.values('donation_type') \
                                                .annotate(
                                                    count=Count('id'),
                                                    avg_urgency=Avg('urgency')
                                                ) \
                                                .order_by('-count')
            
            transaction_list = []
            for t in transactions:
                transaction_list.append({
                    "recipient_name": t.name,
                    "location": t.location,
                    "donation_type": t.donation_type,
                    "donor_name": t.donor_name,
                    "recipient_contact": t.recipient_contact,
                    "donor_contact": t.donor_contact,
                    "pickup_location": t.pickup_location,
                    "date": t.transaction_date
                })
            
            stats_list = []
            for stat in type_stats:
                stats_list.append({
                    "donation_type": stat['donation_type'].capitalize(),
                    "count": stat['count'],
                    "avg_urgency": float(stat['avg_urgency'])
                })
            
            return JsonResponse({
                "transactions": transaction_list,
                "type_stats": stats_list
            })
            
        except Exception as e:
            logger.error(f"Error getting donation history: {e}")
            return JsonResponse({
                "transactions": [],
                "type_stats": [],
                "error": str(e)
            })

class SummaryStatsView(View):
    def get(self, request):
        try:
            # Get total donations by combining current donations and donated history
            total_donations = (
                Donation.objects.count() + 
                DonatedRecipient.objects.count()
            )
            
            # Get unique donors by combining both tables and using distinct
            unique_donors = len(set(
                list(Donation.objects.values_list('donor_name', flat=True)) +
                list(DonatedRecipient.objects.values_list('donor_name', flat=True))
            ))
            
            # Get unique communities served
            communities_served = len(set(
                list(Recipient.objects.values_list('location', flat=True)) +
                list(DonatedRecipient.objects.values_list('location', flat=True))
            ))
            
            return JsonResponse({
                'total_donations': total_donations,
                'unique_donors': unique_donors,
                'communities_served': communities_served
            })
            
        except Exception as e:
            logger.error(f"Error getting summary stats: {e}")
            return JsonResponse({
                'total_donations': 0,
                'unique_donors': 0,
                'communities_served': 0
            })

class ClassifyImageView(View):  # Add this new view class
    def post(self, request):
        try:
            if 'image' not in request.FILES:
                return JsonResponse({
                    'success': False,
                    'message': 'No image file provided'
                }, status=400)

            image_file = request.FILES['image']
            category, confidence = classifier.classify_image(image_file)

            return JsonResponse({
                'success': True,
                'category': category,
                'confidence': confidence
            })
        except Exception as e:
            logger.error(f"Error classifying image: {e}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

@csrf_exempt
def detect_donation_type(request):  # Add this new function
    if request.method == 'POST':
        data = json.loads(request.body)
        text = data.get('text', '')
        matches = match_donation_text(text)
        return JsonResponse({
            'success': True,
            'matches': matches
        })
    return JsonResponse({'success': False})
