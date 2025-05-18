import os
from django.template.loader import get_template
from django.template import TemplateDoesNotExist


class TemplateDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        if hasattr(response, 'template_name'):
            template_names = response.template_name
            if not isinstance(template_names, (list, tuple)):
                template_names = [template_names]

            for template_name in template_names:
                try:
                    template = get_template(template_name)
                    print(f"\n[DEBUG] Rendering template: {os.path.abspath(template.origin.name)}")
                except TemplateDoesNotExist:
                    print(f"\n[ERROR] Template not found: {template_name}")

        return response