from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/reservar', methods=['POST'])
def reservar():
    # Cambiamos 'data' por 'request.form'
    nombre = request.form.get('nombre')
    asiento = request.form.get('asiento')
    
    # Imprime en la consola para verificar
    print(f"Reserva recibida: Pasajero={nombre}, Asiento={asiento}")
    
    return f"<h3>¡Reserva confirmada con éxito para {nombre} en el asiento {asiento}!</h3><br><a href='/'>Volver al inicio</a>"

if __name__ == '__main__':
    app.run(debug=True)