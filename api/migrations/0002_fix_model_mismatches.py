# Generated manually to fix model mismatches

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        # OnboardingSession에서 제거된 필드들 삭제 (정규화 테이블 사용)
        migrations.RemoveField(
            model_name='onboardingsession',
            name='main_space',
        ),
        migrations.RemoveField(
            model_name='onboardingsession',
            name='priority_list',
        ),
        migrations.RemoveField(
            model_name='onboardingsession',
            name='selected_categories',
        ),
        migrations.RemoveField(
            model_name='onboardingsession',
            name='recommended_products',
        ),
        migrations.RemoveField(
            model_name='onboardingsession',
            name='recommendation_result',
        ),
        # ordering에서 created_date를 created_at으로 변경
        migrations.AlterModelOptions(
            name='member',
            options={
                'verbose_name': '회원',
                'verbose_name_plural': '회원',
                'db_table': 'member',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterModelOptions(
            name='cartnew',
            options={
                'verbose_name': '장바구니',
                'verbose_name_plural': '장바구니',
                'db_table': 'cart',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterModelOptions(
            name='estimate',
            options={
                'verbose_name': '견적',
                'verbose_name_plural': '견적',
                'db_table': 'estimate',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterModelOptions(
            name='consultation',
            options={
                'verbose_name': '상담',
                'verbose_name_plural': '상담',
                'db_table': 'consultation',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterModelOptions(
            name='product',
            options={
                'verbose_name': '제품',
                'verbose_name_plural': '제품',
                'db_table': 'product',
                'ordering': ['-created_at'],
            },
        ),
    ]

