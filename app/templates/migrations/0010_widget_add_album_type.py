from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("templates", "0009_ensure_qr_action_tables"),
    ]

    operations = [
        migrations.AlterField(
            model_name="widget",
            name="type",
            field=models.CharField(
                choices=[
                    ("text", "Text"),
                    ("marquee", "Marquee"),
                    ("weather", "Weather"),
                    ("qr_action", "QR Action"),
                    ("image", "Image"),
                    ("video", "Video"),
                    ("album", "Album Playlist"),
                    ("clock", "Clock"),
                    ("date", "Date"),
                    ("weekday", "Weekday"),
                    ("countdown", "Countdown"),
                    ("webview", "Web View"),
                    ("chart", "Chart"),
                ],
                help_text="Type of widget content",
                max_length=20,
            ),
        ),
    ]
