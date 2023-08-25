# Generated by Django 4.2 on 2023-04-14 16:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LittleLemonAPI', '0002_alter_orderitem_order'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cart',
            old_name='quanity',
            new_name='quantity',
        ),
        migrations.RenameField(
            model_name='orderitem',
            old_name='quanity',
            new_name='quantity',
        ),
        migrations.AlterField(
            model_name='order',
            name='date',
            field=models.DateField(auto_now_add=True, db_index=True),
        ),
    ]
