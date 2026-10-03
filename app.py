import sqlite3
from flask import Flask, render_template, request, redirect

app = Flask(__name__, template_folder='.')

def init_db():
    conn = sqlite3.connect('estoque.db')
    cursor = conn.cursor()
    # Tabela de Itens atualizada com a coluna "codigo"
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            tipo TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            motivo TEXT,
            FOREIGN KEY (item_id) REFERENCES itens(id)
        )
    ''')
    # Cadastra itens iniciais de exemplo apenas se a tabela estiver completamente vazia
    cursor.execute("SELECT COUNT(*) FROM itens")
    if cursor.fetchone() == 0:
        cursor.executemany("INSERT INTO itens (codigo, nome, categoria) VALUES (?, ?, ?)", [
            ('EMB-001', 'Caixa de Papelão P', 'Embalagem'),
            ('EMB-002', 'Saco Plástico 1kg', 'Embalagem'),
            ('INS-001', 'Matéria-Prima A', 'Insumo')
        ])
    conn.commit()
    conn.close()

# Página Principal: Mostra estoque e formulários
@app.route('/')
def index():
    conn = sqlite3.connect('estoque.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, codigo, nome, categoria FROM itens")
    itens = cursor.fetchall()
    
    lista_estoque = []
    for item in itens:
        item_id, codigo, nome, categoria = item
        
        cursor.execute("SELECT SUM(quantidade) FROM movimentacoes WHERE item_id = ? AND tipo = 'Entrada'", (item_id,))
        entradas = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(quantidade) FROM movimentacoes WHERE item_id = ? AND tipo = 'Saída'", (item_id,))
        saidas = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(quantidade) FROM movimentacoes WHERE item_id = ? AND tipo = 'Perda'", (item_id,))
        perdas = cursor.fetchone()[0] or 0
        
        atual = entradas - saidas - perdas
        
        lista_estoque.append({
            'id': item_id,
            'codigo': codigo,
            'nome': nome,
            'categoria': categoria,
            'atual': atual,
            'perdas': perdas
        })
        
    conn.close()
    return render_template('index.html', itens=lista_estoque, item_editar=None)

# Rota para CADASTRAR um novo item (Embalagem ou Insumo)
@app.route('/cadastrar-item', methods=['POST'])
def cadastrar_item():
    codigo = request.form['codigo'].strip().upper()
    nome = request.form['nome'].strip()
    categoria = request.form['categoria']

    conn = sqlite3.connect('estoque.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO itens (codigo, nome, categoria) VALUES (?, ?, ?)", (codigo, nome, categoria))
        conn.commit()
    except sqlite3.IntegrityError:
        # Ignora se o código já existir para não travar o app
        pass
    finally:
        conn.close()
    return redirect('/')

# Rota que abre a página principal em "modo de edição" para um item específico
@app.route('/editar-item/<int:item_id>')
def editar_item(item_id):
    conn = sqlite3.connect('estoque.db')
    cursor = conn.cursor()
    
    # Busca os dados do item que será editado
    cursor.execute("SELECT id, codigo, nome, categoria FROM itens WHERE id = ?", (item_id,))
    item_editar = cursor.fetchone()
    
    # Recarrega a lista do estoque normalmente
    cursor.execute("SELECT id, codigo, nome, categoria FROM itens")
    itens = cursor.fetchall()
    
    lista_estoque = []
    for item in itens:
        i_id, codigo, nome, categoria = item
        entradas = cursor.execute("SELECT SUM(quantidade) FROM movimentacoes WHERE item_id = ? AND tipo = 'Entrada'", (i_id,)).fetchone()[0] or 0
        saidas = cursor.execute("SELECT SUM(quantidade) FROM movimentacoes WHERE item_id = ? AND tipo = 'Saída'", (i_id,)).fetchone()[0] or 0
        perdas = cursor.execute("SELECT SUM(quantidade) FROM movimentacoes WHERE item_id = ? AND tipo = 'Perda'", (i_id,)).fetchone()[0] or 0
        lista_estoque.append({
            'id': i_id, 'codigo': codigo, 'nome': nome, 'categoria': categoria, 'atual': (entradas - saidas - perdas), 'perdas': perdas
        })
        
    conn.close()
    return render_template('index.html', itens=lista_estoque, item_editar=item_editar)

# Rota para SALVAR as alterações do item editado
@app.route('/salvar-edicao', methods=['POST'])
def salvar_edicao():
    item_id = request.form['id']
    codigo = request.form['codigo'].strip().upper()
    nome = request.form['nome'].strip()
    categoria = request.form['categoria']

    conn = sqlite3.connect('estoque.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE itens SET codigo = ?, nome = ?, categoria = ? WHERE id = ?", (codigo, nome, categoria, item_id))
    conn.commit()
    conn.close()
    return redirect('/')

# Rota para registrar movimentações (Entrada/Saída/Perda)
@app.route('/registrar', methods=['POST'])
def registrar():
    item_id = request.form['item_id']
    tipo = request.form['tipo']
    quantidade = int(request.form['quantidade'])

    conn = sqlite3.connect('estoque.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO movimentacoes (item_id, tipo, quantidade) VALUES (?, ?, ?)", (item_id, tipo, quantidade))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
