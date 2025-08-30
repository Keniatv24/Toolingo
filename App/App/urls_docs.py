from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

app_name = "docs"

urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('', SpectacularSwaggerView.as_view(url_name='docs:schema'), name='swagger-ui'),
]
