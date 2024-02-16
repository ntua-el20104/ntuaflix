# Generated by Django 5.0.2 on 2024-02-16 21:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0021_alter_user_password_alter_user_username'),
    ]

    operations = [
        migrations.CreateModel(
            name='Disliked',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=30)),
                ('tconst', models.CharField(max_length=255)),
            ],
            options={
                'unique_together': {('username', 'tconst')},
            },
        ),
        migrations.CreateModel(
            name='Liked',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=30)),
                ('tconst', models.CharField(max_length=255)),
            ],
            options={
                'unique_together': {('username', 'tconst')},
            },
        ),
    ]