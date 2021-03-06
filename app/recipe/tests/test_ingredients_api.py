from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    """Tests for publicly available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Tests that login is required to access endpoint"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngedientsApiTests(TestCase):
    """Test ingredients can be retrieved by auth user"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@google.com',
            'password1234',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients_list(self):
        """Test retrieving list of ingredients"""
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Carrot')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_ingredients_limited_to_user(self):
        """Test that only ingredints of the auth user are returned"""
        user2 = get_user_model().objects.create_user(
            'whip@gmail.com',
            'password1234',
        )
        Ingredient.objects.create(name='apple', user=user2)
        my = Ingredient.objects.create(name='pear', user=self.user)

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(my.name, res.data[0]['name'])

    def test_create_ingredient_successful(self):
        """Test that aut user can create ingredient"""
        payload = {'name': 'cabbage'}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test that no ingredient created with invalid input"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipe(self):
        """Test filtering ingredients by those assigned to recipes"""
        ingredient1 = Ingredient.objects.create(
            name='broccoli', user=self.user
        )
        ingredient2 = Ingredient.objects.create(
            name='kale', user=self.user
        )
        recipe = Recipe.objects.create(
            title='apple crumble',
            time_minutes=209,
            price=38,
            user=self.user
        )
        recipe.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredient_assigned_unique(self):
        """Test filter ingredients by assigned returns unique items"""
        ingredient = Ingredient.objects.create(user=self.user, name='turkey')
        Ingredient.objects.create(user=self.user, name='bok choi')
        recipe1 = Recipe.objects.create(
            title='eggs benny',
            time_minutes=3,
            price=3,
            user=self.user
        )
        recipe1.ingredients.add(ingredient)
        recipe2 = Recipe.objects.create(
            title='turkey ham',
            time_minutes=5,
            price=6.66,
            user=self.user
        )
        recipe2.ingredients.add(ingredient)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)
