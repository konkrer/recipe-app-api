from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'tags', views.TagViewSet)
router.register(r'ingredients', views.IngredientViewSet)
router.register(r'recipes', views.RecipeViewset)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls))
]
