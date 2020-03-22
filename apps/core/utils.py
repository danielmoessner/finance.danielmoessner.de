from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.html import strip_tags
from django.utils.text import slugify
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


def create_slug(instance, on=None, slug=None):
    if slug is None:
        if on:
            slug = slugify(on)
        else:
            slug = slugify(instance.name)

    instance_class = instance.__class__
    qs = instance_class.objects.filter(slug=slug).order_by("-pk")
    if qs.exists():
        new_slug = "%s-%s" % (slug, qs.first().pk)
        return create_slug(instance=instance, on=on, slug=new_slug)
    return slug


def form_invalid_universal(view, form, errors_name, heading="Something went wrong.", **kwargs):
    context = view.get_context_data(**kwargs)
    context[errors_name] = [heading, ]
    for field in form:
        context[errors_name].append(
            strip_tags(field.errors).replace(".", ". ").replace("  ", " ")
        )
    while "" in context[errors_name]:
        context[errors_name].remove("")
    return view.render_to_response(context)


def errors_to_view(view, errors_heading="Something went wrong.", errors=()):
    errors = list(errors)
    errors.insert(0, errors_heading)
    context = view.get_context_data()
    context["errors"] = errors
    return view.render_to_response(context)


def create_paginator(page_get_param, objects, pages):
    paginator = Paginator(objects, pages)
    success = False
    try:
        objects = paginator.page(page_get_param)
        success = True
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        objects = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        if int(page_get_param) < 1:
            objects = paginator.page(paginator.num_pages)
        else:
            objects = paginator.page(1)
        success = True
    return objects, success
