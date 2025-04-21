from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

@app.route('/stock', methods=['GET'])
def get_stock():
    referencia = request.args.get('ref')
    if not referencia:
        return jsonify({"error": "Parámetro 'ref' es obligatorio"}), 400

    referencia = str(referencia).strip()

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
            f"{referencia} - {nombre}\n\n"
            f"Saldos:\n\n"
            f"Medellín {row['Medellin']},\n"
            f"Bogotá {row['Bogota']},\n"
            f"Cali {row['Cali']},\n"
            f"Barranquilla {row['Barranquilla']},\n"
            f"Cartagena {row['Cartagena']}.\n\n"
            f"Datos del precio: El precio de lista es de {precio_formateado} y tiene un descuento de vendedor del {des_porcentaje}%."
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

    tipo_busqueda = request.args.get('tipo', 'all')  # 'all' o 'any'
    operador = " AND " if tipo_busqueda == 'all' else " OR "

    palabras = nombre.strip().lower().split()
    ignorar = {"ref", "codigo", "cod", "art"}
    palabras = [p for p in palabras if p not in ignorar]

    if not palabras:
        return jsonify({"error": "No se ingresaron palabras relevantes"}), 400

    condiciones_nombre = [
        "REPLACE(REPLACE(LOWER(`Nombre producto`), '-', ''), '/', '') LIKE ?"
        for _ in palabras
    ]
    condiciones_referencia = [
        "REPLACE(REPLACE(LOWER(`Referencia`), '-', ''), '/', '') LIKE ?"
        for _ in palabras
    ]

    condicion_final = f"({operador.join(condiciones_nombre)}) OR ({operador.join(condiciones_referencia)})"
    parametros = [f"%{p.replace('-', '').replace('/', '')}%" for p in palabras] * 2

    param_orden = nombre.lower()
    parametros_orden = [param_orden, f"%{param_orden}%", f"%{param_orden}%"]

    conn = sqlite3.connect('stock.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = f"""
        SELECT *, 
            CASE
                WHEN LOWER(`Referencia`) = ? THEN 1
                WHEN LOWER(`Referencia`) LIKE ? THEN 2
                WHEN LOWER(`Nombre producto`) LIKE ? THEN 3
                ELSE 4
            END AS prioridad
        FROM inventario 
        WHERE {condicion_final}
        ORDER BY prioridad ASC
        LIMIT 20
    """
    cursor.execute(query, parametros_orden + parametros)
    filas = cursor.fetchall()
    conn.close()

    resultados = []
    for row in filas:
        referencia = str(row["Referencia"]).strip()
        nombre_producto = row["Nombre producto"]
        precio_lista = row["Precio lista"] if row["Precio lista"] is not None else 0
        descuento = round(float(row["Desc"] or 0) * 100)
        precio_formateado = f"${int(precio_lista):,}".replace(",", ".")
        
        resultado_texto = (
            f"{referencia} - {nombre_producto}\n\n"
            f"Saldos:\n\n"
            f"Medellín {row['Medellin']},\n"
            f"Bogotá {row['Bogota']},\n"
            f"Cali {row['Cali']},\n"
            f"Barranquilla {row['Barranquilla']},\n"
            f"Cartagena {row['Cartagena']}.\n\n"
            f"Datos del precio: El precio de lista es de {precio_formateado} y tiene un descuento de vendedor del {descuento}%."
        )

        resultados.append({
            "Resultado": resultado_texto,
            "Referencia": referencia,
            "Nombre producto": nombre_producto,
            "Medellin": row["Medellin"],
            "Bogota": row["Bogota"],
            "Cali": row["Cali"],
            "Barranquilla": row["Barranquilla"],
            "Cartagena": row["Cartagena"],
            "Producción": row["Producción"],
            "Precio lista": precio_formateado,
            "Descuento de vendedor": f"{descuento}%"
        })

    if resultados:
        return jsonify(resultados)
    else:
        return jsonify({"mensaje": "No se encontraron coincidencias"}), 404


# 🔁 Esto permite que Render detecte correctamente el puerto
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
