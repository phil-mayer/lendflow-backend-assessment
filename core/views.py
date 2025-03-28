from django.http import JsonResponse
from django.views import View


class BestSellersView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"message": "Unauthorized"}, status=401)

        return JsonResponse([])
