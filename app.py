from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup
from datetime import datetime
from functools import wraps
import urllib.parse

app = Flask(__name__)
app.secret_key = 'sgt_particular_secret_key_super_segura'

PRECIO_PASAJE_DEFECTO = 5.00

usuarios = [
    {
        'id': 1,
        'username': 'admin',
        'password': generate_password_hash('admin123'),
        'rol': 'admin',
        'nombre': 'Administrador del Sistema'
    },
    {
        'id': 2,
        'username': 'pedro',
        'password': generate_password_hash('chofer123'),
        'rol': 'conductor',
        'nombre': 'Pedro Picapiedra',
        'vehiculo_id': 1
    }
]

vehiculos = [
    {'id': 1, 'placa': 'PBC-1234', 'modelo': 'Hino Coaster', 'tipo': 'Buseta', 'capacidad': 12, 'chofer': 'Pedro Picapiedra', 'estado': 'En Servicio', 'mantenimiento': 'Al día'},
    {'id': 2, 'placa': 'PBA-5678', 'modelo': 'Hyundai H350', 'tipo': 'Furgoneta', 'capacidad': 15, 'chofer': 'Pablo Mármol', 'estado': 'En Servicio', 'mantenimiento': 'Al día'},
    {'id': 3, 'placa': 'PBT-9012', 'modelo': 'Mercedes-Benz Sprinter', 'tipo': 'Buseta', 'capacidad': 19, 'chofer': 'Vilma Picapiedra', 'estado': 'En Servicio', 'mantenimiento': 'Al día'}
]

rutas = [
    {'id': 1, 'origen': 'Puyo', 'destino': 'Tena', 'precio': 4.00},
    {'id': 2, 'origen': 'Puyo', 'destino': 'Baños', 'precio': 3.50},
    {'id': 3, 'origen': 'Puyo', 'destino': 'Ambato', 'precio': 6.00},
    {'id': 4, 'origen': 'Puyo', 'destino': 'Macas', 'precio': 5.00},
    {'id': 5, 'origen': 'Puyo', 'destino': 'Quito', 'precio': 25.00}
]

reservas = []
viaticos = []
historial_viajes = []

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor inicia sesión para acceder al sistema.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session or session.get('rol') != 'admin':
            flash('Acceso restringido únicamente a Administradores.', 'danger')
            return redirect(url_for('conductor'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = next((u for u in usuarios if u['username'].lower() == username.lower()), None)

        if user and check_password_hash(user['password'], password):
            session['usuario_id'] = user['id']
            session['username'] = user['username']
            session['nombre'] = user['nombre']
            session['rol'] = user['rol']
            session['vehiculo_id'] = int(user.get('vehiculo_id', 1))

            flash(f'¡Bienvenido {user["nombre"]}!', 'success')

            if user['rol'] == 'admin':
                return redirect(url_for('index'))
            else:
                return redirect(url_for('conductor'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        vehiculo_id = int(request.form.get('vehiculo_id', 1))

        if not username or not password or not nombre:
            flash('Por favor completa todos los campos del formulario.', 'warning')
            return redirect(url_for('registro'))

        if any(u['username'].lower() == username.lower() for u in usuarios):
            flash('El nombre de usuario ya existe. Intenta con otro.', 'danger')
            return redirect(url_for('registro'))

        nuevo_usuario = {
            'id': len(usuarios) + 1,
            'username': username,
            'password': generate_password_hash(password),
            'rol': 'conductor',
            'nombre': nombre,
            'vehiculo_id': vehiculo_id
        }
        usuarios.append(nuevo_usuario)

        session['usuario_id'] = nuevo_usuario['id']
        session['username'] = nuevo_usuario['username']
        session['nombre'] = nuevo_usuario['nombre']
        session['rol'] = nuevo_usuario['rol']
        session['vehiculo_id'] = vehiculo_id

        flash('Registro completado e inicio de sesión exitoso.', 'success')
        return redirect(url_for('conductor'))

    return render_template('registro.html', vehiculos=vehiculos)

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
@admin_required
def index():
    vehiculo_id = request.args.get('vehiculo_id', default=1, type=int)
    search_query = request.args.get('buscar_pasajero', default='', type=str).strip().lower()
    
    unidad = next((v for v in vehiculos if v['id'] == vehiculo_id), vehiculos[0])
    reservas_unidad = [r for r in reservas if r['vehiculo_id'] == unidad['id']]
    
    if search_query:
        reservas_filtradas = [r for r in reservas_unidad if search_query in r['nombre'].lower()]
    else:
        reservas_filtradas = reservas_unidad

    asientos_ocupados = [r['asiento'] for r in reservas_unidad]
    stats = {
        'ocupados': len(asientos_ocupados),
        'disponibles': unidad['capacidad'] - len(asientos_ocupados)
    }

    viaticos_unidad = [v for v in viaticos if v['vehiculo_id'] == unidad['id']]
    total_viaticos = sum(v['monto'] for v in viaticos_unidad)
    total_ingresos = sum(r.get('precio', PRECIO_PASAJE_DEFECTO) for r in reservas_unidad)
    ganancia_neta = total_ingresos - total_viaticos

    return render_template('index.html', 
                           flota=vehiculos, 
                           unidad=unidad, 
                           reservas=reservas_filtradas,
                           asientos_ocupados=asientos_ocupados,
                           stats=stats,
                           rutas=rutas,
                           viaticos=viaticos_unidad,
                           total_viaticos=total_viaticos,
                           total_ingresos=total_ingresos,
                           ganancia_neta=ganancia_neta,
                           search_query=search_query)

@app.route('/conductor')
@login_required
def conductor():
    if session.get('rol') == 'admin':
        vehiculo_id = request.args.get('vehiculo_id', type=int)
        if not vehiculo_id:
            vehiculo_id = session.get('vehiculo_id', 1)
    else:
        vehiculo_id = session.get('vehiculo_id', 1)

    unidad = next((v for v in vehiculos if v['id'] == vehiculo_id), vehiculos[0])
    reservas_unidad = [r for r in reservas if r['vehiculo_id'] == unidad['id']]
    stats = {
        'ocupados': len(reservas_unidad),
        'disponibles': unidad['capacidad'] - len(reservas_unidad)
    }

    return render_template('conductor.html', unidad=unidad, reservas=reservas_unidad, stats=stats)

@app.route('/reservar', methods=['POST'])
@login_required
def reservar():
    vehiculo_id = int(request.form.get('vehiculo_id'))
    nombre = request.form.get('nombre')
    telefono = request.form.get('telefono', '').strip()
    asiento = request.form.get('asiento')
    hora_salida = request.form.get('hora_salida', 'Sin definir')
    ruta_id = int(request.form.get('ruta_id', 0))

    unidad = next((v for v in vehiculos if v['id'] == vehiculo_id), None)
    if unidad and unidad['estado'] == 'Mantenimiento':
        flash('El vehículo está en Mantenimiento. No se pueden realizar reservas.', 'danger')
        return redirect(url_for('index', vehiculo_id=vehiculo_id))

    ruta_sel = next((r for r in rutas if r['id'] == ruta_id), None)
    precio_aplicado = ruta_sel['precio'] if ruta_sel else PRECIO_PASAJE_DEFECTO
    origen_destino = f"{ruta_sel['origen']} ➔ {ruta_sel['destino']}" if ruta_sel else "Ruta General"

    # Construcción de mensaje para WhatsApp
    texto_whatsapp = (
        f"🚌 BOLETO DIGITAL - SGT-Particular*\n\n"
        f"👤 Pasajero: {nombre}\n"
        f"💺 Asiento: {asiento}\n"
        f"📍 Ruta: {origen_destino}\n"
        f"⏰ Hora de Salida: {hora_salida}\n"
        f"💵 Valor: ${precio_aplicado:.2f}\n"
        f"🚐 Unidad: {unidad['modelo']} ({unidad['placa']})\n"
        f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"¡Gracias por viajar con nosotros!"
    )

    mensaje_url = urllib.parse.quote(texto_whatsapp)
    
    # Si ingresó número telefónico se envía directo a su chat, si no, abre selector general de WhatsApp
    if telefono:
        whatsapp_link = f"https://api.whatsapp.com/send?phone={telefono}&text={mensaje_url}"
    else:
        whatsapp_link = f"https://api.whatsapp.com/send?text={mensaje_url}"

    nueva_reserva = {
        'id': len(reservas) + 1,
        'vehiculo_id': vehiculo_id,
        'nombre': nombre,
        'telefono': telefono,
        'asiento': asiento,
        'hora_salida': hora_salida,
        'fecha': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'ruta_id': ruta_id,
        'precio': precio_aplicado,
        'whatsapp_link': whatsapp_link
    }
    reservas.append(nueva_reserva)

    mensaje_html = Markup(
        f'Reserva registrada para {nombre} (Asiento {asiento}). '
        f'<a href="{whatsapp_link}" target="_blank" class="btn btn-sm btn-success ms-2 fw-bold">'
        f'<i class="bi bi-whatsapp me-1"></i>Enviar Boleto por WhatsApp</a>'
    )

    flash(mensaje_html, 'success')

    if session.get('rol') == 'conductor':
        return redirect(url_for('conductor'))
    return redirect(url_for('index', vehiculo_id=vehiculo_id))

@app.route('/eliminar_reserva/<int:reserva_id>', methods=['POST'])
@login_required
def eliminar_reserva(reserva_id):
    global reservas
    vehiculo_id = request.args.get('vehiculo_id', type=int, default=1)
    reserva = next((r for r in reservas if r['id'] == reserva_id), None)
    
    if reserva:
        reservas = [r for r in reservas if r['id'] != reserva_id]
        flash(f'Reserva de {reserva["nombre"]} (Asiento {reserva["asiento"]}) cancelada.', 'warning')
    
    if session.get('rol') == 'conductor':
        return redirect(url_for('conductor'))
    return redirect(url_for('index', vehiculo_id=vehiculo_id))

@app.route('/agregar_vehiculo', methods=['POST'])
@login_required
@admin_required
def agregar_vehiculo():
    placa = request.form.get('placa')
    modelo = request.form.get('modelo')
    tipo = request.form.get('tipo', 'Buseta')
    capacidad = int(request.form.get('capacidad', 12))
    chofer = request.form.get('chofer')

    nuevo_v = {
        'id': len(vehiculos) + 1,
        'placa': placa,
        'modelo': modelo,
        'tipo': tipo,
        'capacidad': capacidad,
        'chofer': chofer,
        'estado': 'En Servicio',
        'mantenimiento': 'Al día'
    }
    vehiculos.append(nuevo_v)
    flash(f'Vehículo {modelo} ({placa}) agregado.', 'success')
    return redirect(url_for('index', vehiculo_id=nuevo_v['id']))

@app.route('/editar_vehiculo', methods=['POST'])
@login_required
@admin_required
def editar_vehiculo():
    vehiculo_id = int(request.form.get('vehiculo_id'))
    unidad = next((v for v in vehiculos if v['id'] == vehiculo_id), None)
    if unidad:
        unidad['placa'] = request.form.get('placa')
        unidad['modelo'] = request.form.get('modelo')
        unidad['tipo'] = request.form.get('tipo')
        unidad['capacidad'] = int(request.form.get('capacidad'))
        unidad['chofer'] = request.form.get('chofer')
        unidad['mantenimiento'] = request.form.get('mantenimiento')
        flash('Vehículo actualizado correctamente.', 'success')
    return redirect(url_for('index', vehiculo_id=vehiculo_id))

@app.route('/agregar_ruta', methods=['POST'])
@login_required
@admin_required
def agregar_ruta():
    origen = request.form.get('origen', 'Puyo').strip()
    destino = request.form.get('destino').strip()
    precio = float(request.form.get('precio', 0.0))

    if destino and precio > 0:
        rutas.append({'id': len(rutas) + 1, 'origen': origen, 'destino': destino, 'precio': precio})
        flash(f'Ruta {origen} - {destino} (${precio:.2f}) guardada.', 'success')
    return redirect(url_for('index'))

@app.route('/editar_ruta', methods=['POST'])
@login_required
@admin_required
def editar_ruta():
    ruta_id = int(request.form.get('ruta_id'))
    ruta_item = next((r for r in rutas if r['id'] == ruta_id), None)
    if ruta_item:
        ruta_item['origen'] = request.form.get('origen')
        ruta_item['destino'] = request.form.get('destino')
        ruta_item['precio'] = float(request.form.get('precio'))
        flash('Ruta actualizada.', 'info')
    return redirect(url_for('index'))

@app.route('/eliminar_ruta/<int:ruta_id>', methods=['POST'])
@login_required
@admin_required
def eliminar_ruta(ruta_id):
    global rutas
    rutas = [r for r in rutas if r['id'] != ruta_id]
    flash('Ruta eliminada.', 'warning')
    return redirect(url_for('index'))

@app.route('/cambiar_estado_flota', methods=['POST'])
@login_required
def cambiar_estado_flota():
    vehiculo_id = int(request.form.get('vehiculo_id'))
    nuevo_estado = request.form.get('estado')
    for v in vehiculos:
        if v['id'] == vehiculo_id:
            v['estado'] = nuevo_estado
            break
    flash(f'Estado actualizado a: {nuevo_estado}', 'info')
    
    if session.get('rol') == 'conductor':
        return redirect(url_for('conductor'))
    return redirect(url_for('index', vehiculo_id=vehiculo_id))

@app.route('/registrar_viatico', methods=['POST'])
@login_required
def registrar_viatico():
    vehiculo_id = int(request.form.get('vehiculo_id'))
    viaticos.append({
        'id': len(viaticos) + 1,
        'vehiculo_id': vehiculo_id,
        'concepto': request.form.get('concepto'),
        'monto': float(request.form.get('monto', 0)),
        'descripcion': request.form.get('descripcion'),
        'fecha': datetime.now().strftime('%Y-%m-%d %H:%M')
    })
    flash('Viático registrado.', 'success')
    if session.get('rol') == 'conductor':
        return redirect(url_for('conductor'))
    return redirect(url_for('index', vehiculo_id=vehiculo_id))

@app.route('/eliminar_viatico/<int:viatico_id>', methods=['POST'])
@login_required
@admin_required
def eliminar_viatico(viatico_id):
    global viaticos
    v_item = next((v for v in viaticos if v['id'] == viatico_id), None)
    vehiculo_id = v_item['vehiculo_id'] if v_item else 1
    viaticos = [v for v in viaticos if v['id'] != viatico_id]
    flash('Registro de viático eliminado.', 'warning')
    return redirect(url_for('index', vehiculo_id=vehiculo_id))

@app.route('/liquidacion')
@login_required
@admin_required
def liquidacion():
    vehiculo_id = request.args.get('vehiculo_id', default=1, type=int)
    unidad = next((v for v in vehiculos if v['id'] == vehiculo_id), vehiculos[0])
    
    reservas_unidad = [r for r in reservas if r['vehiculo_id'] == unidad['id']]
    viaticos_unidad = [v for v in viaticos if v['vehiculo_id'] == unidad['id']]

    total_ingresos = sum(r.get('precio', PRECIO_PASAJE_DEFECTO) for r in reservas_unidad)
    total_viaticos = sum(v['monto'] for v in viaticos_unidad)
    ganancia_neta = total_ingresos - total_viaticos

    return render_template('liquidacion.html', 
                           unidad=unidad, 
                           reservas=reservas_unidad, 
                           viaticos=viaticos_unidad,
                           total_ingresos=total_ingresos,
                           total_viaticos=total_viaticos,
                           ganancia_neta=ganancia_neta,
                           historial_viajes=historial_viajes)

@app.route('/cerrar_caja', methods=['POST'])
@login_required
@admin_required
def cerrar_caja():
    global reservas, viaticos
    vehiculo_id = int(request.form.get('vehiculo_id'))
    unidad = next((v for v in vehiculos if v['id'] == vehiculo_id), None)

    if unidad:
        reservas_unidad = [r for r in reservas if r['vehiculo_id'] == vehiculo_id]
        viaticos_unidad = [v for v in viaticos if v['vehiculo_id'] == vehiculo_id]

        total_ingresos = sum(r.get('precio', PRECIO_PASAJE_DEFECTO) for r in reservas_unidad)
        total_gastos = sum(v['monto'] for v in viaticos_unidad)
        ganancia_neta = total_ingresos - total_gastos

        historial_viajes.append({
            'id': len(historial_viajes) + 1,
            'vehiculo': f"{unidad['modelo']} ({unidad['placa']})",
            'chofer': unidad['chofer'],
            'pasajeros_totales': len(reservas_unidad),
            'ingresos': total_ingresos,
            'gastos': total_gastos,
            'ganancia_neta': ganancia_neta,
            'fecha_cierre': datetime.now().strftime('%Y-%m-%d %H:%M')
        })

        reservas = [r for r in reservas if r['vehiculo_id'] != vehiculo_id]
        viaticos = [v for v in viaticos if v['vehiculo_id'] != vehiculo_id]
        unidad['estado'] = 'En Servicio'

        flash(f'¡Cierre de caja completado! Ganancia neta: ${ganancia_neta:.2f}', 'success')
    return redirect(url_for('liquidacion', vehiculo_id=vehiculo_id))

if __name__ == '__main__':
    app.run(debug=True)