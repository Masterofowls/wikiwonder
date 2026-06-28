"""Add Russian modeltranslation fields (en + ru only)."""
import markdownx.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wiki", "0004_edit_suggestion"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="description_ru",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="category",
            name="name_ru",
            field=models.CharField(max_length=120, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="wikipage",
            name="content_ru",
            field=markdownx.models.MarkdownxField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="wikipage",
            name="summary_ru",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="wikipage",
            name="title_ru",
            field=models.CharField(max_length=255, null=True, db_index=True),
        ),
        migrations.AddField(
            model_name="wikisection",
            name="content_ru",
            field=markdownx.models.MarkdownxField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="wikisection",
            name="title_ru",
            field=models.CharField(max_length=255, null=True),
        ),
    ]
