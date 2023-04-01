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
    df = exporter.export_formatted_events_dataframe()
    df.write_csv(Path(__file__).parent / "output/formatted_event_dataframe.csv")


if __name__ == "__main__":
    main()
