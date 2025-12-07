# Generated manually for WISHLIST table creation
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_tasteconfig_ill_suited_categories_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Wishlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.CharField(db_index=True, help_text='사용자 ID', max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wishlist_items', to='api.product')),
            ],
            options={
                'verbose_name': '찜하기',
                'verbose_name_plural': '찜하기',
                'ordering': ['-created_at'],
                'unique_together': {('user_id', 'product')},
            },
        ),
    ]

