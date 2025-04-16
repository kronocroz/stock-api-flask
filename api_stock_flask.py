from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/stock', methods=['GET'])
def get_stock():
    referencia = request.args.get('ref')
    if not referencia:
        return jsonify({"error": "Parámetro 'ref' es obligatorio"}), 400

    referencia = str(referencia).strip()  # Aseguramos que sea texto

    conn = sqlite3.connect('stock.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT *
        FROM inventario
        WHERE CAST(Referencia AS TEXT) = ?
    """
    cursor.execute(query, (referencia,))
    row = cursor.fetchone()
    conn.close()

    if row:
        nombre = row["Nombre producto"]
        precio_lista = row["Precio lista"] if row["Precio lista"] is not None else 0
        des_decimal = row["Desc"] if row["Desc"] is not None else 0
        des_porcentaje = round(float(des_decimal) * 100)
        precio_formateado = f"${int(precio_lista):,}".replace(",", ".")

        resultado_texto = (
            f"{referencia} - {nombre}. "
            f"El precio de lista es de {precio_formateado} y tiene un descuento de vendedor del {des_porcentaje}%."
        )

        return jsonify({
            "Resultado": resultado_texto,
            "Referencia": row["Referencia"],
            "Nombre producto": nombre,
            "Medellin": row["Medellin"],
            "Bogota": row["Bogota"],
            "Cali": row["Cali"],
            "Barranquilla": row["Barranquilla"],
            "Cartagena": row["Cartagena"],
            "Producción": row["Producción"],
            "Precio lista": precio_formateado,
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

    conn = sqlite3.connect('stock.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = f"SELECT * FROM inventario WHERE {condiciones} LIMIT 20"
    cursor.execute(query, parametros)
    filas = cursor.fetchall()
    conn.close()

    resultados = []
    for row in filas:
        texto = row["Nombre producto"].lower().replace("-", " ")
        palabras_producto = set(texto.split())
        if all(p in palabras_producto for p in palabras):
            referencia = str(row["Referencia"]).strip()
            nombre = row["Nombre producto"]
            precio_lista = row["Precio lista"] if row["Precio lista"] is not None else 0
            des_decimal = row["Desc"] if row["Desc"] is not None else 0
            des_porcentaje = round(float(des_decimal) * 100)
            precio_formateado = f"${int(precio_lista):,}".replace(",", ".")

            resultado_texto = (
                f"{referencia} - {nombre}. "
                f"El precio de lista es de {precio_formateado} y tiene un descuento de vendedor del {des_porcentaje}%."
            )

            resultados.append({
                "Resultado": resultado_texto,
                "Referencia": referencia,
                "Nombre producto": nombre,
                "Medellin": row["Medellin"],
                "Bogota": row["Bogota"],
                "Cali": row["Cali"],
                "Barranquilla": row["Barranquilla"],
                "Cartagena": row["Cartagena"],
                "Producción": row["Producción"],
                "Precio lista": precio_formateado,
                "Descuento de vendedor": f"{des_porcentaje}%"
            })

    if resultados:
        return jsonify(resultados)
    else:
        return jsonify({"mensaje": "No se encontraron coincidencias exactas"}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
