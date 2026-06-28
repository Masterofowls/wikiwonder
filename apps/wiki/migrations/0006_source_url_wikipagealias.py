"""Add source_url on WikiPage and WikiPageAlias for title matching."""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wiki", "0005_add_russian_translation_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="wikipage",
            name="source_url",
            field=models.URLField(
                blank=True,
                help_text="Original import URL (e.g. Wikipedia article)",
                max_length=2048,
            ),
        ),
        migrations.CreateModel(
            name="WikiPageAlias",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("alias", models.CharField(db_index=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "page",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="aliases",
                        to="wiki.wikipage",
                    ),
                ),
            ],
            options={
                "ordering": ["alias"],
                "indexes": [models.Index(fields=["alias"], name="wiki_wikipagealias_alias_idx")],
                "unique_together": {("page", "alias")},
            },
        ),
    ]
