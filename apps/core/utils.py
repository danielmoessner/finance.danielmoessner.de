from datetime import timedelta


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
