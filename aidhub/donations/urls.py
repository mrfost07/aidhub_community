from django.urls import path
from .views import (
    IndexView, TrendingView, RecipientListView,
    DonationView, AddRecipientView, HistoryView, SummaryStatsView,
    ClassifyImageView
)
from . import views

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    # Add both with and without trailing slash for each API endpoint
    path('api/trending', TrendingView.as_view(), name='trending'),
    path('api/trending/', TrendingView.as_view(), name='trending-slash'),
    path('api/recipients', RecipientListView.as_view(), name='recipients'),
    path('api/recipients/', RecipientListView.as_view(), name='recipients-slash'),
    path('api/donate', DonationView.as_view(), name='donate'),
    path('api/donate/', DonationView.as_view(), name='donate-slash'),
    path('api/add_recipient', AddRecipientView.as_view(), name='add_recipient'),
    path('api/add_recipient/', AddRecipientView.as_view(), name='add_recipient-slash'),
    path('api/history', HistoryView.as_view(), name='history'),
    path('api/history/', HistoryView.as_view(), name='history-slash'),
    path('api/summary_stats', SummaryStatsView.as_view(), name='summary_stats'),
    path('api/summary_stats/', SummaryStatsView.as_view(), name='summary_stats-slash'),
    path('api/classify_image', ClassifyImageView.as_view(), name='classify_image'),
    path('api/classify_image/', ClassifyImageView.as_view(), name='classify_image-slash'),
    path('api/detect_donation_type/', views.detect_donation_type, name='detect_donation_type'),
]
