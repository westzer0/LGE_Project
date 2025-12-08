# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_tasteconfig_ill_suited_categories_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='portfolio',
            name='internal_key',
            field=models.CharField(blank=True, help_text='포트폴리오 내부 키 (portfolio_id와 동일 또는 별도 키)', max_length=20, null=True, unique=True),
        ),
        migrations.AddIndex(
            model_name='portfolio',
            index=models.Index(fields=['internal_key'], name='api_portfol_interna_idx'),
        ),
    ]

