# Generated by Django 4.1.2 on 2022-10-23 10:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mboard', '0003_post_session_rating_calctime_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='poster',
        ),
    ]
