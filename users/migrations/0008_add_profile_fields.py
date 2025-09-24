from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0007_add_wallet_nonce"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="city",
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="via",
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="cap",
            field=models.CharField(max_length=20, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="linkedin",
            field=models.URLField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="github",
            field=models.URLField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="instagram",
            field=models.URLField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="facebook",
            field=models.URLField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="skills",
            field=models.TextField(blank=True, null=True),
        ),
    ]
