
from django.test import TestCase
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

from django.test import TestCase
from django.contrib.auth.models import User
from myApp.models import Disliked, Movies  

class DislikeActionTestCase(TestCase):
    def setUp(self):
        # Αρχικοποίηση του testing environment
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.title = Movies.objects.create(tconst='t123', primaryTitle='Test Movie',titleType='short',originalTitle="Test",startYear="1999",runtimeMinutes="60")
        self.client.login(username='testuser', password='12345')
        
    def test_dislike_action(self):

        # Εκτέλεση της ενέργειας "dislike"
        response = self.client.post("/title/{self.title.tconst}/html", {'action': 'dislike'})
        
        # Ελέγχουμε αν το "dislike" έχει προστεθεί
        self.assertTrue(Disliked.objects.filter(username=self.user.username, tconst=self.title.tconst).exists())
        
        # Επιβεβαιώνουμε την επιτυχή ανακατεύθυνση
        self.assertEqual(response.status_code, 302)
