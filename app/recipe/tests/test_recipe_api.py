import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPE_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Return url for recipe image upload"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id):
    """Return recipe detail url"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main course'):
    """Create and return sample tag for testing"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Carrot'):
    """Create and return sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'bread',
        'time_minutes': 50,
        'price': 5.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeAPITests(TestCase):
    """Tests for the public recipe endpoint"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required_recipe(self):
        """Test that autenticaton is required for recipe access"""
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Tests for authenticated user recipe API access"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='rich@gmail.com',
            password='password12345',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test that a user can only retrieve their own recipe"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user, title="Beans")

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_limited_to_user(self):
        """Test retrieving recipe for user"""
        user2 = get_user_model().objects.create_user(
            'test@gmail.com',
            'password3456',
        )
        sample_recipe(self.user)
        sample_recipe(user2)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(self.user)
        recipe.tags.add(sample_tag(self.user))
        recipe.ingredients.add(sample_ingredient(self.user))

        res = self.client.get(detail_url(recipe.id))

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating basic recipe"""
        payload = {
            'title': 'Cake',
            'time_minutes': 40,
            'price': 20,
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload:
            self.assertEqual(payload[key], getattr(recipe, key))
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe_with_tags(self):
        """Test creating recipe with associated tags"""
        tag1 = sample_tag(self.user)
        tag2 = sample_tag(self.user, name='Fatty food')
        payload = {
            'title': 'Cheescake',
            'time_minutes': 49,
            'price': 30,
            'tags': [tag1.id, tag2.id]
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)
        #  Remove probably
        serializer = RecipeDetailSerializer(recipe)
        res = self.client.get(detail_url(recipe.id))
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with associated ingredients"""
        ingred1 = sample_ingredient(self.user)
        ingred2 = sample_ingredient(self.user, name='sugar')
        payload = {
            'title': 'cake',
            'time_minutes': 39,
            'price': 39,
            'ingredients': [ingred1.id, ingred2.id]
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingred1, ingredients)
        self.assertIn(ingred2, ingredients)

    def test_patch_recipe(self):
        """Test updating recipe with patch"""
        recipe = sample_recipe(self.user)
        recipe.tags.add(sample_tag(self.user))
        tag = sample_tag(self.user, name='bacon')

        payload = {
            'title': 'Ham hack',
            'tags': tag.id
        }
        res = self.client.patch(detail_url(recipe.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        serializer = RecipeSerializer(recipe)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(serializer.data['tags'], [payload['tags']])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(tag, tags)

    def test_put_recipe(self):
        """Test updating recipe with put method"""
        recipe = sample_recipe(self.user)
        recipe.tags.add(sample_tag(self.user))
        payload = {
            'title': 'Ham hack',
            'time_minutes': 38,
            'price': 33.00
        }
        res = self.client.put(detail_url(recipe.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        serializer = RecipeSerializer(recipe)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(recipe.title, payload['title'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)


class RecipeImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'rich@gmail.com',
            'password12345'
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)  # go back to begining of file_path
            res = self.client.post(url, {'image': ntf, format: 'multipart'})

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'notimage', format: 'multipart'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
