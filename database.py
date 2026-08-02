import sqlite3
import json
import numpy as np

DB_NAME = "local_rag_knowledge.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            embedding TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def insert_chunk(content, embedding_vector):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO documents (content, embedding) VALUES (?, ?)', 
                   (content, json.dumps(embedding_vector)))
    conn.commit()
    conn.close()

def cosine_similarity(v1, v2):
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    # Sıfıra bölünme hatasını engellemek için güvenlik kontrolü
    if norm1 == 0 or norm2 == 0: 
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))

def get_top_chunks(query_embedding, top_k=3):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT content, embedding FROM documents')
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        content = row[0]
        doc_embedding = np.array(json.loads(row[1]))
        similarity = cosine_similarity(query_embedding, doc_embedding)
        results.append((similarity, content))
    
    # Skorları en yüksekten en düşüğe sırala
    results.sort(key=lambda x: x[0], reverse=True)
    # En iyi eşleşen parçaları döndür
    return [content for _, content in results[:top_k]]