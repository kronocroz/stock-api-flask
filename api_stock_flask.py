from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/stock', methods=['GET'])
def get_stock():
    referencia = request.args.get('ref')
    if not referencia:
        return jsonify({"error": "Parámetro 'ref' es obligatorio"}), 400

    conn = sqlite3.connect('stock.db')
    cursor = conn.cursor()
    query = """
        SELECT "Nombre producto", Medellin, Bogota, Cali, Barranquilla, Cartagena, Producción
        FROM inventario
        WHERE Referencia = ?
    """
    cursor.execute(query, (referencia,))
    result = cursor.fetchone()
    conn.close()

    if result:
        keys = ["Nombre producto", "Medellin", "Bogota", "Cali", "Barranquilla", "Cartagena", "Producción"]
        return jsonify(dict(zip(keys, result)))
    else:
        return jsonify({"error": "Referencia no encontrada"}), 404

@app.route('/buscar_nombre', methods=['GET'])
def buscar_nombre():
    nombre = request.args.get('nombre')
    if not nombre:
        return jsonify({"error": "Parámetro 'nombre' es obligatorio"}), 400

    palabras = nombre.strip().lower().split()

    # Palabras que ignoramos
    ignorar = {"ref", "codigo", "cod", "art"}

    # Filtro de palabras útiles
    palabras = [p for p in palabras if p not in ignorar]

    if not palabras:
        return jsonify({"error": "No se ingresaron palabras relevantes"}), 400

    # Traer posibles coincidencias con LIKE amplio primero
    condiciones = " AND ".join([f"LOWER(`Nombre producto`) LIKE ?" for _ in palabras])
    parametros = [f"%{p}%" for p in palabras]

    query = f"""
        SELECT "Referencia", "Nombre producto", Medellin, Bogota, Cali, Barranquilla, Cartagena, Producción
        FROM inventario
        WHERE {condiciones}
        LIMIT 20
    """

    conn = sqlite3.connect('stock.db')
    cursor = conn.cursor()
    cursor.execute(query, parametros)
    resultados_crudos = cursor.fetchall()
    conn.close()

    # Precisión: solo mantener filas donde cada palabra está como palabra individual
    resultados_filtrados = []
    for fila in resultados_crudos:
        texto = fila[1].lower().replace("-", " ")  # nombre producto
        palabras_producto = set(texto.split())
        if all(palabra in palabras_producto for palabra in palabras):
            resultados_filtrados.append(fila)

   if resultados_filtrados:
        respuesta = []
        for fila in resultados_filtrados:
            referencia = fila[0]
            nombre = fila[1]
            stock_data = dict(zip(
                ["Medellin", "Bogota", "Cali", "Barranquilla", "Cartagena", "Producción"],
                fila[2:]
            ))
            respuesta.append({
                "Resultado": f"{referencia} - {nombre}",
                "Referencia": referencia,
                "Nombre producto": nombre,
                **stock_data
            })
        return jsonify(respuesta)
    else:
        return jsonify({"mensaje": "No se encontraron coincidencias exactas"}), 404
