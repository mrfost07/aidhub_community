from django.apps import AppConfig
import os

class DonationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'donations'

    def ready(self):
        # Only run when the server is actually starting, not during migrations
        if os.environ.get('RUN_MAIN') and os.environ.get('DJANGO_SETTINGS_MODULE'):
            from django.db import connection
            from django.db.utils import OperationalError
            try:
                # Check if tables exist
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='donations_recipient'")
                    if cursor.fetchone()[0] > 0:
                        from .ml.trainer import train_model, train_trend_model
                        from django.conf import settings
                        from pathlib import Path

                        model_path = Path(settings.BASE_DIR) / 'donations' / 'ml' / 'models' / 'donation_matcher.pkl'
                        if not model_path.exists():
                            print("Initializing ML models...")
                            train_model()
                            train_trend_model()
            except OperationalError:
                # Tables don't exist yet, skip ML initialization
                pass
