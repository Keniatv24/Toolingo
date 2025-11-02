from django.test import TestCase
from django.test import TestCase
from users.models import User

class UserTests(TestCase):
    def test_crear_usuario(self):
        """Debe poder crear un usuario correctamente."""
        user = User.objects.create_user(username="keni", password="12345")
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(user.check_password("12345"))
