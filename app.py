from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify,send_file
from io import BytesIO
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import os
import json

from dotenv import load_dotenv
from functools import wraps
from flask_mail import Mail, Message
load_dotenv()  
app = Flask(__name__)

###
# bd
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///default.db')
#app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@172.21.0.1/ctf_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24) 

db = SQLAlchemy(app)

###
#correo
# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Usa el servidor SMTP de tu proveedor de correo
app.config['MAIL_PORT'] = 587  # Puerto de Gmail para envío SMTP
app.config['MAIL_USE_TLS'] = True  # Habilitar TLS
app.config['MAIL_USERNAME'] = 'iric.sauldc@gmail.com'  # Tu correo
app.config['MAIL_PASSWORD'] = 'password'  # Tu contraseña de aplicación o la contraseña de correo
app.config['MAIL_DEFAULT_SENDER'] = 'iric.sauldc@gmail.com'  # El correo desde el que se enviarán los mensajes

mail = Mail(app)
# Modelos

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(20), unique=True, nullable=False) 
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contraseña = db.Column(db.String(200), nullable=False)
    puntuacion = db.Column(db.Integer, default=0)  # Puntuación del usuario
    desafios_completados = db.relationship('DesafioCompletado', backref='usuario', lazy=True)

    def verificar_contraseña(self, contraseña):
        return check_password_hash(self.contraseña, contraseña)
 

class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    subcategorias = db.relationship('Subcategoria', backref='categoria', lazy=True)

class Subcategoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)  # Relación con Categoria
    
class Desafio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    puntuacion = db.Column(db.Integer, nullable=False)
    dificultad = db.Column(db.String(50), nullable=False)
    archivo = db.Column(db.LargeBinary, nullable=True)
    flag = db.Column(db.String(255), nullable=False)
    subcategoria_id = db.Column(db.Integer, db.ForeignKey('subcategoria.id'), nullable=False)
    subcategoria = db.relationship('Subcategoria', backref='desafios', lazy=True)

class DesafioCompletado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    desafio_id = db.Column(db.Integer, db.ForeignKey('desafio.id'), nullable=False)
    puntuacion = db.Column(db.Integer, nullable=False, default=0)
    flag_ingresada = db.Column(db.String(200), nullable=False)
    fecha_completado = db.Column(db.TIMESTAMP, default=lambda: datetime.now(timezone.utc))
    tiempo_record = db.Column(db.Float, nullable=True) 
    es_correcta = db.Column(db.Boolean, default=False)

    desafio = db.relationship('Desafio', backref=db.backref('completados', lazy=True))

    def actualizar_puntuacion(self):
        if self.es_correcta:
            usuario = Usuario.query.get(self.usuario_id)
            usuario.puntuacion += self.desafio.puntuacion
            db.session.commit()
            return True
        return False
    
class DesafioEnProgreso(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    desafio_id = db.Column(db.Integer, db.ForeignKey('desafio.id'), nullable=False)
    tiempo_inicio = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    tiempo_limite = db.Column(db.Integer, default=0)  # En segundos, si aplica
    estado = db.Column(db.String(20), default='en_progreso')  # Valores: en_progreso, completado, fallido
    reintentos = db.Column(db.Integer, default=0)
    # Relaciones
    usuario = db.relationship('Usuario', backref='desafios_en_progreso')
    desafio = db.relationship('Desafio', backref='desafios_en_progreso')

    def incrementar_reintentos(self):
        """Incrementa el número de reintentos."""
        self.reintentos += 1
        db.session.commit()

    def __repr__(self):
        return f"<DesafioEnProgreso id={self.id} user_id={self.user_id} desafio_id={self.desafio_id} estado={self.estado}>"

class ProgresoDesafio(db.Model):
    __tablename__ = 'progreso_desafio'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    desafio_id = db.Column(db.Integer, db.ForeignKey('desafio.id'), nullable=False)
    progreso = db.Column(db.JSON, nullable=True)  # Información parcial guardada en JSON
    actualizado_en = db.Column(
        db.DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False
    )

    # Relaciones
    usuario = db.relationship('Usuario', backref='progresos_desafios')
    desafio = db.relationship('Desafio', backref='progresos_desafios')

    def __repr__(self):
        return f"<ProgresoDesafio id={self.id} user_id={self.user_id} desafio_id={self.desafio_id}>"


##########################################################################3

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica si el usuario está en la sesión
        if 'usuario_id' not in session:
            flash('Por favor, inicia sesión primero.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        confirmacion = request.form['confirmacion']

        if contraseña != confirmacion:
            flash("Las contraseñas no coinciden", "error")
            return redirect(url_for('registro'))

        # Verificar si el usuario ya existe
        if Usuario.query.filter_by(usuario=usuario).first():
            flash("El usuario ya existe", "error")
            return redirect(url_for('registro'))

        # Verificar si el correo ya está registrado
        if Usuario.query.filter_by(correo=correo).first():
            flash("El correo ya está registrado", "error")
            return redirect(url_for('registro'))
            

        # Crear nuevo usuario
        nuevo_usuario = Usuario(
            usuario =usuario,
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            contraseña=generate_password_hash(contraseña)
        )
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
        return render_template('registro.html')

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        # Buscar usuario por correo
        usuario = Usuario.query.filter_by(correo=correo).first()
        if usuario and usuario.verificar_contraseña(contraseña):
            session['usuario_id'] = usuario.id
            session['usuario_usuario'] = usuario.usuario
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    session.pop('usuario_nombre', None)
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('index'))

@app.route('/')
def index():
    usuario_logueado = 'usuario_id' in session
    categorias = [
        {'id': 1, 'nombre': 'Superior', 'descripcion': 'Desafíos avanzados.'},
        {'id': 2, 'nombre': 'Media Superior', 'descripcion': 'Desafíos intermedios.'}
    ]
    return render_template('index.html', categorias=categorias, usuario_logueado=usuario_logueado)

@app.route('/soporte', methods=['GET', 'POST'])
def soporte():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        mensaje = request.form['mensaje']

        # Crear el mensaje de correo
        msg = Message('Nuevo mensaje desde el formulario de contacto',
                      recipients=['iric.sauldc@gmail.com'])  # El correo al que se enviará el mensaje
        msg.body = f"Nombre: {nombre}\nCorreo: {correo}\n\nMensaje:\n{mensaje}"

        try:
            mail.send(msg)  # Enviar el correo
            flash('Mensaje enviado con éxito', 'success')
            print("mensaje enviado")
        except Exception as e:
            flash(f'Ocurrió un error al enviar el mensaje: {str(e)}', 'error')
            print("mensaje no enviado")

        return redirect(url_for('soporte'))  # Redirigir después de enviar el mensaje
    return render_template('soporte.html')

@app.route('/recursos')
def recursos():
    return render_template('recursos.html')

@app.route('/terminos')
def term_condi():
    return render_template('term_condi.html')

@app.route('/ranking')
def ranking():
    # Obtener solo los primeros 10 participantes ordenados por puntuación descendente
    participantes = Usuario.query.order_by(Usuario.puntuacion.desc()).limit(5).all()

    # Datos para la tabla principal
    ranking_data = []
    for i, participante in enumerate(participantes):
        desafios_completados = len([dc for dc in participante.desafios_completados if dc.es_correcta])
        tiempo_total = sum([dc.tiempo_record or 0 for dc in participante.desafios_completados if dc.es_correcta])
        penalizaciones = sum([DesafioEnProgreso.query.filter_by(user_id=participante.id, desafio_id=dc.desafio_id).first().reintentos for dc in participante.desafios_completados if dc.es_correcta])
        
#        print(f"Usuario: {participante.usuario}, Tiempo Total: {tiempo_total}")  # Depuración
        
        ranking_data.append({
            'id': participante.id,  # Agrega el ID aquí
            'posicion': i + 1,
            'nombre': f"{participante.usuario}",
            'puntuacion': participante.puntuacion,
            'desafios_completados': desafios_completados,
            'tiempo_total': f"{tiempo_total:.2f}",
            'penalizaciones': penalizaciones
        })

    # Estadísticas globales
    total_participantes = Usuario.query.count()
    total_desafios_resueltos = sum([len([dc for dc in u.desafios_completados if dc.es_correcta]) for u in participantes])

    desafios_mas_dificiles = db.session.query(
        Desafio, db.func.count(DesafioCompletado.id)
    ).join(DesafioCompletado).filter_by(es_correcta=False).group_by(Desafio.id).order_by(db.func.count(DesafioCompletado.id).desc()).limit(5).all()

    estadisticas = {
        'total_usuarios': len(participantes),
        'total_participantes': total_participantes,
        'total_desafios_resueltos': total_desafios_resueltos,
        'desafios_mas_dificiles': [{'nombre': d.nombre, 'fallos': f} for d, f in desafios_mas_dificiles]
    }

    return render_template('ranking.html', ranking_data=ranking_data, estadisticas=estadisticas)

@app.route('/ranking/<int:usuario_id>')
def ranking_detalle(usuario_id):
    participante = Usuario.query.get_or_404(usuario_id)
    detalles = [
        {
            'nombre': dc.desafio.nombre,
            'puntuacion': dc.desafio.puntuacion,
            'categoria': dc.desafio.subcategoria.categoria.nombre,
            'dificultad': dc.desafio.dificultad,
            'tiempo': dc.tiempo_record,
            'fecha': dc.fecha_completado
        }
        for dc in participante.desafios_completados if dc.es_correcta
    ]

    return render_template('ranking_detalle.html', participante=participante, detalles=detalles)

@app.route('/ranking/data')
def ranking_data():
    # Obtener los primeros 10 participantes ordenados por puntuación descendente
    participantes = Usuario.query.order_by(Usuario.puntuacion.desc()).limit(5).all()

    ranking_data = []
    for i, participante in enumerate(participantes):
        desafios_completados = len([dc for dc in participante.desafios_completados if dc.es_correcta])
        tiempo_total = sum([dc.tiempo_record or 0 for dc in participante.desafios_completados if dc.es_correcta])
        penalizaciones = sum([DesafioEnProgreso.query.filter_by(user_id=participante.id, desafio_id=dc.desafio_id).first().reintentos for dc in participante.desafios_completados if dc.es_correcta])

    

        ranking_data.append({
            'id': participante.id,
            'posicion': i + 1,
            'nombre': f"{participante.usuario}",
            'puntuacion': participante.puntuacion,
            'desafios_completados': desafios_completados,
            'tiempo_total': f"{tiempo_total:.2f}",
            'penalizaciones': penalizaciones
        })

    return jsonify(ranking_data)

@app.route('/categoria/<int:categoria_id>')
def categoria(categoria_id):
    # Obtiene la categoría junto con sus subcategorías
    categoria = Categoria.query.get_or_404(categoria_id)
    return render_template('categoria.html', categoria=categoria)

@app.route('/subcategoria/<int:subcategoria_id>')
def subcategoria(subcategoria_id):
    subcategoria = Subcategoria.query.get_or_404(subcategoria_id)
    desafios = Desafio.query.filter_by(subcategoria_id=subcategoria_id).all()
    desafios_con_estado = []

    # Verificar si el usuario está logueado
    usuario_id = session.get('usuario_id')

    if usuario_id:
        # Si el usuario está logueado, verificar el estado de completado de cada desafío
        for desafio in desafios:
            completado = DesafioCompletado.query.filter_by(
                usuario_id=usuario_id,
                desafio_id=desafio.id,
                es_correcta=True
            ).first() is not None
            desafios_con_estado.append((desafio, completado))
    else:
        # Si el usuario no está logueado, marcar todos los desafíos como no completados
        desafios_con_estado = [(desafio, False) for desafio in desafios]

    return render_template('subcategoria.html', subcategoria=subcategoria, desafios_con_estado=desafios_con_estado)

@app.route('/dashboard')
@login_required
def dashboard():
    usuario = Usuario.query.get(session['usuario_id'])

    puntuacion_total = sum([dc.desafio.puntuacion for dc in usuario.desafios_completados if dc.es_correcta])

    niveles = {'Fácil': 0, 'Medio': 0, 'Difícil': 0}
    for dc in usuario.desafios_completados:
        if dc.es_correcta:
            niveles[dc.desafio.dificultad] += 1

    usuarios = Usuario.query.order_by(Usuario.puntuacion.desc()).all()
    posicion_ranking = usuarios.index(usuario) + 1

    total_desafios = Desafio.query.count()
    desafios_completados = len([dc for dc in usuario.desafios_completados if dc.es_correcta])
    progreso_porcentual = (desafios_completados / total_desafios) * 100 if total_desafios > 0 else 0

    ultimo_desafio_completado = max(usuario.desafios_completados, key=lambda x: x.fecha_completado, default=None)

    logros = []
    
    if any(dc.es_correcta and getattr(dc, 'reintentos', 0) == 1 for dc in usuario.desafios_completados):
        logros.append("Desafíos completado sin reintentos")
    
    # Logro: Primera Bandera
    if len(usuario.desafios_completados) > 0:
        logros.append("Primera Bandera")

    # Logro: Explorador Curioso
#    secciones_visitadas = set()
#    for dc in usuario.desafios_completados:
#        secciones_visitadas.add(dc.desafio.subcategoria.categoria.nombre)
#    if len(secciones_visitadas) == len(Categoria.query.all()):
#        logros.append("Explorador Curioso")

    # Logro: Perseverante
    if any(getattr(dc, 'reintentos', 0) > 10 for dc in usuario.desafios_completados if dc.es_correcta):
        logros.append("Perseverante")

    # Logros: Desafíos por nivel
    if niveles['Fácil'] == len([d for d in Desafio.query.filter_by(dificultad='Fácil').all()]):
        logros.append("Desafíos Fáciles")

    if niveles['Medio'] == len([d for d in Desafio.query.filter_by(dificultad='Medio').all()]):
        logros.append("Desafíos Intermedios")

    if niveles['Difícil'] == len([d for d in Desafio.query.filter_by(dificultad='Difícil').all()]):
        logros.append("Desafíos Difíciles")

    # Logros por temática
#    for nombre, tema in tematicas.items():
#        if all(dc.desafio.subcategoria.categoria.nombre == tema and dc.es_correcta for dc in usuario.desafios_completados if dc.desafio.subcategoria.categoria.nombre == tema):
#            logros.append(f"Logro por temática: {nombre}")
    # Logros de velocidad
    if any(dc.tiempo_record and dc.tiempo_record < 5 for dc in usuario.desafios_completados):
        logros.append("Relámpago")

    if any(dc.tiempo_record and dc.fecha_completado == min(usuario.desafios_completados, key=lambda x: x.fecha_completado).fecha_completado for dc in usuario.desafios_completados):
        logros.append("Récord Rápido")

    # Logro Completa Todo
    if desafios_completados == total_desafios:
        logros.append("Completa Todo")

    return render_template('dashboard.html', usuario=usuario, puntuacion_total=puntuacion_total,
                           niveles=niveles, posicion_ranking=posicion_ranking,
                           progreso_porcentual=progreso_porcentual, ultimo_desafio_completado=ultimo_desafio_completado,
                           logros=logros)

@app.route('/foro')
@login_required
def foro():
    if 'usuario_id' in session:
        return render_template('foro.html')
    else:
        flash("Debes iniciar sesión para acceder al foro.")
        return redirect(url_for('login'))

###
@app.route('/desafio/<int:desafio_id>', methods=['GET', 'POST'])
@login_required
def desafio(desafio_id):
    usuario_id = session.get('usuario_id')
    desafio = Desafio.query.get_or_404(desafio_id)

    # Verificar si el usuario ya tiene el desafío en progreso
    progreso = DesafioEnProgreso.query.filter_by(
        user_id=usuario_id,
        desafio_id=desafio_id,
        estado='en_progreso'
    ).first()

    if not progreso:
        # Registrar el inicio del desafío
        progreso = DesafioEnProgreso(
            user_id=usuario_id,
            desafio_id=desafio_id,
            tiempo_inicio=datetime.now()
        )
        db.session.add(progreso)
        db.session.commit()

    if request.method == 'POST':
        flag = request.form.get('flag')
        if not flag:
            mensaje = ('danger', "Debes proporcionar una flag.")
            return render_template('resolver_desafio.html', desafio=desafio, mensaje=mensaje, completado=False)

        # Validar tiempo transcurrido
        tiempo_actual = datetime.now()
        tiempo_transcurrido = (tiempo_actual - progreso.tiempo_inicio).total_seconds()

        if tiempo_transcurrido < 3:  # Validación de tiempo mínimo
            mensaje = ('danger', "Tiempo irreal detectado. Intento inválido.")
            return render_template('resolver_desafio.html', desafio=desafio, mensaje=mensaje, completado=False)

        if flag == desafio.flag:
            # Actualizar progreso como completado
            progreso.estado = 'completado'
            progreso.tiempo_limite = tiempo_transcurrido
            db.session.commit()

            # Registrar desafío completado
            desafio_completado = DesafioCompletado(
                usuario_id=usuario_id,
                desafio_id=desafio_id,
                puntuacion=desafio.puntuacion,
                tiempo_record=tiempo_transcurrido,
                fecha_completado=datetime.now(timezone.utc),
                es_correcta=True
            )
            db.session.add(desafio_completado)
            db.session.commit()
            
            usuario = Usuario.query.get(session['usuario_id'])
            usuario.puntuacion += desafio.puntuacion
            db.session.commit()

            mensaje = ('success', f"¡Desafío completado! Te tomó {tiempo_transcurrido:.2f} segundos.")
            return render_template('resolver_desafio.html', desafio=desafio, mensaje=mensaje, completado=True)

        else:
            progreso.reintentos += 1
            progreso.flag_ingresada = flag
            db.session.commit()
            mensaje = ('danger', "Flag incorrecta. Intenta nuevamente.")
            return render_template('resolver_desafio.html', desafio=desafio, mensaje=mensaje, completado=False)

    return render_template('resolver_desafio.html', desafio=desafio)

@app.route('/descargar_archivo/<int:desafio_id>')
@login_required
def descargar_archivo(desafio_id):
    desafio = Desafio.query.get_or_404(desafio_id)
    if desafio.archivo is None:
        return "No hay archivo asociado a este desafío.", 404

    # Crear un objeto BytesIO con el contenido del archivo
    archivo_stream = BytesIO(desafio.archivo)
    archivo_stream.seek(0)

    # Enviar el archivo con el encabezado correcto
    return send_file(
        archivo_stream,
        as_attachment=True,
        download_name=f"{desafio.nombre}.zip",
        mimetype='application/zip'
    )


##########################
#Manejo de errores
@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404
@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500

###########
#Funciones
def actualizar_progreso(usuario_id, desafio_id, nuevos_datos):
    progreso = ProgresoDesafio.query.filter_by(
        user_id=usuario_id,
        desafio_id=desafio_id
    ).first()

    if progreso:
        progreso_datos = json.loads(progreso.progreso)
        progreso_datos.update(nuevos_datos)
        progreso.progreso = json.dumps(progreso_datos)
        db.session.commit()
    else:
        nuevo_progreso = ProgresoDesafio(
            user_id=usuario_id,
            desafio_id=desafio_id,
            progreso=json.dumps(nuevos_datos)
        )
        db.session.add(nuevo_progreso)
        db.session.commit()

def validar_tiempo(usuario_id, desafio_id):
    progreso = DesafioEnProgreso.query.filter_by(
        user_id=usuario_id,
        desafio_id=desafio_id,
        estado='en_progreso'
    ).first()

    tiempo_actual = datetime.now()
    tiempo_transcurrido = (tiempo_actual - progreso.tiempo_inicio).total_seconds()

    if tiempo_transcurrido < 1:
        raise ValueError("Tiempo irreal detectado.")

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = '127.0.0.1' if debug_mode else '0.0.0.0'
    port = int(os.getenv('FLASK_PORT', 5000))   
    app.run(debug=debug_mode,  host=host, port=port)

#if __name__ == '__main__':
#    app.run(debug=True, host='0.0.0.0')#, port=80)
