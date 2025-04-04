from django.contrib import admin
from .models import Recipient, Donation, DonatedRecipient

admin.site.register(Recipient)
admin.site.register(Donation)
admin.site.register(DonatedRecipient)
