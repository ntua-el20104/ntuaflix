# my_custom_filters.py
from django import template

register = template.Library()

@register.filter(name='replace')
def replace(value, args):
    search_str, replace_str = args.split(',')
    return value.replace(search_str, replace_str)
