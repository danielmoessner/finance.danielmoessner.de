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
    # merge the dataframe with all alternatives
    for item in list(queryset):
        item_df = item.get_value_df()
        if item_df is None:
            break
        item_df.rename(columns={'value': 'value__' + str(item.pk)}, inplace=True)
        df = df.merge(item_df, how='outer')
    # return the df
    return df


def sum_up_all_value_columns_in_a_dataframe(df):
    # return none if the df is empty
    if df.empty:
        return None
    # set the date as index and sort the df as preparation for the interpolate method
    df.set_index('date', inplace=True)
    df.sort_index(inplace=True)
    # interpolate the alternative value columns based on the time
    value_columns = df.columns.str.contains('value__')
    df.iloc[:, value_columns] = df.iloc[:, value_columns].interpolate(method='time', limit_direction='forward')
    # sum the alternative values in the value column
    df.loc[:, 'value'] = df.iloc[:, value_columns].sum(axis=1)
    # drop all unnecessary columns
    df = df.loc[:, ['value']]
    # set the index as column
    df.reset_index(inplace=True)
    # return the new df
    return df


def turn_dict_of_dicts_into_list_of_dicts(dict_of_dicts, name_of_key):
    list_of_dicts = []
    for key_to_inside_dict, inside_dict in dict_of_dicts.items():
        inside_dict.update({name_of_key: key_to_inside_dict})
        list_of_dicts.append(inside_dict)
    return list_of_dicts


def change_time_of_date_column_in_df(df, hours):
    assert 0 <= hours <= 24
    if not df.empty:
        df.loc[:, 'date'] = df.loc[:, 'date'].dt.normalize() + timedelta(hours=hours)
    return df


def round_value_if_exists(value, places=2):
    if value is not None:
        return round(value, places)
    return None
