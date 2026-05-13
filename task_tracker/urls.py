from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from tasks.views import (
    PriorityViewSet,
    ProjectMemberViewSet,
    ProjectViewSet,
    TaskCommentViewSet,
    TaskViewSet,
    UserRegistrationView,
    UserViewSet,
)


router = DefaultRouter()
# Router сам создаёт стандартные REST-маршруты:
# list, retrieve, create, update, partial_update и delete.
router.register('priorities', PriorityViewSet, basename='priority')
router.register('users', UserViewSet, basename='user')
router.register('projects', ProjectViewSet, basename='project')
router.register(
    'project-members',
    ProjectMemberViewSet,
    basename='project-member',
)
router.register('tasks', TaskViewSet, basename='task')
router.register('comments', TaskCommentViewSet, basename='comment')

urlpatterns = [
    # Корень сайта сразу ведёт на Swagger.
    path('', RedirectView.as_view(pattern_name='swagger-ui')),
    path('admin/', admin.site.urls),
    path('api/register/', UserRegistrationView.as_view(), name='register'),
    # Основные endpoints подключаются через router.
    path('api/', include(router.urls)),
    path('api/auth/', include('rest_framework.urls')),
    # OpenAPI схема нужна Swagger и ReDoc.
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
]
