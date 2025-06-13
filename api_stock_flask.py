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
        # 🔍 Depuración: ver las claves que devuelve SQLite
        print("Claves disponibles:", list(row.keys()))

        nombre = row["Nombre producto"]
        precio_lista = row["Precio lista"] if row["Precio lista"] is not None else 0
        des_decimal = row["Desc"] if row["Desc"] is not None else 0
        des_porcentaje = round(float(des_decimal) * 100)
        precio_formateado = f"${int(precio_lista):,}".replace(",", ".")

        # Manejo seguro del campo con tilde
        try:
            produccion = row["Producción"]
        except Exception as e:
            print("Error al acceder a 'Producción':", e)
            produccion = 0

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

        # Detectar si contiene "talla" para sugerir ver más
        sugerencia_tallas = ""
        if "talla" in nombre.lower():
            sugerencia_tallas = "¿Deseas conocer el stock de las demás tallas similares?"

        return jsonify({
            "Resultado": resultado_texto,
            "Referencia": row["Referencia"],
            "Nombre producto": nombre,
            "Medellin": row["Medellin"],
            "Bogota": row["Bogota"],
            "Cali": row["Cali"],
            "Barranquilla": row["Barranquilla"],
            "Cartagena": row["Cartagena"],
            "Producción": produccion,
            "Precio lista": precio_formateado,
            "Descuento de vendedor": f"{des_porcentaje}%",
            "Sugerencia": sugerencia_tallas  # solo aparece si aplica
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
        "REPLACE(REPLACE(LOWER(Nombre producto), '-', ''), '/', '') LIKE ?"
        for _ in palabras
    ]
    condiciones_referencia = [
        "REPLACE(REPLACE(LOWER(Referencia), '-', ''), '/', '') LIKE ?"
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
                WHEN LOWER(Referencia) = ? THEN 1
                WHEN LOWER(Referencia) LIKE ? THEN 2
                WHEN LOWER(Nombre producto) LIKE ? THEN 3
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

@app.route('/tallas', methods=['GET'])
def buscar_otras_tallas():
    ref = request.args.get('ref')
    if not ref:
        return jsonify({"error": "Parámetro 'ref' es obligatorio"}), 400

    conn = sqlite3.connect('stock.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inventario WHERE CAST(Referencia AS TEXT) = ?", (ref,))
    producto = cursor.fetchone()

    if not producto:
        return jsonify({"error": "Referencia no encontrada"}), 404

    nombre_completo = producto["Nombre producto"]
    if "talla" not in nombre_completo.lower():
        return jsonify({"mensaje": "Esta referencia no contiene información de talla."}), 200

    # Extraer base del nombre (antes de 'talla')
    partes = nombre_completo.lower().split("talla")
    nombre_base = partes[0].strip()

    # Buscar productos que tengan el mismo nombre base y contengan "talla"
    query = """
        SELECT *
        FROM inventario
        WHERE LOWER(Nombre producto) LIKE ?
        ORDER BY Nombre producto ASC
    """
    cursor.execute(query, (f"{nombre_base}%talla%",))
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

    return jsonify(resultados)

@app.route('/analisis_inventario', methods=['GET'])
def analisis_inventario():
    try:
        ref = request.args.get('ref')
        if not ref:
            return jsonify({"error": "Parámetro 'ref' es obligatorio"}), 400

        conn = sqlite3.connect('stock.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT Referencia, "Nombre producto", Medellin, Min_Med, Max_Med,
                   Bogota, Min_Bog, Max_Bog,
                   Cali, Min_Cal, Max_Cal,
                   Barranquilla, Min_Baq, Max_Baq,
                   Cartagena, Min_Crt, Max_Crt
            FROM inventario
            WHERE CAST(Referencia AS TEXT) = ?
        """
        cursor.execute(query, (ref,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({"error": "Referencia no encontrada"}), 404

        referencia = row['Referencia']
        nombre_producto = row['Nombre producto']

        ciudades = [
            ("Medellin", "Min_Med", "Max_Med"),
            ("Bogota", "Min_Bog", "Max_Bog"),
            ("Cali", "Min_Cal", "Max_Cal"),
            ("Barranquilla", "Min_Baq", "Max_Baq"),
            ("Cartagena", "Min_Crt", "Max_Crt")
        ]

        resultados = []
        sugerencias = []

        for ciudad, min_col, max_col in ciudades:
            valor = row[ciudad] if row[ciudad] is not None else 0
            min_val = row[min_col] if row[min_col] is not None else 0
            max_val = row[max_col] if row[max_col] is not None else 0

            if valor < min_val:
                estado = "Recompra"
            elif min_val <= valor <= max_val:
                estado = "OK"
            else:
                estado = "Sobrestock"
                diferencia = valor - max_val
                for destino, min_dest, max_dest in ciudades:
                    if destino != ciudad:
                        dest_valor = row[destino] if row[destino] is not None else 0
                        dest_min = row[min_dest] if row[min_dest] is not None else 0
                        capacidad_faltante = dest_min - dest_valor
                        trasladar = min(diferencia, capacidad_faltante)
                        if trasladar > 0:
                            sugerencias.append({
                                "Desde": ciudad,
                                "Hacia": destino,
                                "Cantidad": trasladar
                            })

            resultados.append({
                "Ciudad": ciudad,
                "Stock": valor,
                "Min": min_val,
                "Max": max_val,
                "Estado": estado
            })

        return jsonify({
            "Referencia": referencia,
            "Nombre producto": nombre_producto,
            "Analisis": resultados,
            "Sugerencias de Traslado": sugerencias
        }), 200

    except Exception as e:
        print("❌ ERROR EN EL ENDPOINT /analisis_inventario:", str(e))
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# 🔁 Esto permite que Render detecte correctamente el puerto
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
