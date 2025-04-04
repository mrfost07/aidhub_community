from django.core.management.base import BaseCommand
from donations.models import Donation, Recipient, DonatedRecipient

class Command(BaseCommand):
    help = 'Reset all data in the database while keeping the structure'

    def handle(self, *args, **options):
        self.stdout.write('Deleting all data...')
        
        # Delete all data from existing models
        DonatedRecipient.objects.all().delete()  # Delete this first due to relationships
        Recipient.objects.all().delete()
        Donation.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS('Successfully cleared all data'))

if __name__ == '__main__':
    import os
    import django
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aidhub.settings')
    django.setup()
    
    cmd = Command()
    cmd.handle()
