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
