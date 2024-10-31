from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
import json
import os
from math import ceil

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Clave para sesiones

# Cargar datos de JSON con manejo de errores
def cargar_datos(archivo):
    try:
        with open(f'src/database/{archivo}', 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error al cargar {archivo}: {e}")
        return {}

def guardar_datos(archivo, datos):
    with open(f'src/database/{archivo}', 'w', encoding='utf-8') as file:
        json.dump(datos, file, indent=4, ensure_ascii=False)

# Cargar datos de usuarios y biblioteca
usuarios = cargar_datos('usuarios.json')
libros = cargar_datos('biblioteca.json').get('biblioteca', [])

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

# Ruta de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('username')
        contrasena = request.form.get('password')
        
        if not usuario or not contrasena:
            return 'Faltan datos de usuario o contraseña', 400

        for user in usuarios.get('usuarios', []):
            if user.get('username') == usuario and user.get('password') == contrasena:
                session['username'] = usuario
                session['role'] = user.get('role')
                return redirect(url_for('admin_dashboard') if user.get('role') == 'admin' else url_for('consultas'))
        
        return 'Usuario o contraseña incorrectos', 403
    
    return render_template('login.html')

# Rutas de dashboard para administrador
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    return render_template('admin/dashboard.html')

# Ruta para ver todos los usuarios
@app.route('/admin/ver_usuarios')
def ver_usuarios():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    return render_template('admin/ver_usuarios.html', usuarios=usuarios.get('usuarios', []))

# Ruta para crear un nuevo usuario
@app.route('/admin/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Obtener datos del formulario
        nuevo_usuario = {
            "id": len(usuarios.get('usuarios', [])) + 1,  # Asignar un ID autoincremental
            "username": request.form.get('username'),
            "password": request.form.get('password'),
            "role": request.form.get('role'),
            "nombre": request.form.get('nombre'),
            "email": request.form.get('email')
        }

        # Validación básica para evitar duplicados
        if any(user['username'] == nuevo_usuario['username'] for user in usuarios.get('usuarios', [])):
            flash('El nombre de usuario ya existe, elige otro.', 'error')
            return redirect(url_for('crear_usuario'))

        usuarios['usuarios'].append(nuevo_usuario)
        guardar_datos('usuarios.json', usuarios)
        flash('Usuario creado exitosamente.', 'success')
        return redirect(url_for('ver_usuarios'))
    
    return render_template('admin/crear_usuario.html')

    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        nuevo_usuario = {
            "username": request.form.get('username'),
            "password": request.form.get('password'),
            "role": request.form.get('role')
        }

        if any(user['username'] == nuevo_usuario['username'] for user in usuarios.get('usuarios', [])):
            flash('El nombre de usuario ya existe, elige otro.', 'error')
            return redirect(url_for('crear_usuario'))

        usuarios['usuarios'].append(nuevo_usuario)
        guardar_datos('usuarios.json', usuarios)
        flash('Usuario creado exitosamente.', 'success')
        return redirect(url_for('ver_usuarios'))
    
    return render_template('admin/crear_usuario.html')


# Ruta para editar un usuario
@app.route('/admin/editar_usuario/<int:user_id>', methods=['GET', 'POST'])
def editar_usuario(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    usuario = next((user for user in usuarios.get('usuarios', []) if user['id'] == user_id), None)

    if not usuario:
        return 'Usuario no encontrado', 404

    if request.method == 'POST':
        # Actualizar los datos del usuario
        if request.form.get('password'):
            usuario['password'] = request.form.get('password')
        usuario['role'] = request.form.get('role')
        usuario['nombre'] = request.form.get('nombre')
        usuario['email'] = request.form.get('email')

        # Guardar los cambios
        guardar_datos('usuarios.json', usuarios)
        flash('Usuario editado exitosamente.', 'success')
        return redirect(url_for('ver_usuarios'))

    return render_template('admin/editar_usuario.html', usuario=usuario)

    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    # Encontrar el usuario a editar
    usuario = next((u for u in usuarios.get('usuarios', []) if u['username'] == username), None)

    if not usuario:
        return 'Usuario no encontrado', 404

    if request.method == 'POST':
        # Actualizar datos del usuario
        usuario['password'] = request.form.get('password', usuario['password'])  # No cambiar si no se proporciona
        usuario['role'] = request.form.get('role', usuario['role'])  # No cambiar si no se proporciona
        # Guardar los cambios
        guardar_datos('usuarios.json', usuarios)
        return redirect(url_for('ver_usuarios'))

    return render_template('admin/editar_usuario.html', usuario=usuario)

# Ruta para bloquear o desbloquear un usuario
@app.route('/admin/bloquear_usuario/<string:username>', methods=['POST'])
def bloquear_usuario(username):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    usuario = next((u for u in usuarios.get('usuarios', []) if u['username'] == username), None)

    if usuario:
        # Alternar estado de bloqueo
        usuario['bloqueado'] = not usuario.get('bloqueado', False)
        # Guardar cambios
        guardar_datos('usuarios.json', usuarios)

    return redirect(url_for('ver_usuarios'))

# Ruta para ver todos los libros con paginación
@app.route('/admin/ver_libros', methods=['GET'])
def ver_libros():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    # Obtener el número de página actual, por defecto es 1
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Resultados por página

    # Calcular el total de libros y la cantidad de páginas
    total_libros = len(libros)
    total_pages = ceil(total_libros / per_page)

    # Calcular el índice de inicio y fin para la paginación
    start = (page - 1) * per_page
    end = start + per_page

    # Obtener los libros de la página actual
    libros_pagina = libros[start:end]

    return render_template('admin/ver_libros.html', libros=libros_pagina, page=page, total_pages=total_pages)

# Ruta para crear un nuevo libro
@app.route('/admin/agregar_libro', methods=['GET', 'POST'])
def agregar_libro():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        nuevo_libro = {
            "titulo": request.form.get('titulo'),
            "autor": request.form.get('autor'),
            "genero": request.form.get('genero'),
            "codigo": request.form.get('codigo'),
            "ubicacion": request.form.get('ubicacion')
        }

        # Validación básica para evitar duplicados (por código)
        if any(libro['codigo'] == nuevo_libro['codigo'] for libro in libros):
            flash('El código del libro ya existe, elige otro.', 'error')
            return redirect(url_for('agregar_libro'))

        libros.append(nuevo_libro)
        guardar_datos('biblioteca.json', {'biblioteca': libros})
        flash('Libro agregado exitosamente.', 'success')
        return redirect(url_for('ver_libros'))
    
    return render_template('admin/agregar_libro.html')

# Rutas de consultas para usuarios
@app.route('/user/consultas')
def consultas():
    if not session.get('username'):
        return redirect(url_for('login'))

    # Obtener parámetros de búsqueda y paginación
    page = int(request.args.get('page', 1))
    limit = 20
    start = (page - 1) * limit
    end = start + limit

    # Filtrado por título o autor si se especifica
    query = request.args.get('q', '').lower()
    libros_filtrados = [libro for libro in libros if query in libro['titulo'].lower() or query in libro['autor'].lower()]

    total_pages = (len(libros_filtrados) + limit - 1) // limit
    libros_paginados = libros_filtrados[start:end]

    return render_template('user/consultas.html', libros=libros_paginados, total_pages=total_pages, current_page=page)

# API para obtener libros con paginación
@app.route('/api/libros', methods=['GET'])
def obtener_libros():
    page = int(request.args.get('page', 1))
    limit = 20
    start = (page - 1) * limit
    end = start + limit

    # Filtrado por título o autor si se especifica
    query = request.args.get('q', '').lower()
    libros_filtrados = [libro for libro in libros if query in libro['titulo'].lower() or query in libro['autor'].lower()]

    total_pages = (len(libros_filtrados) + limit - 1) // limit
    libros_paginados = libros_filtrados[start:end]

    return jsonify({
        'libros': libros_paginados,
        'total_pages': total_pages
    })
# Ruta para logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
