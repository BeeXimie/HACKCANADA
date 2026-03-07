from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('scholarships.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/scholarships')
def get_scholarships():
    conn = get_db_connection()
    scholarships = conn.execute('SELECT * FROM ouinfo_scholarships').fetchall()
    conn.close()
    
    return jsonify([dict(ix) for ix in scholarships])

if __name__ == '__main__':
    print("Run this to serve your newly scraped SQLite scholarships over JSON!")
    app.run(port=5001)
