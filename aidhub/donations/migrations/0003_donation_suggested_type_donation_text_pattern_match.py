# Generated by Django 5.2 on 2025-04-04 16:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0002_donation_classified_type_donation_donation_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='donation',
            name='suggested_type',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='donation',
            name='text_pattern_match',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
