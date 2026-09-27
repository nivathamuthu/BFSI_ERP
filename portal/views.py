from django.views.generic import TemplateView


class PortalView(TemplateView):
    template_name = "portal/index.html"
