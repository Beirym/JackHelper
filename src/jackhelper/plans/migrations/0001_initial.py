# Generated by Django 5.1.1 on 2024-10-14 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city', models.CharField(max_length=3)),
                ('year', models.IntegerField()),
                ('month', models.IntegerField()),
                ('revenue', models.IntegerField()),
                ('works_revenue', models.IntegerField()),
                ('spare_parts_revenue', models.IntegerField()),
            ],
            options={
                'db_table': 'plans',
            },
        ),
    ]
