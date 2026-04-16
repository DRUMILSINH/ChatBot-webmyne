from django.db import migrations


def backfill_runtime_tables_on_default(apps, schema_editor):
    if schema_editor.connection.alias != "default":
        return

    existing_tables = set(schema_editor.connection.introspection.table_names())
    model_order = [
        "ChatSession",
        "AuditLog",
        "CrawlJob",
        "ChatMessage",
        "MessageFeedback",
    ]

    for model_name in model_order:
        model = apps.get_model("chat", model_name)
        table_name = model._meta.db_table
        if table_name in existing_tables:
            continue
        schema_editor.create_model(model)
        existing_tables.add(table_name)


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0004_production_upgrade"),
    ]

    operations = [
        migrations.RunPython(backfill_runtime_tables_on_default, migrations.RunPython.noop),
    ]
