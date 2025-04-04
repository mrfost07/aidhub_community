from django.urls import path
from .views import (
    IndexView, TrendingView, RecipientListView,
    DonationView, AddRecipientView, HistoryView, SummaryStatsView
)

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('api/trending/', TrendingView.as_view(), name='trending'),
    path('api/recipients/', RecipientListView.as_view(), name='recipients'),
    path('api/donate/', DonationView.as_view(), name='donate'),
    path('api/add_recipient/', AddRecipientView.as_view(), name='add_recipient'),
    path('api/history/', HistoryView.as_view(), name='history'),
    path('api/summary_stats/', SummaryStatsView.as_view(), name='summary_stats'),
]
