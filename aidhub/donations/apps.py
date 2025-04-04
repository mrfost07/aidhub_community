from django.apps import AppConfig
import os

class DonationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'donations'

    def ready(self):
        if os.environ.get('RUN_MAIN') and os.environ.get('DJANGO_SETTINGS_MODULE'):
            try:
                # More reliable check for table existence
                from django.db import connection
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT EXISTS(
                        SELECT * FROM pg_tables 
                        WHERE tablename = 'donations_recipient'
                        AND schemaname = 'public'
                    );
                """)
                table_exists = cursor.fetchone()[0]
                if table_exists:
                    from .ml.trainer import train_model, train_trend_model
                    from django.conf import settings
                    from pathlib import Path

                    model_path = Path(settings.BASE_DIR) / 'donations' / 'ml' / 'models' / 'donation_matcher.pkl'
                    if not model_path.exists():
                        print("Initializing ML models...")
                        train_model()
                        train_trend_model()
            except Exception:
                # Tables don't exist yet or other error, skip ML initialization
                pass
