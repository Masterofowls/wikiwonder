from django.http import HttpResponse
from django.views import View

from apps.seo.services import robots_txt_content


class RobotsTxtView(View):
    def get(self, request):
        return HttpResponse(robots_txt_content(), content_type="text/plain")
