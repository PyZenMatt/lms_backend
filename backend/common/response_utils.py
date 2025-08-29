from typing import Any, Dict, Optional
from django.http import JsonResponse


def ok(data: Optional[Dict[str, Any]] = None, message: Optional[str] = None) -> JsonResponse:
    payload: Dict[str, Any] = {"status": "ok"}
    if data:
        payload.update(data)
    if message:
        payload["message"] = message
    return JsonResponse(payload, status=200)


def err(code: str, message: str, http_status: int = 400) -> JsonResponse:
    payload = {"status": "error", "error_code": code, "message": message}
    return JsonResponse(payload, status=http_status)
