from datetime import date
from typing import Union

import numpy as np
import pandas as pd


#############
# standard dfs
#############
def _get_merged_flow_and_value_df(
    flow_df: pd.DataFrame | None, value_df: pd.DataFrame | None
) -> Union[pd.DataFrame, None]:
    # no calculations are possible if on of the dfs is none
    if value_df is None or flow_df is None or value_df.empty or flow_df.empty:
        return None
    # test that the first df has a flow column and the second a value column
    assert "flow" in flow_df.columns and "value" in value_df.columns
    # merge the dfs and sort by date
    df = flow_df.merge(value_df, how="outer", sort=True, on="date")
    # stop calculation if there is not a flow in the first row
    first_flow_cell = df.iloc[0, df.columns.get_loc("flow")]
    assert (
        type(first_flow_cell) == np.float64 or type(first_flow_cell) == np.int64
    ), type(first_flow_cell)
    if np.isnan(first_flow_cell):
        return None
    # stop calculations if there is no value in the last row
    last_value_cell = df.iloc[-1, df.columns.get_loc("value")]
    assert isinstance(last_value_cell, (np.float64, np.int64))  # pyright: ignore
    if np.isnan(last_value_cell):
        return None
    # return the new df
    return df


def get_value_with_flow_df(
    flow_df: pd.DataFrame | None, value_df: pd.DataFrame | None
) -> Union[pd.DataFrame, None]:
    # get the right df
    df = _get_merged_flow_and_value_df(flow_df, value_df)
    # stop calculations if something went wrong beforehand
    if df is None or df.empty:
        return None
    # fill the nan values next to the flows with values
    # that make sense based on the time
    # best case scenario: this does nothing;
    # worst case: it fills most of the values
    df.loc[:, "value"] = df.loc[:, "value"].interpolate(
        method="time", limit_direction="both"
    )
    # fill the nan flow with 0
    df.loc[:, "flow"].fillna(0, inplace=True)
    # return the combined df
    return df


#############
# current return
#############
def get_current_return_df(
    flow_df: pd.DataFrame | None, value_df: pd.DataFrame | None
) -> Union[pd.DataFrame, None]:
    if flow_df is None or value_df is None:
        return None
    # get the right df
    df = get_value_with_flow_df(flow_df, value_df)
    # stop calculations if something went wrong beforehand
    if df is None or df.empty:
        return None
    # new check to see if there are still datetimes used instead of dates
    assert isinstance(flow_df.index[0], date) and isinstance(value_df.index[0], date)
    # copy the first value to the flow column if there is no flow
    # if df.iloc[0, df.columns.get_loc("flow")] == 0:
    #     df.iloc[0, df.columns.get_loc("flow")] = df.iloc[0, df.columns.get_loc("value")]
    # init the invested_capital column
    df.loc[:, "invested_capital"] = None
    # calculate the invested capital
    for i in range(0, df.shape[0]):
        flow = df.iloc[i, df.columns.get_loc("flow")]
        previous_invested_capital = (
            df.iloc[i - 1, df.columns.get_loc("invested_capital")] if i > 0 else 0
        )
        assert type(flow) == np.float64 or type(flow) == np.int64, type(flow)
        if flow > 0:
            invested_capital = previous_invested_capital + flow
        elif flow < 0:
            value = df.iloc[i, df.columns.get_loc("value")]
            invested_capital = previous_invested_capital * (value / (abs(flow) + value))
        else:
            invested_capital = previous_invested_capital
        df.iloc[i, df.columns.get_loc("invested_capital")] = invested_capital
    # calculate the current return
    df.loc[:, "invested_capital"] = df.loc[:, "invested_capital"].apply(
        pd.to_numeric, downcast="float"
    )
    # df.loc[:, "invested_capital"] = df.loc[:, "invested_capital"].replace(0, np.nan)
    df.loc[:, "current_return"] = df.loc[:, "value"] / df.loc[
        :, "invested_capital"
    ].replace(0, np.nan)
    # return the df
    return df


def get_current_return(df):
    # return None if something went wrong before
    if df is None or df.empty:
        return None
    # test that all necessary columns are available
    assert "current_return" in df.columns
    # current return of a period is always the last value
    current_return = df.iloc[-1, df.columns.get_loc("current_return")]
    # adjust to represent a percentage value
    current_return -= 1
    # safety stuff to make sure the db can save it
    if abs(current_return) == np.inf or np.isnan(current_return):
        current_return = None
    # return the current return
    return current_return


def get_invested_capital(df):
    # return None if something went wrong before
    if df is None or df.empty:
        return None
    # test that all necessary columns are available
    assert "invested_capital" in df.columns
    # invested capital is always the last value
    invested_capital = df.iloc[-1, df.columns.get_loc("invested_capital")]
    # safety stuff to make sure the db can save it
    if abs(invested_capital) == np.inf or np.isnan(invested_capital):
        invested_capital = None
    # return the invested capital
    return invested_capital
