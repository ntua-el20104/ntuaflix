
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.management import call_command

# class HealthCheckTest(TestCase):
#     @override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'wrong.db'}})
#     def test_health_check_failure(self):
#         response = self.client.get('/upload/health_check')
#         self.assertEqual(response.http()['status'], 'failed')
    
class CommandTestCase(TestCase):
    def test_create_user(self):
        # Setup
        User.objects.create_user('testuser', 'test@example.com', 'password')

        # Test
        user_exists = User.objects.filter(username='testuser').exists()

        # Assert
        self.assertTrue(user_exists)


class CommandTestCase2(TestCase):
    def test_command_with_authenticated_user(self):
        # Setup
        user = User.objects.create_user('testuser', password='secret')
        self.client.login(username='testuser', password='secret')
