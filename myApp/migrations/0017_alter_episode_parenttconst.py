# Generated by Django 5.0.1 on 2024-02-08 12:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0016_principals'),
    ]

    operations = [
        migrations.AlterField(
            model_name='episode',
            name='parentTconst',
            field=models.CharField(default='\\N', max_length=255),
        ),
    ]