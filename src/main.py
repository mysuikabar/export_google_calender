from datetime import datetime
from pathlib import Path
import click
import yaml
from export_calender import GoogleCalenderExporter


@click.command()
@click.option("--year", type=int, default=datetime.now().year)
@click.option("--month", type=int, default=datetime.now().month)
def main(year, month):
    with open(Path(__file__).parent / "conf/config.yaml") as f:
        config = yaml.load(f, Loader=yaml.Loader)

    calender_id = config["calender_id"]
    event_categories = config["event_categories"]

    exporter = GoogleCalenderExporter(
        year=year,
        month=month,
        event_categories=event_categories,
        calender_id=calender_id,
    )
    formatted_events_df = exporter.export_formatted_events_dataframe()
    events_without_category_df = exporter.export_events_without_category_dataframe()

    formatted_events_df.write_csv(Path(__file__).parent / "output/formatted_events.csv")
    events_without_category_df.write_csv(
        Path(__file__).parent / "output/events_without_category.csv"
    )


if __name__ == "__main__":
    main()
