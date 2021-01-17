# Django library
from django.forms import RadioSelect


# create your widgets


class RadioSelectButtonGroup(RadioSelect):
    """
    This widget renders a Bootstrap 5 set of buttons horizontally instead of typical radio buttons.
    """

    template_name = 'widgets/radiobuttongroup.html'
