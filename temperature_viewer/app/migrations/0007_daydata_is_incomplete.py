# Generated by Django 3.2.12 on 2022-03-12 04:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_auto_20220311_1123'),
    ]

    operations = [
        migrations.AddField(
            model_name='daydata',
            name='is_incomplete',
            field=models.BooleanField(default=False),
        ),
    ]
