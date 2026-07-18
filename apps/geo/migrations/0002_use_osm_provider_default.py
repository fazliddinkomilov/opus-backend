from django.db import migrations, models


def migrate_twogis_events_to_osm(apps, schema_editor):
    geo_provider_event = apps.get_model("geo", "GeoProviderEvent")
    geo_provider_event.objects.filter(provider="2gis").update(provider="osm")


class Migration(migrations.Migration):

    dependencies = [
        ("geo", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            migrate_twogis_events_to_osm,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="geoproviderevent",
            name="provider",
            field=models.CharField(
                choices=[("osm", "OpenStreetMap"), ("mock", "Mock")],
                default="osm",
                max_length=32,
            ),
        ),
    ]
