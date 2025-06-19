from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from . import views

schema_view = get_schema_view(
    openapi.Info(
        title="Library API",
        default_version='v1',
        description="API documentation for Library Management System",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,), 
    )

router = DefaultRouter()
router.register(r'register', views.RegisterViewSet, basename='register')
router.register(r'books', views.BookViewSet)
router.register(r'borrows', views.BorrowViewSet, basename='borrow')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
urlpatterns += [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]