# Django library
from django.forms import RadioSelect


# create your widgets

path='/Users/jurgen/UniApps/uniwork/venv/lib/python3.9/site-packages/django/forms/templates/widgets/radiobuttongroup.html'


class RadioSelectButtonGroup(RadioSelect):
    """
    This widget renders a Bootstrap 4 set of buttons horizontally instead of typical radio buttons.
    """

    template_name = 'widgets/radiobuttongroup.html'
