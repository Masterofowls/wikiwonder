import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.mcp.server import handle_jsonrpc, list_tools


@method_decorator(csrf_exempt, name="dispatch")
class MCPView(View):
    """POST /api/mcp/ — JSON-RPC 2.0 MCP endpoint."""

    def get(self, request):
        return JsonResponse({"tools": list_tools(), "protocol": "jsonrpc-2.0"})

    def post(self, request):
        try:
            body = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        if isinstance(body, list):
            return JsonResponse([handle_jsonrpc(item) for item in body], safe=False)
        return JsonResponse(handle_jsonrpc(body))
