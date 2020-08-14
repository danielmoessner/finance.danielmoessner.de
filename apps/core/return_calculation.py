from scipy.optimize import newton
import pandas as pd
import numpy as np


#############
# standard dfs
#############
def _get_merged_flow_and_value_df(flow_df, value_df):
    # no calculations are possible if on of the dfs is none
    if value_df is None or flow_df is None or value_df.empty or flow_df.empty:
        return None
    # test that the first df has a flow column and the second a value column
    assert 'flow' in flow_df.columns and 'value' in value_df.columns
    # merge the dfs and sort by date
    df = flow_df.merge(value_df, how='outer', sort=True, on='date')
    # stop calculation if there is not a flow in the first row
    if np.isnan(df.iloc[0, df.columns.get_loc('flow')]):
        return None
    # stop calculations if there is no value in the last row
    if np.isnan(df.iloc[-1, df.columns.get_loc('value')]):
        return None
    # return the new df
    return df


def get_value_with_flow_df(flow_df, value_df):
    # get the right df
    df = _get_merged_flow_and_value_df(flow_df, value_df)
    # stop calculations if something went wrong beforehand
    if df is None or df.empty:
        return None
    # fill the nan values next to the flows with values that make sense based on the time
    # best case scenario: this does nothing; worst case: it fills most of the values
    df.loc[:, 'value'] = df.loc[:, 'value'].interpolate(method='time', limit_direction='both')
    # fill the nan flow with 0
    df.loc[:, 'flow'].fillna(0, inplace=True)
    # return the combined df
    return df


#############
# time weighted return
#############
def get_time_weighted_return_df(flow_df, value_df):
    # get the right df
    df = get_value_with_flow_df(flow_df, value_df)
    # stop calculations if something went wrong beforehand
    if df is None or df.empty:
        return None
    # calculate twr for each sub period
    df.loc[:, 'twr'] = (df.loc[:, 'value'] - df.loc[:, 'flow']) / df.loc[:, 'value'].shift(1)
    # fill the first row twr value as it is nan
    df.iloc[0, df.columns.get_loc('twr')] = 1
    # return the df
    return df


def get_time_weighted_return(df):
    # return None if something went wrong beforehand
    if df is None or df.empty:
        return None
    # test that all necessary columns are available
    assert 'twr' in df.columns
    # return nan if there are nan values in the twr column
    if df.loc[:, 'twr'].isnull().values.any():
        return None
    # calculate twr
    time_weighted_return = df.loc[:, 'twr'].product() - 1
    # safety stuff to make sure the db can save it
    if abs(time_weighted_return) == np.inf or np.isnan(time_weighted_return):
        time_weighted_return = None
    # return the rate
    return time_weighted_return


#############
# internal rate of return
#############
def get_internal_rate_of_return_df(flow_df, value_df):
    # get the right df
    df = _get_merged_flow_and_value_df(flow_df, value_df)
    # stop calculations if something went wrong beforehand
    if df is None or df.empty:
        return None
    # move the first value to the flow column if there is no flow
    if np.isnan(df.iloc[0, df.columns.get_loc('flow')]):
        df.iloc[0, df.columns.get_loc('flow')] = df.iloc[0, df.columns.get_loc('value')]
    # flip the flows
    df.loc[:, 'flow'] = df.loc[:, 'flow'] * (-1)
    # get the last value as flow
    df.iloc[-1, df.columns.get_loc('flow')] = df.iloc[-1, df.columns.get_loc('value')]
    # drop the nan rows
    df = df.loc[df.loc[:, 'flow'].notna()]
    # test that the length is equal to the length of the flow df plus the last row of the value df
    assert len(df.index) == len(flow_df.index) + 1 or len(df.index) == len(flow_df.index) + 2
    # drop the value column
    df = df.loc[:, ['flow']]
    # add the days column
    df.loc[:, 'days'] = df.index - df.index[0]
    # convert the days column to a number in days
    df.loc[:, 'days'] = df.loc[:, 'days'].map(lambda x: x.days)
    # return the df
    return df


def _custom_xnpv(rate, df):
    # test that all necessary columns are available
    assert 'flow' in df.columns and 'days' in df.columns
    # calculation
    xnpv = 0
    for i in range(0, df.shape[0]):
        xnpv += df.iloc[i, df.columns.get_loc('flow')] / (1 + rate) ** df.iloc[i, df.columns.get_loc('days')]
    # return the
    return xnpv


def _get_daily_internal_rate_of_return(df, guess=0.000210874):
    # test that all necessary columns are available
    assert 'flow' in df.columns and 'days' in df.columns
    # return nan if the last flow is 0 because that means that there is no money invested anymore
    if df.iloc[-1, df.columns.get_loc('flow')] == 0:
        return np.nan
    # calculate the internal rate of return
    try:
        internal_rate_of_return = newton(lambda rate: _custom_xnpv(rate, df), guess)
    except RuntimeError:
        internal_rate_of_return = None
    # return the rate
    return internal_rate_of_return


def get_internal_rate_of_return(df):
    # stop calculations if something went wrong beforehand
    if df is None or df.empty:
        return None
    # get the daily rate
    internal_rate_of_return = _get_daily_internal_rate_of_return(df)
    # return none if no rate was found
    if internal_rate_of_return is None:
        return None
    # turn the daily rate into the rate of the period
    internal_rate_of_return = (1 + internal_rate_of_return) ** (df.iloc[-1, df.columns.get_loc('days')])
    # adjust to represent a percentage value
    internal_rate_of_return -= 1
    # safety stuff to make sure the db can save it
    if abs(internal_rate_of_return) == np.inf or np.isnan(internal_rate_of_return):
        internal_rate_of_return = None
    # return the rate
    return internal_rate_of_return


#############
# current return
#############
def get_current_return_df(flow_df, value_df):
    # get the right df
    df = get_value_with_flow_df(flow_df, value_df)
    # stop calculations if something went wrong beforehand
    if df is None or df.empty:
        return None
    # copy the first value to the flow column if there is no flow
    if df.iloc[0, df.columns.get_loc('flow')] == 0:
        df.iloc[0, df.columns.get_loc('flow')] = df.iloc[0, df.columns.get_loc('value')]
    # init the invested_capital column
    df.loc[:, 'invested_capital'] = None
    # calculate the invested capital
    for i in range(0, df.shape[0]):
        flow = df.iloc[i, df.columns.get_loc('flow')]
        previous_invested_capital = df.iloc[i - 1, df.columns.get_loc('invested_capital')] if i > 0 else 0
        if flow > 0:
            invested_capital = previous_invested_capital + flow
        elif flow < 0:
            value = df.iloc[i, df.columns.get_loc('value')]
            invested_capital = previous_invested_capital * (value / (abs(flow) + value))
        else:
            invested_capital = previous_invested_capital
        df.iloc[i, df.columns.get_loc('invested_capital')] = invested_capital
    # calculate the current return
    df.loc[:, 'invested_capital'] = df.loc[:, 'invested_capital'].apply(pd.to_numeric, downcast='float')
    df.loc[:, 'current_return'] = df.loc[:, 'value'] / df.loc[:, 'invested_capital']
    # return the df
    return df


def get_current_return(df):
    # return None if something went wrong before
    if df is None or df.empty:
        return None
    # test that all necessary columns are available
    assert 'current_return' in df.columns
    # current return of a period is always the last value
    current_return = df.iloc[-1, df.columns.get_loc('current_return')]
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
    assert 'invested_capital' in df.columns
    # invested capital is always the last value
    invested_capital = df.iloc[-1, df.columns.get_loc('invested_capital')]
    # safety stuff to make sure the db can save it
    if abs(invested_capital) == np.inf or np.isnan(invested_capital):
        invested_capital = None
    # return the invested capital
    return invested_capital
