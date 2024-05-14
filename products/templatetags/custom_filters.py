from django import template

register = template.Library()

@register.filter
def add_commas(value):
    """
    Adds commas to an integer.
    """
    try:
        # Convert the value to an integer
        value = int(value)
        # Format the integer value with commas
        return '{:,}'.format(value)
    except (ValueError, TypeError):
        return value
