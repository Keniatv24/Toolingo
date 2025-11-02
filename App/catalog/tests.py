from django.test import TestCase
from catalog.models import Categoria

class CategoriaTests(TestCase):
    def test_crear_categoria(self):
        """Debe poder crear una categoría correctamente."""
        c = Categoria.objects.create(nombre="Herramientas Eléctricas")
        self.assertEqual(Categoria.objects.count(), 1)
        self.assertEqual(c.nombre, "Herramientas Eléctricas")

    def test_endpoint_categorias_lista(self):
        """
        Debe responder 200 en el listado de categorías.
        Usamos la URL literal para evitar problemas de reverse/namespace.
        Ajusta la ruta si tu API usa otro prefijo.
        """
        resp = self.client.get("/api/categorias/")
        self.assertEqual(resp.status_code, 200)
