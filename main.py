from fastapi import FastAPI, Form, File, UploadFile, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import os
import shutil
from typing import Optional

app = FastAPI()

# 정적 파일 및 업로드 폴더 설정
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 데이터베이스 초기화 (테이블 생성)
def init_db():
    conn = sqlite3.connect("pokemon_trade.db")
    cursor = conn.cursor()
    
    # 회원 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # 게시글 테이블 (이미지, 속성 추가)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            pokemon_name TEXT NOT NULL,
            attribute TEXT NOT NULL,
            price TEXT NOT NULL,
            image_url TEXT,
            username TEXT NOT NULL
        )
    """)
    
    # 댓글(거래 제안) 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# 간단한 로그인 상태 확인 (쿠키 기반)
def get_current_user(request: Request) -> Optional[str]:
    return request.cookies.get("username")

# --- 1. 회원가입 및 로그인 페이지 & 기능 ---
@app.get("/signup", response_class=HTMLResponse)
def signup_page():
    return """
    <h2>회원가입</h2>
    <form action="/signup" method="post">
        아이디: <input type="text" name="username" required><br>
        비밀번호: <input type="password" name="password" required><br>
        <button type="submit">가입하기</button>
    </form>
    <a href="/">홈으로</a>
    """

@app.post("/signup")
def signup(username: str = Form(...), password: str = Form(...)):
    try:
        conn = sqlite3.connect("pokemon_trade.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login", response_class=HTMLResponse)
def login_page():
    return """
    <h2>로그인</h2>
    <form action="/login" method="post">
        아이디: <input type="text" name="username" required><br>
        비밀번호: <input type="password" name="password" required><br>
        <button type="submit">로그인</button>
    </form>
    <a href="/signup">회원가입하기</a> | <a href="/">홈으로</a>
    """

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect("pokemon_trade.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=400, detail="아이디 또는 비밀번호가 틀렸습니다.")
    
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="username", value=username)
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="username")
    return response


# --- 2. 메인 페이지 (검색, 필터, 게시글 목록) ---
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, q: Optional[str] = None, attribute: Optional[str] = None):
    current_user = get_current_user(request)
    
    conn = sqlite3.connect("pokemon_trade.db")
    cursor = conn.cursor()
    
    query = "SELECT id, title, pokemon_name, attribute, price, image_url, username FROM posts WHERE 1=1"
    params = []
    
    if q:
        query += " AND (pokemon_name LIKE ? OR title LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%"])
    if attribute and attribute != "전체":
        query += " AND attribute = ?"
        params.append(attribute)
        
    cursor.execute(query, params)
    posts = cursor.fetchall()
    conn.close()
    
    # 상단 메뉴 구성
    user_menu = f"<b>{current_user}</b>님 환영합니다! | <a href='/logout'>로그아웃</a> | <a href='/write'>카드 등록하기</a>" if current_user else "<a href='/login'>로그인</a> | <a href='/signup'>회원가입</a>"
    
    posts_html = ""
    for post in posts:
        pid, title, p_name, attr, price, img, author = post
        img_tag = f"<img src='/{img}' width='100'><br>" if img else ""
        posts_html += f"""
        <div style="border:1px solid #ccc; margin:10px; padding:10px;">
            {img_tag}
            <h3><a href="/post/{pid}">{title}</a></h3>
            <p>포켓몬: {p_name} | 속성: {attr} | 가격: {price}</p>
            <small>작성자: {author}</small>
        </div>
        """
        
    return f"""
    <html>
    <head><title>포켓몬 카드 마켓</title></head>
    <body style="font-family:sans-serif; padding:20px;">
        <h1>🔥 포켓몬 카드 거래 마켓</h1>
        <div>{user_menu}</div>
        <hr>
        
        <!-- 검색 및 필터 폼 -->
        <form method="get" action="/">
            <input type="text" name="q" placeholder="포켓몬 이름 또는 제목 검색" value="{q if q else ''}">
            <select name="attribute">
                <option value="전체">전체 속성</option>
                <option value="불꽃" {'selected' if attribute=='불꽃' else ''}>불꽃</option>
                <option value="물" {'selected' if attribute=='물' else ''}>물</option>
                <option value="풀" {'selected' if attribute=='풀' else ''}>풀</option>
                <option value="전기" {'selected' if attribute=='전기' else ''}>전기</option>
                <option value="무색" {'selected' if attribute=='무색' else ''}>무색</option>
            </select>
            <button type="submit">검색</button>
        </form>
        <hr>
        
        <h2>등록된 카드 목록</h2>
        {posts_html if posts_html else "<p>등록된 카드가 없습니다.</p>"}
    </body>
    </html>
    """


# --- 3. 카드 등록 및 이미지 업로드 ---
@app.get("/write", response_class=HTMLResponse)
def write_page(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
    return """
    <h2>포켓몬 카드 등록</h2>
    <form action="/write" method="post" enctype="multipart/form-data">
        글 제목: <input type="text" name="title" required><br>
        포켓몬 이름: <input type="text" name="pokemon_name" required><br>
        속성: 
        <select name="attribute">
            <option value="불꽃">불꽃</option>
            <option value="물">물</option>
            <option value="풀">풀</option>
            <option value="전기">전기</option>
            <option value="무색">무색</option>
        </select><br>
        가격/교환조건: <input type="text" name="price" required><br>
        카드 사진: <input type="file" name="file"><br><br>
        <button type="submit">등록하기</button>
    </form>
    <a href="/">돌가기</a>
    """

@app.post("/write")
def write_post(
    request: Request,
    title: str = Form(...),
    pokemon_name: str = Form(...),
    attribute: str = Form(...),
    price: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
        
    image_url = None
    if file and file.filename:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        image_url = f"static/uploads/{file.filename}"
        
    conn = sqlite3.connect("pokemon_trade.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO posts (title, pokemon_name, attribute, price, image_url, username)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, pokemon_name, attribute, price, image_url, current_user))
    conn.commit()
    conn.close()
    
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


# --- 4. 상세 페이지 및 댓글(거래 제안) 기능 ---
@app.get("/post/{post_id}", response_class=HTMLResponse)
def post_detail(post_id: int, request: Request):
    current_user = get_current_user(request)
    
    conn = sqlite3.connect("pokemon_trade.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, pokemon_name, attribute, price, image_url, username FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    
    cursor.execute("SELECT username, content FROM comments WHERE post_id = ?", (post_id,))
    comments = cursor.fetchall()
    
    conn.close()
    
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
        
    pid, title, p_name, attr, price, img, author = post
    img_tag = f"<img src='/{img}' width='200'><br>" if img else ""
    
    comments_html = ""
    for c_user, content in comments:
        comments_html += f"<p><b>{c_user}</b>: {content}</p>"
        
    comment_form = ""
    if current_user:
        comment_form = f"""
        <form action="/post/{pid}/comment" method="post">
            <input type="text" name="content" placeholder="거래 제안이나 댓글을 입력하세요" required style="width:300px;">
            <button type="submit">등록</button>
        </form>
        """
    else:
        comment_form = "<p><a href='/login'>로그인</a>을 해야 댓글을 남길 수 있습니다.</p>"
        
    return f"""
    <html>
    <head><title>{title}</title></head>
    <body style="font-family:sans-serif; padding:20px;">
        <a href="/">← 홈으로</a>
        {img_tag}
        <h2>{title}</h2>
        <p><b>포켓몬:</b> {p_name}</p>
        <p><b>속성:</b> {attr}</p>
        <p><b>가격/조건:</b> {price}</p>
        <p><b>작성자:</b> {author}</p>
        <hr>
        <h3>💬 거래 제안 및 댓글</h3>
        {comments_html if comments_html else "<p>아직 댓글이 없습니다.</p>"}
        {comment_form}
    </body>
    </html>
    """

@app.post("/post/{post_id}/comment")
def add_comment(post_id: int, request: Request, content: str = Form(...)):
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
        
    conn = sqlite3.connect("pokemon_trade.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO comments (post_id, username, content) VALUES (?, ?, ?)", (post_id, current_user, content))
    conn.commit()
    conn.close()
    
    return RedirectResponse(url=f"/post/{post_id}", status_code=status.HTTP_303_SEE_OTHER)
