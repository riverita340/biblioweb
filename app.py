from flask import Flask, jsonify, request, render_template
import json

app = Flask(__name__)

# Cargar los libros desde el archivo JSON
with open('src/database/biblioteca.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
    libros = data['biblioteca']

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')


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

if __name__ == '__main__':
    app.run(debug=True)
