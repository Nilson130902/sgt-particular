import unittest
from app import app, vehiculos, reservas, viaticos, PRECIO_PASAJE

class TestSGTParticular(unittest.TestCase):

    def setUp(self):
        # Configurar cliente de pruebas de Flask
        self.app = app.test_client()
        self.app.testing = True

        # Restablecer estado de los datos de prueba
        reservas.clear()
        viaticos.clear()
        
        # Asegurar estado de vehículo 3 en Mantenimiento para prueba de restricción
        for v in vehiculos:
            if v['id'] == 3:
                v['estado'] = 'Mantenimiento'

    def test_01_bloqueo_reserva_en_mantenimiento(self):
        """Verifica que no se permitan reservas si la unidad está en Mantenimiento."""
        response = self.app.post('/reservar', data={
            'vehiculo_id': 3,
            'nombre': 'Pasajero Prueba',
            'asiento': 'A1'
        }, follow_redirects=True)

        # La lista de reservas debe seguir vacía
        self.assertEqual(len(reservas), 0)
        self.assertIn(b"El veh\xc3\xadculo est\xc3\xa1 en Mantenimiento", response.data)

    def test_02_registro_viatico_exitoso(self):
        """Verifica el registro correcto de un gasto/viático."""
        response = self.app.post('/registrar_viatico', data={
            'vehiculo_id': 1,
            'concepto': 'Combustible',
            'monto': '25.50',
            'descripcion': 'Recarga diésel'
        }, follow_redirects=True)

        self.assertEqual(len(viaticos), 1)
        self.assertEqual(viaticos[0]['monto'], 25.50)
        self.assertEqual(viaticos[0]['concepto'], 'Combustible')

    def test_03_calculo_liquidacion_financiera(self):
        """Verifica que el cálculo de ingresos y ganancia neta en la liquidación sea exacto."""
        # Agregar 2 reservas a la unidad 1
        reservas.append({'id': 1, 'vehiculo_id': 1, 'nombre': 'Juan', 'asiento': 'A1', 'fecha': '2026-10-03'})
        reservas.append({'id': 2, 'vehiculo_id': 1, 'nombre': 'Maria', 'asiento': 'A2', 'fecha': '2026-10-03'})
        
        # Agregar 1 viático de $5.00 a la unidad 1
        viaticos.append({'id': 1, 'vehiculo_id': 1, 'concepto': 'Peaje', 'monto': 5.0, 'descripcion': '', 'fecha': '2026-10-03'})

        # Ingreso esperado: 2 pasajeros * $5.00 = $10.00
        # Ganancia neta esperada: $10.00 - $5.00 = $5.00
        response = self.app.get('/liquidacion')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"+$10.00", response.data)
        self.assertIn(b"-$5.00", response.data)

if __name__ == '__main__':
    unittest.main()