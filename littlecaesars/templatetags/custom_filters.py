# littlecaesars/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Allows accessing dictionary items with a variable key in templates"""
    return dictionary.get(key)

# Optional: Filter to check if a value is in a list/queryset (used for checkboxes)
@register.filter(name='in')
def value_in(value, container):
    if value is None:
        return False
    try:
        # Convert value to string if comparing against string list from form values
        return str(value) in [str(item) for item in container]
    except TypeError:
        return False