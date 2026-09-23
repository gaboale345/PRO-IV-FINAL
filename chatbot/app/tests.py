from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from .models import ChatHistory, Producto
from .forms import ProductoForm, AjusteStockForm

class InventarioCRDTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Crear datos de prueba iniciales
        self.p1 = Producto.objects.create(
            codigo="COMP-01",
            nombre="Computadora Portátil Dell Inspiron",
            categoria="Computadoras",
            precio=750.00,
            cantidad_existente=10,
            stock_minimo=3,
            estado=True
        )
        self.p2 = Producto.objects.create(
            codigo="PER-01",
            nombre="Teclado Mecánico RGB",
            categoria="Periféricos",
            precio=45.00,
            cantidad_existente=2,
            stock_minimo=5,
            estado=True
        )
        self.p3 = Producto.objects.create(
            codigo="MON-01",
            nombre="Monitor Gamer 144Hz",
            categoria="Monitores",
            precio=220.00,
            cantidad_existente=0, # Agotado
            stock_minimo=2,
            estado=True
        )

    def test_pagina_principal_carga_correctamente(self):
        """Verifica que la interfaz cargue con HTTP 200 y contenga la información de red."""
        response = self.client.get(reverse('Chatbot'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '172.25.4.247')
        self.assertContains(response, 'Inventario & IA Local')

    def test_rf01_registro_producto_exitoso(self):
        """RF-01: Registro de un nuevo producto con campos obligatorios y código único."""
        datos = {
            "codigo": "AUDIO-01",
            "nombre": "Auriculares Inalámbricos con Cancelación",
            "categoria": "Audio",
            "precio": "89.99",
            "cantidad_existente": "15",
            "stock_minimo": "4",
            "estado": "true",
            "descripcion": "Auriculares bluetooth de alta fidelidad"
        }
        res = self.client.post(reverse('api_crear_producto'), data=datos)
        self.assertEqual(res.status_code, 201)
        self.assertTrue(Producto.objects.filter(codigo="AUDIO-01").exists())

    def test_rf01_registro_producto_falla_por_codigo_duplicado_o_precio_negativo(self):
        """RF-01: Validación de que no se permitan códigos duplicados ni precios negativos."""
        # Código duplicado
        res_dup = self.client.post(reverse('api_crear_producto'), data={
            "codigo": "COMP-01", # Ya existe en setUp
            "nombre": "Otra laptop",
            "categoria": "Computadoras",
            "precio": "500",
            "cantidad_existente": "5",
            "stock_minimo": "2",
        })
        self.assertEqual(res_dup.status_code, 400)

        # Precio negativo
        res_neg = self.client.post(reverse('api_crear_producto'), data={
            "codigo": "NEG-01",
            "nombre": "Producto inválido",
            "categoria": "Varios",
            "precio": "-10.00",
            "cantidad_existente": "5",
            "stock_minimo": "1",
        })
        self.assertEqual(res_neg.status_code, 400)

    def test_rf02_consulta_y_busqueda_productos(self):
        """RF-02: Consulta de productos y búsqueda por código, nombre o categoría."""
        # Búsqueda por código
        res_cod = self.client.get(reverse('api_productos') + '?q=COMP-01')
        self.assertEqual(res_cod.status_code, 200)
        data = res_cod.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['productos'][0]['codigo'], "COMP-01")

        # Búsqueda por categoría
        res_cat = self.client.get(reverse('api_productos') + '?categoria=Periféricos')
        self.assertEqual(res_cat.status_code, 200)
        self.assertEqual(res_cat.json()['total'], 1)

    def test_rf03_actualizacion_producto(self):
        """RF-03: Modificar información de un producto existente."""
        res = self.client.post(reverse('api_editar_producto', kwargs={'pk': self.p1.id}), data={
            "codigo": "COMP-01",
            "nombre": "Computadora Portátil Dell XPS Actualizada",
            "categoria": "Computadoras",
            "precio": "899.99",
            "cantidad_existente": "12",
            "stock_minimo": "3",
            "estado": "true"
        })
        self.assertEqual(res.status_code, 200)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.nombre, "Computadora Portátil Dell XPS Actualizada")
        self.assertEqual(float(self.p1.precio), 899.99)
        self.assertEqual(self.p1.cantidad_existente, 12)

    def test_rf04_eliminacion_logica_y_cambio_estado(self):
        """RF-04: Eliminación lógica cambiando estado a inactivo para conservar historial."""
        res = self.client.post(reverse('api_eliminar_producto', kwargs={'pk': self.p2.id}), data={"tipo": "logico"})
        self.assertEqual(res.status_code, 200)
        self.p2.refresh_from_db()
        self.assertFalse(self.p2.estado) # Desactivado lógicamente

    def test_rf05_control_existencia_aumentar_y_disminuir(self):
        """RF-05: Aumentar y disminuir existencias impidiendo valores negativos."""
        # Aumentar
        res_inc = self.client.post(reverse('api_ajustar_stock', kwargs={'pk': self.p1.id}), data={
            "accion": "aumentar",
            "cantidad": "5"
        })
        self.assertEqual(res_inc.status_code, 200)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.cantidad_existente, 15)

        # Disminuir dentro del rango
        res_dec = self.client.post(reverse('api_ajustar_stock', kwargs={'pk': self.p1.id}), data={
            "accion": "disminuir",
            "cantidad": "7"
        })
        self.assertEqual(res_dec.status_code, 200)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.cantidad_existente, 8)

        # Disminuir por encima del stock (debe fallar para impedir cantidad negativa)
        res_fail = self.client.post(reverse('api_ajustar_stock', kwargs={'pk': self.p1.id}), data={
            "accion": "disminuir",
            "cantidad": "100"
        })
        self.assertEqual(res_fail.status_code, 400)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.cantidad_existente, 8) # No se modificó

    def test_rf06_menu_reportes_predefinidos_8_opciones(self):
        """RF-06: Verificación de los 8 reportes predefinidos requeridos."""
        reportes = [
            "todos",
            "mas_caro",
            "mas_barato",
            "pocas_existencias",
            "agotados",
            "por_categoria",
            "valor_total",
            "mayor_existencia"
        ]
        for rep in reportes:
            res = self.client.get(reverse('api_reportes', kwargs={'tipo': rep}))
            self.assertEqual(res.status_code, 200, f"El reporte '{rep}' falló con código {res.status_code}")
            data = res.json()
            self.assertEqual(data["status"], "ok")
            self.assertIn("titulo", data)
            self.assertIn("datos", data)

    @patch('app.views.consultar_ollama_local')
    def test_rf07_rf08_rf09_chat_con_ollama(self, mock_ollama):
        """RF-07, RF-08, RF-09: Chat interactivo con contexto oficial de inventario y restricción."""
        mock_ollama.return_value = (True, "El producto más caro es la Computadora Portátil Dell Inspiron con un precio de Bs. 750.00.")

        res = self.client.post(reverse('chat'), data={"user_input": "¿Cuál es el producto más caro?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("bot_response", data)
        self.assertIn("Computadora Portátil Dell", data["bot_response"])

        # Verificar guardado en historial (RF-10)
        self.assertTrue(ChatHistory.objects.filter(user_input="¿Cuál es el producto más caro?").exists())

    def test_exactitud_agotados_y_extremos_inventario(self):
        """Verifica que el resolver inteligente identifique exactamente los productos agotados y extremos sin alucinaciones."""
        from .views import resolver_contexto_inteligente

        # 1. Agotados
        hecho_agotados, prods_agotados = resolver_contexto_inteligente("¿Qué productos están agotados?")
        self.assertEqual(len(prods_agotados), 1)
        self.assertEqual(prods_agotados[0].codigo, "MON-01") # Definido con cantidad 0 en setUp
        self.assertIn("MON-01", hecho_agotados)

        # 2. Más barato
        hecho_barato, prods_barato = resolver_contexto_inteligente("¿Cuál es el producto más barato?")
        self.assertEqual(len(prods_barato), 1)
        self.assertEqual(prods_barato[0].codigo, "PER-01") # Precio 45.00
        self.assertIn("45.0", hecho_barato)

        # 3. Más caro
        hecho_caro, prods_caro = resolver_contexto_inteligente("¿Cuál es el producto más caro?")
        self.assertEqual(len(prods_caro), 1)
        self.assertEqual(prods_caro[0].codigo, "COMP-01") # Precio 750.00
        self.assertIn("750.0", hecho_caro)

    @patch('app.views.consultar_ollama_local')
    def test_optimizacion_cache_chat(self, mock_ollama):
        """Verifica que las consultas repetidas respondan desde la caché en milisegundos."""
        from .views import invalidar_cache
        invalidar_cache()

        mock_ollama.return_value = (True, "Respuesta generada por IA")
        # Primera consulta (miss de caché)
        res1 = self.client.post(reverse('chat'), data={"user_input": "¿Cuántas unidades hay?"})
        self.assertEqual(res1.status_code, 200)
        self.assertFalse(res1.json().get("cached", False))
        self.assertEqual(mock_ollama.call_count, 1)

        # Segunda consulta idéntica (hit de caché)
        res2 = self.client.post(reverse('chat'), data={"user_input": "¿Cuántas unidades hay?"})
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.json().get("cached", False))
        # Ollama no debe haber sido llamado una segunda vez
        self.assertEqual(mock_ollama.call_count, 1)

    def test_chat_stream_sse_endpoint(self):
        """Verifica que el endpoint de streaming SSE retorne un stream con Content-Type text/event-stream."""
        res = self.client.post(reverse('chat_stream'), data={"user_input": "¿Cómo hacer una receta de pizza?"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "text/event-stream")
        content = b"".join(res.streaming_content).decode("utf-8")
        self.assertIn("No encontré información suficiente", content)

    def test_kardex_registro_movimientos_y_consulta_api(self):
        """Verifica el registro atómico de movimientos en el Kardex y su consulta vía API."""
        # 1. Ajuste de stock vía API
        res_ajuste = self.client.post(
            reverse('api_ajustar_stock', kwargs={'pk': self.p1.id}),
            data={"accion": "aumentar", "cantidad": 4, "motivo": "Recepción de lote de prueba"}
        )
        self.assertEqual(res_ajuste.status_code, 200)

        # 2. Consultar Kardex del producto
        res_kardex = self.client.get(reverse('api_kardex_producto', kwargs={'pk': self.p1.id}))
        self.assertEqual(res_kardex.status_code, 200)
        data = res_kardex.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["producto"]["id"], self.p1.id)
        self.assertGreaterEqual(data["total_movimientos"], 1)

        # Verificar primer movimiento
        ultimo_mov = data["movimientos"][0]
        self.assertEqual(ultimo_mov["tipo"], "ENTRADA")
        self.assertEqual(ultimo_mov["cantidad"], 4)
        self.assertEqual(ultimo_mov["stock_previo"], 10)
        self.assertEqual(ultimo_mov["stock_resultante"], 14)
        self.assertIn("Recepción de lote de prueba", ultimo_mov["motivo"])

    def test_paginacion_catalogo_productos(self):
        """Verifica la paginación interactiva del catálogo sin recarga de página."""
        # Consultar página 1 con tamaño de 2 productos
        res = self.client.get(reverse('api_productos') + '?pagina=1&por_pagina=2')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["pagina"], 1)
        self.assertEqual(data["por_pagina"], 2)
        self.assertEqual(data["total"], 3)
        self.assertEqual(data["total_paginas"], 2)
        self.assertEqual(len(data["productos"]), 2)

        # Consultar página 2
        res2 = self.client.get(reverse('api_productos') + '?pagina=2&por_pagina=2')
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(data2["pagina"], 2)
        self.assertEqual(len(data2["productos"]), 1)

    def test_exportacion_catalogo_csv(self):
        """Verifica la exportación en tiempo real del catálogo a formato CSV."""
        res = self.client.get(reverse('api_exportar_productos') + '?formato=csv')
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/csv", res["Content-Type"])
        self.assertIn("attachment; filename=", res["Content-Disposition"])
        content = res.content.decode("utf-8-sig")
        self.assertIn("Código", content)
        self.assertIn("Precio (Bs.)", content)
        self.assertIn("Cantidad Existente", content)
        self.assertIn("COMP-01", content)
        self.assertIn("PER-01", content)

    def test_exportacion_catalogo_pdf_hoja_oficial(self):
        """Verifica la generación de la Hoja Oficial de Inventario Valorizado imprimible en PDF."""
        res = self.client.get(reverse('api_exportar_productos') + '?formato=pdf')
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res["Content-Type"])
        content = res.content.decode("utf-8")
        self.assertIn("SISTEMA INTEGRADO DE INVENTARIO Y ALMACÉN", content)
        self.assertIn("Responsable de Almacén", content)
        self.assertIn("Auditor de Sistemas", content)
        self.assertIn("Bs.", content)

    def test_importacion_catalogo_csv_valido(self):
        """Verifica la importación masiva de productos desde archivo CSV."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        csv_contenido = (
            "codigo,nombre,categoria,precio,cantidad_existente,stock_minimo,descripcion\n"
            "MIC-01,Micrófono Condensador USB,Audio,320.50,15,4,Micrófono para streaming y podcast\n"
            "CAM-01,Cámara Web 1080p 60fps,Video,450.00,8,2,Cámara web profesional\n"
        )
        archivo_csv = SimpleUploadedFile(
            "importar_prueba.csv",
            csv_contenido.encode("utf-8-sig"),
            content_type="text/csv"
        )
        res = self.client.post(reverse('api_importar_productos'), {"archivo_csv": archivo_csv})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["creados"], 2)

        # Verificar que existen en la base de datos
        self.assertTrue(Producto.objects.filter(codigo="MIC-01").exists())
        self.assertTrue(Producto.objects.filter(codigo="CAM-01").exists())

