# Generated by Django 5.1.6 on 2025-02-28 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offers_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='offer',
            name='status',
            field=models.CharField(choices=[('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='in_progress', max_length=20),
        ),
    ]
