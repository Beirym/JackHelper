# Generated by Django 5.1.1 on 2024-10-22 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='normal_hours',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
