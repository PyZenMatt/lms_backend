from core.admin_views import custom_admin_logout
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
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
    path("healthz/", healthz),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Debug toolbar URLs
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
