from datetime import datetime, timezone
from pathlib import Path

import polars as pl
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


class GoogleCalenderExporter:
    """
    指定された年月のGoogleカレンダーの情報を取得し、適当な形式のデータフレームに成形して出力するクラス
    """

    def __init__(
        self,
        year: int,
        month: int,
        event_categories: dict[str, list],
        *,
        calender_id: str,
    ) -> None:
        self.year = year
        self.month = month
        self.event_categories = event_categories
        self.cacalender_id = calender_id

    @property
    def start_month(self) -> datetime:
        return datetime(self.year, self.month, 1, tzinfo=timezone.utc)

    @property
    def end_month(self) -> datetime:
        if self.month != 12:
            year, month = self.year, self.month + 1
        else:
            year, month = self.year + 1, 1
        return datetime(year, month, 1, tzinfo=timezone.utc)

    def event_categories_df(self) -> pl.DataFrame:
        """
        イベントとカテゴリーを対応させた辞書をデータフレームの形に整形する
        """
        df = pl.DataFrame(schema={"event": pl.Utf8, "category": pl.Utf8})

        for category, events in self.event_categories.items():
            for event in events:
                tmp = pl.DataFrame({"event": event, "category": category})
                df = df.vstack(tmp)

        return df

    def get_calender_events(self) -> list:
        """
        指定された年月のカレンダーの情報を取得する
        """
        credentials = Credentials.from_service_account_file(
            Path(__file__).parent / "conf/credentials.json",
            scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        )
        service = build("calendar", "v3", credentials=credentials)

        # カレンダーのイベントを取得
        events_result = (
            service.events()
            .list(
                calendarId=self.cacalender_id,
                timeMin=self.start_month.isoformat(),
                timeMax=self.end_month.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        return events

    def export_events_dataframe(self) -> pl.DataFrame:
        """
        各イベントに対し、対応するカテゴリとその所要時間をまとめたデータフレームを出力する
        """
        events = self.get_calender_events()
        df = pl.DataFrame(
            schema={"date": pl.Date, "duration": pl.Duration, "event": pl.Utf8}
        )

        # イベントごとの所要時間をdf_eventにまとめる
        for event in events:
            start_time = event["start"].get("dateTime", event["start"].get("date"))
            end_time = event["end"].get("dateTime", event["end"].get("date"))
            start_datetime = datetime.fromisoformat(start_time)
            end_datetime = datetime.fromisoformat(end_time)
            tmp = pl.DataFrame(
                {
                    "date": start_datetime.date(),
                    "duration": end_datetime - start_datetime,
                    "event": event.get("summary", "No title"),
                }
            )
            df = df.vstack(tmp)

        # 各イベントに対応するカテゴリを紐づける
        event_categories_df = self.event_categories_df()
        df = df.join(event_categories_df, on="event", how="left").with_columns(
            pl.col("category").fill_null("others")
        )

        return df

    def export_formatted_events_dataframe(self) -> pl.DataFrame:
        """
        各カテゴリごとに対応するイベントの所要時間の合計を日単位でまとめたデータフレームを出力する
        """
        date_index = pl.DataFrame(
            {
                "date": pl.date_range(
                    low=self.start_month.date(),
                    high=self.end_month.date(),
                    interval="1d",
                    closed="left",
                )
            }
        )
        df = self.export_events_dataframe()

        # 各カテゴリごとの所要時間の合計を日単位でまとめたデータフレームに成形
        df = (
            df.groupby("date", "category")
            .agg(pl.col("duration").sum())
            .with_columns(
                (pl.col("duration") + pl.lit(datetime(2000, 1, 1))).dt.strftime("%H:%M")
            )  # pl.Durationではフォーマットできないのでpl.Datetimeに直す
            .pivot(values="duration", index="date", columns="category")
            .join(date_index, on="date", how="outer")
            .sort("date")
        )

        return df

    def export_events_without_category_dataframe(self):
        """
        カテゴリが紐づかなかったイベントに対して、各イベントとその所要時間をまとめたデータフレームを出力する
        """
        df = self.export_events_dataframe()
        df = df.filter(pl.col("category") == "others").select(
            pl.col("date"),
            pl.col("event"),
            (pl.col("duration") + pl.lit(datetime(2000, 1, 1))).dt.strftime(
                "%H:%M"
            ),  # pl.Durationではフォーマットできないのでpl.Datetimeに直す
        )
        return df
