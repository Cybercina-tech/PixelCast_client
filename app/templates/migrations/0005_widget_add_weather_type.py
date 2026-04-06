from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("templates", "0004_widget_add_marquee_type"),
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
                    ("image", "Image"),
                    ("video", "Video"),
                    ("clock", "Clock"),
                    ("webview", "Web View"),
                    ("chart", "Chart"),
                ],
                help_text="Type of widget content",
                max_length=20,
            ),
        ),
    ]
