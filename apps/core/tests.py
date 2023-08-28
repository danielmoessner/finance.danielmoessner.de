import datetime as dt

import numpy as np
import pandas as pd
import pytz
from django.test import TestCase

import apps.core.return_calculation as rc
import apps.core.utils as utils


def get_aware_datetimes(dates):
    time = dt.time(12, 00)
    aware_dates = []
    for date in dates:
        naive_datetime = dt.datetime.combine(date, time)
        timezone = pytz.timezone("Europe/Berlin")
        aware_datetime = timezone.localize(naive_datetime)
        aware_dates.append(aware_datetime)
    return aware_dates


def get_test_empty_value_df():
    dates = []
    values = []
    aware_datetimes = get_aware_datetimes(dates)
    return pd.DataFrame({"date": aware_datetimes, "value": values}).set_index("date")


def get_test_flow_df():
    dates = [
        dt.date(2020, 1, 1),
        dt.date(2020, 1, 14),
        dt.date(2020, 1, 22),
        dt.date(2020, 2, 20),
        dt.date(2020, 2, 27),
    ]
    flows = [1000, 500, -200, -1200, -500]
    aware_datetimes = get_aware_datetimes(dates)
    return pd.DataFrame({"date": aware_datetimes, "flow": flows}).set_index("date")


def get_test_empty_flow_df():
    dates = []
    flows = []
    aware_datetimes = get_aware_datetimes(dates)
    return pd.DataFrame({"date": aware_datetimes, "flow": flows}).set_index("date")


def get_test_late_flow_df():
    dates = [dt.date(2020, 1, 1), dt.date(2020, 4, 1)]
    flows = [1000, -500]
    aware_datetimes = get_aware_datetimes(dates)
    return pd.DataFrame({"date": aware_datetimes, "flow": flows}).set_index("date")


def get_test_dates_and_values():
    dates = [
        dt.date(2020, 1, 2),
        dt.date(2020, 1, 5),
        dt.date(2020, 1, 10),
        dt.date(2020, 1, 15),
        dt.date(2020, 1, 20),
        dt.date(2020, 1, 25),
        dt.date(2020, 1, 30),
        dt.date(2020, 2, 14),
        dt.date(2020, 2, 25),
        dt.date(2020, 3, 1),
    ]
    values = [1000, 1100, 1050, 1600, 1800, 1700, 1750, 3000, 1800, 1200]
    return dates, values


def get_test_value_df():
    dates, values = get_test_dates_and_values()
    aware_datetimes = get_aware_datetimes(dates)
    return pd.DataFrame({"date": aware_datetimes, "value": values}).set_index("date")


def get_test_datetime_unaware_value_df():
    dates, values = get_test_dates_and_values()
    return pd.DataFrame({"date": dates, "value": values}).set_index("date")


def get_test_no_first_row_flow_df():
    df = get_test_flow_df()
    df = df.iloc[1:, :]
    return df


def get_test_investment_sold_flow_df():
    dates = [
        dt.date(2020, 1, 1),
        dt.date(2020, 1, 21),
    ]
    flows = [1000, -500]
    aware_datetimes = get_aware_datetimes(dates)
    return pd.DataFrame({"date": aware_datetimes, "flow": flows}).set_index("date")


def get_test_investment_sold_value_df():
    dates = [
        dt.date(2020, 1, 2),
        dt.date(2020, 1, 5),
        dt.date(2020, 1, 10),
        dt.date(2020, 1, 15),
        dt.date(2020, 1, 20),
        dt.date(2020, 1, 21),
        dt.date(2020, 1, 25),
    ]
    values = [
        1000,
        1100,
        900,
        800,
        600,
        0,
        0,
    ]
    aware_datetimes = get_aware_datetimes(dates)
    return pd.DataFrame({"date": aware_datetimes, "value": values}).set_index("date")


class ReturnCalculationTestCase(TestCase):
    def setUp(self):
        self.flow_df = get_test_flow_df()
        self.empty_flow_df = get_test_empty_flow_df()
        self.no_first_row_flow_df = get_test_no_first_row_flow_df()
        self.investment_sold_flow_df = get_test_investment_sold_flow_df()
        self.late_flow_df = get_test_late_flow_df()
        self.value_df = get_test_value_df()
        self.empty_value_df = get_test_empty_value_df()
        self.unaware_value_df = get_test_datetime_unaware_value_df()
        self.investment_sold_value_df = get_test_investment_sold_value_df()

    def test_current_return_working(self):
        current_return_df = rc.get_current_return_df(self.flow_df, self.value_df)
        current_return = rc.get_current_return(current_return_df)
        self.assertAlmostEqual(current_return, 0.7783650458069062)

    def test_invested_capital_working(self):
        current_return_df = rc.get_current_return_df(self.flow_df, self.value_df)
        invested_capital = rc.get_invested_capital(current_return_df)
        self.assertAlmostEqual(invested_capital, 674.7770953041411)

    def test_current_return_failing_with_no_values(self):
        current_return_df = rc.get_current_return_df(self.flow_df, self.empty_value_df)
        current_return = rc.get_current_return(current_return_df)
        assert current_return is None

    def test_current_return_working_with_value_first(self):
        current_return_df = rc.get_current_return_df(
            self.no_first_row_flow_df, self.value_df
        )
        rc.get_current_return(current_return_df)

    def test_current_return_failing_with_wrong_dfs(self):
        with self.assertRaisesMessage(AssertionError, ""):
            rc.get_current_return_df(self.value_df, self.flow_df)

    def test_current_return_failing_with_unaware_and_aware_datetimes(self):
        with self.assertRaisesMessage(ValueError, ""):
            rc.get_current_return_df(self.flow_df, self.unaware_value_df)

    def test_current_return_working_with_no_flows(self):
        rc.get_current_return_df(self.empty_flow_df, self.value_df)

    def test_current_return_returning_nan_with_investment_sold(self):
        curent_return_df = rc.get_current_return_df(
            self.investment_sold_flow_df, self.investment_sold_value_df
        )
        current_return = rc.get_current_return(curent_return_df)
        assert current_return is None

    def test_current_return_returning_nan_with_flow_in_last_row(self):
        current_return_df = rc.get_current_return_df(self.late_flow_df, self.value_df)
        current_return = rc.get_current_return(current_return_df)
        assert current_return is None, current_return


class NanRemovalTestCase(TestCase):
    def test_nan_removal_working(self):
        df = pd.DataFrame(
            data={
                "index": [3, 4, 5, 2, 1, 3, 4],
                "value": [np.nan, np.nan, np.nan, 1, 2, 3, np.nan],
            }
        )
        df = utils.remove_all_nans_at_beginning_and_end(df, "value")
        df.reset_index(drop=True, inplace=True)
        assert df.equals(
            pd.DataFrame(
                data={"index": [5, 2, 1, 3, 4], "value": [np.nan, 1, 2, 3, np.nan]}
            )
        )

    def test_nan_removal_not_removing_nan_in_between(self):
        df = pd.DataFrame(
            data={
                "index": [3, 4, 5, 2, 1, 3, 4],
                "value": [np.nan, np.nan, np.nan, 1, np.nan, 3, np.nan],
            }
        )
        df = utils.remove_all_nans_at_beginning_and_end(df, "value")
        df.reset_index(drop=True, inplace=True)
        assert df.equals(
            pd.DataFrame(
                data={"index": [5, 2, 1, 3, 4], "value": [np.nan, 1, np.nan, 3, np.nan]}
            )
        )

    def test_nan_removal_not_doing_anything_if_no_nans_exist(self):
        df = pd.DataFrame(data={"index": [3, 1, 4], "value": [1, 2, 3]})
        df = utils.remove_all_nans_at_beginning_and_end(df, "value")
        df.reset_index(drop=True, inplace=True)
        assert df.equals(pd.DataFrame(data={"index": [3, 1, 4], "value": [1, 2, 3]}))

    def test_nan_removal_working_with_empty_df(self):
        df = pd.DataFrame(columns=["index", "value"])
        df = utils.remove_all_nans_at_beginning_and_end(df, "value")
