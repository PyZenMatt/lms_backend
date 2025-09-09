# Generated manually: add per-area comment fields to ExerciseReview
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0010_peerreviewfeedbackitem_review"),
    ]

    operations = [
        migrations.AddField(
            model_name="exercisereview",
            name="technical_comment",
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="exercisereview",
            name="creative_comment",
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="exercisereview",
            name="following_comment",
            field=models.TextField(null=True, blank=True),
        ),
    ]
