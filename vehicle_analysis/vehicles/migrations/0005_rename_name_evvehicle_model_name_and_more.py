# Generated by Django 5.2 on 2025-04-24 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0004_phevvehicle'),
    ]

    operations = [
        migrations.RenameField(
            model_name='evvehicle',
            old_name='name',
            new_name='model_name',
        ),
        migrations.RenameField(
            model_name='hevvehicle',
            old_name='name',
            new_name='model_name',
        ),
        migrations.RenameField(
            model_name='icevehicle',
            old_name='name',
            new_name='model_name',
        ),
        migrations.RenameField(
            model_name='phevvehicle',
            old_name='name',
            new_name='model_name',
        ),
        migrations.AddField(
            model_name='evvehicle',
            name='mark_name',
            field=models.CharField(default='', max_length=120, verbose_name='Название марки'),
        ),
        migrations.AddField(
            model_name='hevvehicle',
            name='mark_name',
            field=models.CharField(default='', max_length=120, verbose_name='Название марки'),
        ),
        migrations.AddField(
            model_name='icevehicle',
            name='mark_name',
            field=models.CharField(default='', max_length=120, verbose_name='Название марки'),
        ),
        migrations.AddField(
            model_name='phevvehicle',
            name='mark_name',
            field=models.CharField(default='', max_length=120, verbose_name='Название марки'),
        ),
    ]
