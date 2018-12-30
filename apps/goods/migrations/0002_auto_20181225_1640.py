# Generated by Django 2.1.4 on 2018-12-25 08:40

from django.db import migrations, models
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='goodssku',
            name='simple_desc',
            field=models.CharField(default='', max_length=100, verbose_name='商品简介'),
        ),
        migrations.AlterField(
            model_name='goodssku',
            name='desc',
            field=tinymce.models.HTMLField(blank=True, verbose_name='商品详情'),
        ),
    ]