# Generated by Django 5.0.1 on 2024-02-08 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0017_alter_episode_parenttconst'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crews',
            name='directors',
            field=models.CharField(blank=True, default='\\N', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='crews',
            name='writers',
            field=models.CharField(blank=True, default='\\N', max_length=255, null=True),
        ),
    ]