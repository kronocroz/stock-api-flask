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
    
    # Determinar tipo de búsqueda (all: todas las palabras, any: cualquiera)
    tipo_busqueda = request.args.get('tipo', 'all')  # 'all' o 'any'
    operador = " AND " if tipo_busqueda == 'all' else " OR "
    
    palabras = nombre.strip().lower().split()
    ignorar = {"ref", "codigo", "cod", "art"}
    palabras = [p for p in palabras if p not in ignorar]
    
    if not palabras:
        return jsonify({"error": "No se ingresaron palabras relevantes"}), 400
    
    # Condiciones para buscar en el nombre del producto
    condiciones_nombre = [
        "REPLACE(REPLACE(LOWER(`Nombre producto`), ''), '/', '') LIKE ?"
        for _ in palabras
    ]
    
    # Condición adicional para buscar en el campo Referencia
    condiciones_referencia = [
        "REPLACE(REPLACE(LOWER(`Referencia`), '-', ''), '/', '') LIKE ?"
        for _ in palabras
    ]
    
    # Combinar todas las condiciones
    todas_condiciones = []
    
    # Agregar condiciones para Nombre producto
    todas_condiciones.append("(" + operador.join(condiciones_nombre) + ")")
    
    # Agregar condiciones para Referencia
    todas_condiciones.append("(" + operador.join(condiciones_referencia) + ")")
    
    # Unir con OR para buscar en cualquiera de los campos
    condicion_final = " OR ".join(todas_condiciones)
    
    # Parámetros para las condiciones de búsqueda
    parametros_nombre = [f"%{p.replace('-', '').replace('/', '')}%" for p in palabras]
    parametros_referencia = [f"%{p.replace('-', '').replace('/', '')}%" for p in palabras]
    parametros = parametros_nombre + parametros_referencia
    
    # Parámetro adicional para ordenamiento por prioridad
    param_orden = f"%{nombre.lower()}%"
    
    conn = sqlite3.connect('stock.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Consulta con priorización para coincidencias exactas en Referencia
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
    
    # Agregamos parámetros para el ordenamiento
    parametros_orden = [nombre.lower(), f"%{nombre.lower()}%", f"%{nombre.lower()}%"]
    cursor.execute(query, parametros_orden + parametros)
    
    filas = cursor.fetchall()
    conn.close()
    
    resultados = []
    for row in filas:
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
        return jsonify({"mensaje": "No se encontraron coincidencias"}), 404
