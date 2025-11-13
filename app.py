# app.py - versão final completa (2025)
from flask import Flask, render_template, request, redirect, session, url_for, flash
import csv, os, datetime

app = Flask(__name__)
app.secret_key = "terravermelha2025"

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ==========================================================
# FUNÇÕES AUXILIARES DE CSV
# ==========================================================
def caminho_csv(nome):
    return os.path.join(DATA_DIR, nome)

def inicializar_csv(nome_arquivo, cabecalho):
    caminho = caminho_csv(nome_arquivo)
    if not os.path.isfile(caminho):
        with open(caminho, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=cabecalho).writeheader()

def salvar_csv(nome_arquivo, dados, cabecalho):
    caminho = caminho_csv(nome_arquivo)
    precisa = not os.path.isfile(caminho) or os.stat(caminho).st_size == 0
    with open(caminho, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cabecalho)
        if precisa:
            writer.writeheader()
        writer.writerow(dados)

def ler_csv(nome_arquivo):
    caminho = caminho_csv(nome_arquivo)
    if not os.path.isfile(caminho) or os.stat(caminho).st_size == 0:
        return []
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# ==========================================================
# INICIALIZAÇÃO DOS ARQUIVOS CSV
# ==========================================================
inicializar_csv("usuarios.csv", ["id","nome","email","senha","perfil"])
inicializar_csv("alunos.csv", ["id","nome","email","curso_id"])
inicializar_csv("cursos.csv", ["id","nome_curso","descricao"])
inicializar_csv("disciplinas.csv", ["id","nome","curso_id"])
inicializar_csv("conteudos.csv", ["id","titulo","descricao","id_disciplina"])
inicializar_csv("notas.csv", ["id","aluno_id","disciplina_id","nota"])

# ==========================================================
# AJUSTE DE PERFIL
# ==========================================================
def normalizar_perfil(valor):
    v = (valor or "").strip().lower()
    mapa = {
        "masculino": "secretaria",
        "feminino": "professor",
        "outro": "aluno",
        "aluno": "aluno",
        "professor": "professor",
        "secretaria": "secretaria",
        "empresa": "empresa"
    }
    return mapa.get(v, v)

# ==========================================================
# ROTAS PÚBLICAS
# ==========================================================
@app.route("/")
def index():
    usuario = session.get("usuario")
    return render_template("index.html", usuario=usuario)

@app.route("/sobre")
def sobre():
    return render_template("sobre.html")

@app.route("/sobre_nos")
def sobre_nos():
    return render_template("sobre_nos.html")

# ==========================================================
# LOGIN E LOGOUT
# ==========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        senha = (request.form.get("senha") or "").strip()
        usuarios = ler_csv("usuarios.csv")
        for u in usuarios:
            if (u.get("email") or "").lower() == email and u.get("senha") == senha:
                perfil = (u.get("perfil") or "").lower()
                session["usuario"] = {"id": u.get("id"), "nome": u.get("nome"), "perfil": perfil, "email": email}
                flash("Login efetuado com sucesso!", "success")
                if perfil == "secretaria": return redirect("/secretaria")
                if perfil == "professor": return redirect("/professor")
                if perfil == "aluno": return redirect("/alunos")
                if perfil == "empresa": return redirect("/empresa")
                return redirect("/")
        flash("Usuário ou senha inválidos.", "error")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    flash("Você saiu da conta.", "info")
    return redirect(url_for("login"))

# ==========================================================
# CADASTRO PÚBLICO
# ==========================================================
@app.route("/usuarios", methods=["GET", "POST"])
def usuarios():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "").strip()
        repetir = request.form.get("repetir_senha", "").strip()
        perfil = normalizar_perfil(request.form.get("perfil", ""))

        if not nome or not email or not senha or not perfil:
            flash("Preencha todos os campos.", "error")
            return redirect(url_for("usuarios"))
        if senha != repetir:
            flash("As senhas não conferem.", "error")
            return redirect(url_for("usuarios"))

        usuarios_lista = ler_csv("usuarios.csv")
        if any(u["email"].lower() == email for u in usuarios_lista):
            flash("E-mail já cadastrado.", "error")
            return redirect(url_for("usuarios"))

        novo_id = str(len(usuarios_lista) + 1)
        salvar_csv("usuarios.csv", {"id": novo_id, "nome": nome, "email": email, "senha": senha, "perfil": perfil},
                   ["id", "nome", "email", "senha", "perfil"])
        if perfil == "aluno":
            salvar_csv("alunos.csv", {"id": novo_id, "nome": nome, "email": email, "curso_id": ""}, ["id", "nome", "email", "curso_id"])

        flash("Cadastro realizado com sucesso! Faça login.", "success")
        return redirect(url_for("login"))

    usuario_sess = session.get("usuario")
    registros = []
    if usuario_sess and usuario_sess.get("perfil") == "secretaria":
        registros = ler_csv("usuarios.csv")
    return render_template("usuarios.html", registros=registros, usuario=usuario_sess)

# ==========================================================
# DECORADOR DE LOGIN
# ==========================================================
def login_requerido(*perfis):
    def decorator(func):
        def wrapper(*args, **kwargs):
            usuario = session.get("usuario")
            if not usuario:
                flash("Faça login para acessar.", "error")
                return redirect(url_for("login"))
            if perfis and usuario.get("perfil") not in perfis:
                flash("Acesso negado: perfil incorreto.", "error")
                return redirect(url_for("login"))
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

# ==========================================================
# ROTAS DE SECRETARIA E PROFESSOR
# ==========================================================
@app.route("/secretaria")
@login_requerido("secretaria")
def secretaria():
    return render_template("secretaria.html", usuario=session.get("usuario"))

@app.route("/professor")
@login_requerido("professor")
def professor():
    return render_template("professor.html", usuario=session.get("usuario"))

@app.route("/cursos", methods=["GET", "POST"])
@login_requerido("secretaria", "professor")
def cursos():
    cursos = ler_csv("cursos.csv")
    if request.method == "POST":
        nome = request.form.get("nome_curso", "").strip()
        descricao = request.form.get("descricao", "").strip()
        if nome:
            salvar_csv("cursos.csv", {"id": str(len(cursos)+1), "nome_curso": nome, "descricao": descricao},
                       ["id", "nome_curso", "descricao"])
            flash("Curso cadastrado com sucesso.", "success")
            return redirect(url_for("cursos"))
    return render_template("cursos.html", cursos=cursos, usuario=session.get("usuario"))

@app.route("/disciplinas", methods=["GET", "POST"])
@login_requerido("secretaria", "professor")
def disciplinas():
    disciplinas = ler_csv("disciplinas.csv")
    cursos = ler_csv("cursos.csv")
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        curso_id = request.form.get("curso_id", "").strip()
        if nome:
            salvar_csv("disciplinas.csv", {"id": str(len(disciplinas)+1), "nome": nome, "curso_id": curso_id},
                       ["id", "nome", "curso_id"])
            flash("Disciplina cadastrada com sucesso.", "success")
            return redirect(url_for("disciplinas"))
    return render_template("disciplinas.html", disciplinas=disciplinas, cursos=cursos, usuario=session.get("usuario"))

@app.route("/conteudos", methods=["GET", "POST"])
@login_requerido("secretaria", "professor")
def conteudos():
    conteudos = ler_csv("conteudos.csv")
    disciplinas = ler_csv("disciplinas.csv")
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        id_disciplina = request.form.get("id_disciplina", "").strip()
        if titulo:
            salvar_csv("conteudos.csv", {"id": str(len(conteudos)+1), "titulo": titulo, "descricao": descricao, "id_disciplina": id_disciplina},
                       ["id", "titulo", "descricao", "id_disciplina"])
            flash("Conteúdo cadastrado com sucesso.", "success")
            return redirect(url_for("conteudos"))
    return render_template("conteudos.html", conteudos=conteudos, disciplinas=disciplinas, usuario=session.get("usuario"))

# ==========================================================
# ROTAS DE ALUNO E EMPRESA
# ==========================================================
@app.route("/alunos")
@login_requerido("aluno")
def alunos():
    alunos = ler_csv("alunos.csv")
    cursos = ler_csv("cursos.csv")
    conteudos = ler_csv("conteudos.csv")
    for a in alunos:
        a["curso_nome"] = next((c["nome_curso"] for c in cursos if c["id"] == a.get("curso_id")), "N/A")
    return render_template("aluno.html", alunos=alunos, cursos=cursos, conteudos=conteudos, usuario=session.get("usuario"))

@app.route("/empresa")
@login_requerido("empresa")
def empresa():
    cursos = ler_csv("cursos.csv")
    disciplinas = ler_csv("disciplinas.csv")
    notas = ler_csv("notas.csv")
    alunos = ler_csv("alunos.csv")

    ranking = {}
    for n in notas:
        aluno = next((a for a in alunos if a["id"] == n.get("aluno_id")), None)
        if aluno:
            nome = aluno["nome"]
            ranking[nome] = ranking.get(nome, 0) + float(n.get("nota") or 0)

    ranking_geral = sorted(ranking.items(), key=lambda x: x[1], reverse=True)
    return render_template("empresa.html", cursos=cursos, disciplinas=disciplinas, ranking_geral=ranking_geral, usuario=session.get("usuario"))

@app.route("/ranking")
@login_requerido("empresa")
def ranking():
    notas = ler_csv("notas.csv")
    alunos = ler_csv("alunos.csv")
    ranking = {}
    for n in notas:
        aluno = next((a for a in alunos if a["id"] == n.get("aluno_id")), None)
        if aluno:
            ranking[aluno["nome"]] = ranking.get(aluno["nome"], 0) + float(n.get("nota") or 0)
    ranking_geral = sorted(ranking.items(), key=lambda x: x[1], reverse=True)
    return render_template("ranking.html", ranking_geral=ranking_geral, usuario=session.get("usuario"))

# ==========================================================
if __name__ == "__main__":
    app.run(debug=True)
