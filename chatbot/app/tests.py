from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from .models import ChatHistory

class ChatBotTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_pagina_principal_carga_en_espanol(self):
        """Verifica que la página principal cargue con código 200 y en idioma español."""
        response = self.client.get(reverse('Chatbot'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<html lang="es">')
        self.assertContains(response, 'Asistente Virtual')
        self.assertContains(response, '172.25.4.247')

    def test_historial_vacio(self):
        """Verifica que el endpoint de historial devuelva lista vacía inicialmente."""
        response = self.client.get(reverse('history'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('history', data)
        self.assertEqual(len(data['history']), 0)

    @patch('app.views.obtener_cadena')
    def test_envio_mensaje_chat_exitoso(self, mock_obtener_cadena):
        """Verifica que el envío de un mensaje guarde en base de datos y responda en JSON."""
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "¡Hola! Estoy respondiendo en español correctamente."
        mock_obtener_cadena.return_value = mock_chain

        response = self.client.post(reverse('chat'), {'user_input': '¿Cómo estás?'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['user_input'], '¿Cómo estás?')
        self.assertEqual(data['bot_response'], "¡Hola! Estoy respondiendo en español correctamente.")
        
        # Verificar que se guardó en la base de datos
        self.assertEqual(ChatHistory.objects.count(), 1)
        registro = ChatHistory.objects.first()
        self.assertEqual(registro.user_input, '¿Cómo estás?')
        self.assertEqual(registro.bot_response, "¡Hola! Estoy respondiendo en español correctamente.")

    def test_chat_mensaje_vacio_retorna_400(self):
        """Verifica que enviar un mensaje vacío retorne error 400."""
        response = self.client.post(reverse('chat'), {'user_input': '   '})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    @patch('app.views.obtener_cadena')
    def test_envio_mensaje_con_rol_programador(self, mock_obtener_cadena):
        """Verifica que se pueda enviar un mensaje especificando el rol de programador."""
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "def suma(a, b):\n    return a + b"
        mock_obtener_cadena.return_value = mock_chain

        response = self.client.post(reverse('chat'), {
            'user_input': 'Escribe una función de suma',
            'rol': 'programador'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['rol'], 'programador')
        self.assertIn('def suma', data['bot_response'])

    def test_exportar_historial_markdown_y_txt(self):
        """Verifica que los endpoints de exportación generen archivos descargables correctos."""
        # Crear datos de prueba
        ChatHistory.objects.create(
            user_input="¿Qué es Linux?",
            bot_response="Linux es un sistema operativo libre tipo Unix."
        )

        # Probar exportación a Markdown
        res_md = self.client.get(reverse('export') + '?formato=md')
        self.assertEqual(res_md.status_code, 200)
        self.assertIn('attachment; filename="historial_chat_', res_md['Content-Disposition'])
        self.assertIn('text/markdown', res_md['Content-Type'])
        self.assertIn('¿Qué es Linux?', res_md.content.decode('utf-8'))

        # Probar exportación a TXT
        res_txt = self.client.get(reverse('export') + '?formato=txt')
        self.assertEqual(res_txt.status_code, 200)
        self.assertIn('text/plain', res_txt['Content-Type'])
        self.assertIn('¿Qué es Linux?', res_txt.content.decode('utf-8'))

        # Probar exportación a JSON
        res_json = self.client.get(reverse('export') + '?formato=json')
        self.assertEqual(res_json.status_code, 200)
        self.assertIn('application/json', res_json['Content-Type'])

    def test_vaciar_historial(self):
        """Verifica que el endpoint de vaciar historial elimine los registros de la BD."""
        ChatHistory.objects.create(user_input="Test 1", bot_response="Resp 1")
        ChatHistory.objects.create(user_input="Test 2", bot_response="Resp 2")
        self.assertEqual(ChatHistory.objects.count(), 2)

        res = self.client.post(reverse('clear_history'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['status'], 'ok')
        self.assertEqual(ChatHistory.objects.count(), 0)


