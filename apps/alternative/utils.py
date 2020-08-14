###
# General
###
def get_closest_value_or_flow(flow_qs, value_qs, date, direction='previous'):
    """
    Return the closest value or flow. If a flow is closer it
    returns the flow. If a value is closer it returns the value.
    direction: previous | next
    """
    if direction == 'next':
        flow = flow_qs.filter(date__gte=date).order_by("date").first()
        value = value_qs.filter(date__gte=date).order_by("date").first()
    elif direction == 'previous':
        flow = flow_qs.filter(date__lte=date).order_by("-date").first()
        value = value_qs.filter(date__lte=date).order_by("-date").first()
    else:
        return None

    if flow and value:
        return flow if abs(flow.date - date) < abs(value.date - date) else value
    elif flow or value:
        return flow or value
    else:
        return None
