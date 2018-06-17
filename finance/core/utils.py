from django.utils.html import strip_tags
from django.utils.text import slugify

from django.conf import settings


def print_df(df):
    if settings.DEBUG:
        import tabulate
        table = tabulate.tabulate(df, headers="keys")
        print(table)


def create_slug(instance, slug=None):
    if slug is None:
        slug = slugify(instance.name)

    instance_class = instance.__class__
    qs = instance_class.objects.filter(slug=slug).order_by("-pk")
    if qs.exists():
        new_slug = "%s-%s" % (slug, qs.first().pk)
        return create_slug(instance=instance, slug=new_slug)
    return slug


def create_slug_on_username(instance, slug=None):
    if slug is None:
        slug = slugify(instance.username)

    instance_class = instance.__class__
    qs = instance_class.objects.filter(slug=slug).order_by("-pk")
    if qs.exists():
        new_slug = "%s-%s" % (slug, qs.first().pk)
        return create_slug(instance=instance, slug=new_slug)
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
