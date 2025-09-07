from core.admin_views import custom_admin_logout
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rewards.views.discount_views import (
    pending_discount_snapshots,
    accept_teacher_choice,
    decline_teacher_choice,
)

from drf_spectacular.views import (
     SpectacularAPIView,
     SpectacularRedocView,
     SpectacularSwaggerView,
)

# drf-yasg Swagger
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from blockchain.views_simplified import wallet_withdraw
from blockchain.views_simplified import onchain_mint


schema_view = get_schema_view(
    openapi.Info(
        title="API Docs",
        default_version='v1',
        description="Documentazione delle API",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Health check endpoint
from django.http import HttpResponse
import os
from pathlib import Path

def version(request):
    # Return the app version: prefer GIT_COMMIT env, fallback to a lightweight file or package
    git_commit = os.getenv("GIT_COMMIT")
    if git_commit:
        return HttpResponse(git_commit, content_type="text/plain")
    # Fallback to reading a VERSION file if present
    try:
        base = Path(__file__).resolve().parent.parent
        version_file = base / "VERSION"
        if version_file.exists():
            return HttpResponse(version_file.read_text().strip(), content_type="text/plain")
    except Exception:
        pass
    return HttpResponse("unknown", content_type="text/plain")

def healthz(_):
    return HttpResponse("ok", content_type="text/plain")

urlpatterns = [
    path("admin/logout/", custom_admin_logout, name="admin_logout"),
    path("admin/", admin.site.urls),
    path("api/v1/", include("core.urls")),
    path("api/v1/", include("courses.urls")),
    path("api/v1/", include("authentication.urls")),
    path("api/v1/", include("users.urls")),
    path("api/v1/", include("rewards.urls")),
    path("api/v1/", include("notifications.urls")),
    path("api/v1/blockchain/", include("blockchain.urls")),
    # Compatibility alias for on-chain mint endpoint used by frontend
    path("api/v1/onchain/mint/", onchain_mint, name="onchain_mint_alias"),
    # Compatibility alias for wallet withdraw (DB->chain)
    path("api/v1/wallet/withdraw/", wallet_withdraw, name="wallet_withdraw_alias"),
    path("api/v1/services/", include("services.urls")),
    path("api/v1/teocoin/", include("api.teocoin_urls")),
    # Gas-Free V2 System URLs - TODO: Implement proper V2 endpoints
    # path('', include('urls_v2')),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Swagger/Redoc drf-yasg
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path("healthz/", healthz),
    path("version/", version),
]

# Compatibility aliases for older frontend paths (no /v1/rewards/ prefix)
urlpatterns += [
    path("api/discounts/pending/", pending_discount_snapshots),
    path("api/discounts/<int:decision_id>/accept/", accept_teacher_choice),
    path("api/discounts/<int:decision_id>/decline/", decline_teacher_choice),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Debug toolbar URLs
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
