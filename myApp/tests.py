
from django.test import TestCase, override_settings

class HealthCheckTest(TestCase):
    @override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'wrong.db'}})
    def test_health_check_failure(self):
        response = self.client.get('/upload/health_check')
        self.assertEqual(response.http()['status'], 'failed')
    
