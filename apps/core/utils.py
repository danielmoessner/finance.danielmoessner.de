from datetime import timedelta
from typing import Union

import numpy as np
import pandas as pd
from django.db import connection

pd.set_option("future.no_silent_downcasting", True)


###
# DataFrame Utils
###
def remove_all_nans_at_beginning_and_end(df, column):
    # get the index of the first non nan value
    first_idx = df.loc[:, column].first_valid_index()
    # get the row number of the index
    if first_idx:
        first_idx = df.index.get_loc(first_idx)
    # slice the df
    if first_idx and first_idx >= 1:
        df = df.iloc[first_idx - 1 :]
    # get the index of the last non nan value
    last_idx = df.loc[:, column].last_valid_index()
    # get the row number of the index
    if last_idx:
        last_idx = df.index.get_loc(last_idx)
    # slice the df
    if last_idx and last_idx + 2 < len(df):
        df = df.iloc[: last_idx + 2]
    # return the df
    return df


def get_merged_value_df_from_queryset(queryset, column="value"):
    # instantiate a new dataframe
    df = pd.DataFrame(columns=["date", "value"])
    df.set_index("date", inplace=True)
    # merge the dataframe with all items
    for index, item in enumerate(list(queryset)):
        item_df = item.get_value_df()
        if item_df is None:
            continue
        item_df.rename(
            columns={column: "value__{}-{}".format(index, item.pk)}, inplace=True
        )
        df = df.merge(item_df, how="outer", sort=True, on="date")
    # return the df
    return df


def sum_up_value_dfs_from_items(items, column="value"):
    # get the df with all values
    df = get_merged_value_df_from_queryset(items, column=column)
    # fill na values for sum to work correctly
    df = df.ffill().fillna(0)
    # sums up all the values of the assets and interpolates
    df = sum_up_columns_in_a_dataframe(df)
    # remove all the rows where the value is 0 as it doesn't
    # make sense in the calculations
    if df is None:
        return None
    df = df.loc[df.loc[:, column] != 0]
    # return the df
    return df


def create_value_df_from_amount_and_price(item) -> pd.DataFrame | None:
    price_df = item.get_price_df()
    amount_df = item.get_amount_df()
    # return none if there is nothing to be calculated
    if price_df is None or amount_df is None or price_df.empty or amount_df.empty:
        return None
    # merge dfs into on df
    df = pd.merge(price_df, amount_df, on="date", how="outer", sort=True)
    # set the date column to a daily frequency
    idx = pd.date_range(start=df.index[0], end=df.index[-1], freq="D")
    df = df.reindex(idx, fill_value=np.nan)
    df.index.rename("date", inplace=True)
    # forward fill the amount
    df.loc[:, "amount"] = df.loc[:, "amount"].ffill()
    # interpolate the price
    df.loc[:, "price"] = df.loc[:, "price"].interpolate(
        method="time", limit_direction="both"
    )
    # calculate the value
    df.loc[:, "value"] = df.loc[:, "amount"] * df.loc[:, "price"]
    # remove unnecessary columns
    df = df.loc[:, ["value"]]
    # return the df
    return df


def sum_up_columns_in_a_dataframe(
    df, column="value", drop=True
) -> Union[pd.DataFrame, None]:
    # return none if the df is empty
    if df.empty:
        return None
    # safety check sum probably returns wrong values if that's the case
    if df.isnull().values.any():
        raise ValueError("The df should not contain nan values.")
    # get all the value columns as list
    value_columns = df.columns.str.contains(column + "__")
    # sum the alternative values in the value column
    df.loc[:, column] = df.iloc[:, value_columns].sum(axis=1)
    # drop all unnecessary columns
    if drop:
        df = df.loc[:, [column]]
    # return the new df
    return df


def change_time_of_date_index_in_df(df, hours):
    assert 0 <= hours <= 24
    if not df.empty:
        df.index = df.index.normalize() + timedelta(hours=hours)
        df = df.tz_localize(None)
    return df


def remove_time_of_date_index_in_df(df) -> pd.DataFrame:
    if not df.empty:
        df.index = df.index.normalize()
        df = df.tz_localize(None)
    return df


###
# Python Utils
###
def turn_dict_of_dicts_into_list_of_dicts(dict_of_dicts, name_of_key):
    list_of_dicts = []
    for key_to_inside_dict, inside_dict in dict_of_dicts.items():
        inside_dict.update({name_of_key: key_to_inside_dict})
        list_of_dicts.append(inside_dict)
    return list_of_dicts


###
# Database Utils
###
def get_df_from_database(statement: str, columns: list[str]) -> pd.DataFrame:
    cursor = connection.cursor()
    cursor.execute(statement)
    data = cursor.fetchall()
    df = pd.DataFrame(data=data, columns=columns)
    df.loc[:, "date"] = pd.to_datetime(df.loc[:, "date"])
    df.set_index("date", inplace=True)
    return df


def get_number_from_database(statement: str):
    cursor = connection.cursor()
    cursor.execute(statement)
    data = cursor.fetchall()
    # if there is not a single number returned just fallback to none
    if len(data) != 1 or len(data[0]) != 1:
        return None
    data = data[0][0]
    return data


###
# Django Queryset Utils
###
def get_closest_object_in_two_querysets(qs1, qs2, date, direction="previous"):
    """
    Return the closest object of two querysets. If a
    object in qs1 is closer it
    returns the object from qs1. If a object in qs2
    is closer it returns the object from qs2.
    direction: previous | next
    """
    if direction == "next":
        object_from_qs_1 = qs1.filter(date__gte=date).order_by("date").first()
        object_from_qs_2 = qs2.filter(date__gte=date).order_by("date").first()
    elif direction == "previous":
        object_from_qs_1 = qs1.filter(date__lte=date).order_by("-date").first()
        object_from_qs_2 = qs2.filter(date__lte=date).order_by("-date").first()
    else:
        return None

    if object_from_qs_1 and object_from_qs_2:
        if abs(object_from_qs_1.date - date) < abs(object_from_qs_2.date - date):
            return object_from_qs_1
        else:
            return object_from_qs_2
    elif object_from_qs_1 or object_from_qs_2:
        return object_from_qs_1 or object_from_qs_2
    else:
        return None
