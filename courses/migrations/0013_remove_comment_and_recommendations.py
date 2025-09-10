from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0012_backfill_per_area_comments'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='exercisereview',
            name='comment',
        ),
        migrations.RemoveField(
            model_name='exercisereview',
            name='recommendations',
        ),
    ]
