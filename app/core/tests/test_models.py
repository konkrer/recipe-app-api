from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models
from unittest.mock import patch


def sample_user(email='rich@gmail.com', password='testpass1234'):
    """Create a sample user"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """Test - can successfully create user model"""
        email = 'developeroriented@gmail.com'
        password = 'testpass1234'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test that the email for a new user is normalized"""
        email = 'developeroriented@GMAIL.COM'
        user = get_user_model().objects.create_user(email, 'test1234')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'test1234')

    def test_create_new_superuser(self):
        """Test creating superuser"""
        user = get_user_model().objects.create_superuser(
            'test@gmail.com',
            'test1234',
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """Test the tag string representation"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Vegan',
        )

        self.assertEqual(str(tag), tag.name)

    def test_ingredients_str(self):
        """Test the ingredients string representation"""
        ingredient = models.Ingredient.objects.create(
            user=sample_user(),
            name='Carrot',
        )

        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        """Test the reicipe string representation"""
        recipe = models.Recipe.objects.create(
            title='Bread',
            user=sample_user(),
            time_minutes=5,
            price=5.99
        )
        self.assertEqual(str(recipe), recipe.title)

    @patch('uuid.uuid4')
    def test_recipe_filename_uuid(self, mock_uuid):
        """Test that image is saved in the correct location"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'myimage.jpg')

        expected_path = f'upload/recipe/{uuid}.jpg'
        self.assertEqual(file_path, expected_path)
