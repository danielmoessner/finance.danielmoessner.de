from datetime import timedelta
import pandas as pd


def remove_all_nans_at_beginning_and_end(df, column):
    # get the index of the first non nan value
    first_idx = df.loc[:, column].first_valid_index()
    # get the row number of the index
    if first_idx:
        first_idx = df.index.get_loc(first_idx)
    # slice the df
    if first_idx and first_idx >= 1:
        df = df.iloc[first_idx - 1:]
    # get the index of the last non nan value
    last_idx = df.loc[:, column].last_valid_index()
    # get the row number of the index
    if last_idx:
        last_idx = df.index.get_loc(last_idx)
    # slice the df
    if last_idx and last_idx + 2 < len(df):
        df = df.iloc[:last_idx + 2]
    # return the df
    return df


def get_merged_value_df_from_queryset(queryset):
    # instantiate a new dataframe
    df = pd.DataFrame(columns=['date', 'value'])
    df.set_index('date', inplace=True)
    # merge the dataframe with all items
    for item in list(queryset):
        item_df = item.get_value_df()
        if item_df is None:
            continue
        item_df.rename(columns={'value': 'value__' + str(item.pk)}, inplace=True)
        df = df.merge(item_df, how='outer', sort=True, on='date')
    # return the df
    return df


def sum_up_columns_in_a_dataframe(df, column='value'):
    # return none if the df is empty
    if df.empty:
        return None
    # get all the value columns as list
    value_columns = df.columns.str.contains(column + '__')
    # sum the alternative values in the value column
    df.loc[:, column] = df.iloc[:, value_columns].sum(axis=1)
    # drop all unnecessary columns
    df = df.loc[:, [column]]
    # return the new df
    return df


def turn_dict_of_dicts_into_list_of_dicts(dict_of_dicts, name_of_key):
    list_of_dicts = []
    for key_to_inside_dict, inside_dict in dict_of_dicts.items():
        inside_dict.update({name_of_key: key_to_inside_dict})
        list_of_dicts.append(inside_dict)
    return list_of_dicts


def change_time_of_date_index_in_df(df, hours):
    assert 0 <= hours <= 24
    if not df.empty:
        df.index = df.index.normalize() + timedelta(hours=hours)
    return df


def round_value_if_exists(value, places=2):
    if value is not None:
        return round(value, places)
    return None
