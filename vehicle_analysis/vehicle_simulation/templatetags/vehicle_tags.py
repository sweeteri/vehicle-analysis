from django import template
from vehicles.models import ICEVehicle, EVVehicle, HEVVehicle, PHEVVehicle

register = template.Library()


@register.filter
def isinstance(value, class_str):
    if class_str == "ICEVehicle":
        return isinstance(value, ICEVehicle)
    elif class_str == "EVVehicle":
        return isinstance(value, EVVehicle)
    elif class_str == "HEVVehicle":
        return isinstance(value, HEVVehicle)
    elif class_str == "PHEVVehicle":
        return isinstance(value, PHEVVehicle)
    return False
