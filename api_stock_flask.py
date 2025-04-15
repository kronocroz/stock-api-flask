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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 