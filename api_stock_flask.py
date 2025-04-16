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
        SELECT "Nombre producto", Medellin, Bogota, Cali, Barranquilla, Cartagena, Producción,
               "Precio de Lista", Des
        FROM inventario
        WHERE Referencia = ?
    """
    cursor.execute(query, (referencia,))
    result = cursor.fetchone()
    conn.close()

    if result:
        nombre = result[0]
        precio_lista = result[7] if result[7] is not None else 0
        des_decimal = result[8] if result[8] is not None else 0
        des_porcentaje = round(float(des_decimal) * 100)
        precio_formateado = f"${int(precio_lista):,}".replace(",", ".")

        resultado_texto = (
            f"{referencia} - {nombre}. "
            f"El precio de lista es de {precio_formateado} y tiene un descuento de vendedor del {des_porcentaje}%."
        )

        keys = ["Nombre producto", "Medellin", "Bogota", "Cali", "Barranquilla", "Cartagena", "Producción"]
        stock_data = dict(zip(keys, result[:7]))

        return jsonify({
            "Resultado": resultado_texto,
            "Referencia": referencia,
            "Nombre producto": nombre,
            **stock_data,
            "Precio de Lista": precio_formateado,
            "Descuento de vendedor": f"{des_porcentaje}%"
        })
    else:
        return jsonify({"error": "Referencia no encontrada"}), 404


@app.route('/buscar_nombre', methods=['GET'])
def buscar_nombre():
    nombre = request.args.get('nombre')
    if not nombre:
        return jsonify({"error": "Parámetro 'nombre' es obligatorio"}), 400

    palabras = nombre.strip().lower().split()
    ignorar = {"ref", "codigo", "cod", "art"}
    palabras = [p for p in palabras if p not in ignorar]

    if not palabras:
        return jsonify({"error": "No se ingresaron palabras relevantes"}), 400

    condiciones = " AND ".join([f"LOWER(`Nombre producto`) LIKE ?" for _ in palabras])
    parametros = [f"%{p}%" for p in palabras]

    query = f"""
        SELECT "Referencia", "Nombre producto", Medellin, Bogota, Cali, Barranquilla, Cartagena, Producción,
               "Precio de Lista", Des
        FROM inventario
        WHERE {condiciones}
        LIMIT 20
    """

    conn = sqlite3.connect('stock.db')
    cursor = conn.cursor()
    cursor.execute(query, parametros)
    resultados_crudos = cursor.fetchall()
    conn.close()

    resultados_filtrados = []
    for fila in resultados_crudos:
        texto = fila[1].lower().replace("-", " ")
        palabras_producto = set(texto.split())
        if all(palabra in palabras_producto for palabra in palabras):
            resultados_filtrados.append(fila)

    if resultados_filtrados:
        respuesta = []
        for fila in resultados_filtrados:
            referencia = fila[0]
            nombre = fila[1]
            precio_lista = fila[8] if fila[8] is not None else 0
            des_decimal = fila[9] if fila[9] is not None else 0
            des_porcentaje = round(float(des_decimal) * 100)
            precio_formateado = f"${int(precio_lista):,}".replace(",", ".")

            resultado_texto = (
                f"{referencia} - {nombre}. "
                f"El precio de lista es de {precio_formateado} y tiene un descuento de vendedor del {des_porcentaje}%."
            )

            stock_data = dict(zip(
                ["Medellin", "Bogota", "Cali", "Barranquilla", "Cartagena", "Producción"],
                fila[2:8]
            ))

            respuesta.append({
                "Resultado": resultado_texto,
                "Referencia": referencia,
                "Nombre producto": nombre,
                **stock_data,
                "Precio de Lista": precio_formateado,
                "Descuento de vendedor": f"{des_porcentaje}%"
            })

        return jsonify(respuesta)
    else:
        return jsonify({"mensaje": "No se encontraron coincidencias exactas"}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
