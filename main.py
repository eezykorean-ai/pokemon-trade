from fastapi import FastAPI, Form, File, UploadFile, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import os
import shutil
from typing import Optional

app = FastAPI()

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

def init_db():
    conn = sqlite3.connect("pokemon_trade.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
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

def get_current_user(request: Request) -> Optional[str]:
    return request.cookies.get("username")

# 공통 레이아웃 템플릿 함수 (Tailwind CSS 적용)
def layout(title: str, content: str, current_user: Optional[str] = None):
    nav = f"""
    <nav class="bg-indigo-600 text-white shadow-md">
        <div class="max-w-4xl mx-auto px-4 py-3 flex justify-between items-center">
            <a href="/" class="text-xl font-bold tracking-tight">⚡ 포켓몬 카드 마켓</a>
            <div class="space-x-4">
                {f'<span class="font-medium">{current_user}님</span> <a href="/write" class="bg-indigo-500 hover:bg-indigo-400 px-3 py-1.5 rounded-lg text-sm font-semibold transition">카드 등록</a> <a href="/logout" class="bg-rose-500 hover:bg-rose-600 px-3 py-1.5 rounded-lg text-sm font-semibold transition">로그아웃</a>' if current_user else '<a href="/login" class="hover:underline">로그인</a> <a href="/signup" class="bg-indigo-500 hover:bg-indigo-400 px-3 py-1.5 rounded-lg text-sm font-semibold transition">회원가입</a>'}
            </div>
        </div>
    </nav>
    """
    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 text-gray-800 min-h-screen">
        {nav}
        <main class="max-w-4xl mx-auto px-4 py-8">
            {content}
        </main>
    </body>
    </html>
    """

@app.get("/signup", response_class=HTMLResponse)
def signup_page():
    content = """
    <div class="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
        <h2 class="text-2xl font-bold mb-6 text-center text-gray-900">회원가입</h2>
        <form action="/signup" method="post" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">아이디</label>
                <input type="text" name="username" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
                <input type="password" name="password" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none">
            </div>
            <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 rounded-lg transition">가입하기</button>
        </form>
        <div class="mt-4 text-center text-sm text-gray-500">
            이미 계정이 있으신가요? <a href="/login" class="text-indigo-600 hover:underline font-medium">로그인</a>
        </div>
    </div>
    """
    return layout("회원가입", content)

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
    content = """
    <div class="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
        <h2 class="text-2xl font-bold mb-6 text-center text-gray-900">로그인</h2>
        <form action="/login" method="post" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">아이디</label>
                <input type="text" name="username" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
                <input type="password" name="password" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none">
            </div>
            <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 rounded-lg transition">로그인</button>
        </form>
        <div class="mt-4 text-center text-sm text-gray-500">
            계정이 없으신가요? <a href="/signup" class="text-indigo-600 hover:underline font-medium">회원가입</a>
        </div>
    </div>
    """
    return layout("로그인", content)

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
    
    posts_html = ""
    for post in posts:
        pid, title, p_name, attr, price, img, author = post
        img_tag = f"<img src='/{img}' class='w-full h-48 object-cover rounded-lg mb-3'>" if img else "<div class='w-full h-48 bg-gray-100 rounded-lg mb-3 flex items-center justify-center text-gray-400 font-medium'>이미지 없음</div>"
        
        # 속성별 배지 컬러 설정
        attr_colors = {"불꽃": "bg-red-100 text-red-600", "물": "bg-blue-100 text-blue-600", "풀": "bg-green-100 text-green-600", "전기": "bg-yellow-100 text-yellow-700", "무색": "bg-gray-100 text-gray-600"}
        badge_class = attr_colors.get(attr, "bg-gray-100 text-gray-650")

        posts_html += f"""
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 hover:shadow-md transition flex flex-col justify-between">
            <div>
                {img_tag}
                <div class="flex items-center justify-between mb-1">
                    <span class="text-xs font-semibold px-2.5 py-0.5 rounded-full {badge_class}">{attr}</span>
                    <span class="text-xs text-gray-400">{author}</span>
                </div>
                <h3 class="font-bold text-lg mb-1 text-gray-900 truncate"><a href="/post/{pid}" class="hover:text-indigo-600">{title}</a></h3>
                <p class="text-sm text-gray-600 mb-2">포켓몬: <span class="font-medium text-gray-900">{p_name}</span></p>
            </div>
            <div class="pt-3 border-t border-gray-100 flex justify-between items-center">
                <span class="font-bold text-indigo-600">{price}</span>
                <a href="/post/{pid}" class="text-xs bg-gray-100 hover:bg-indigo-50 text-gray-700 hover:text-indigo-600 font-medium px-3 py-1.5 rounded-lg transition">자세히 보기</a>
            </div>
        </div>
        """
        
    content = f"""
    <!-- 검색 및 필터 바 -->
    <form method="get" action="/" class="bg-white p-4 rounded-xl shadow-sm border border-gray-100 mb-6 flex flex-col sm:flex-row gap-3">
        <input type="text" name="q" placeholder="포켓몬 이름 또는 제목 검색" value="{q if q else ''}" class="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none">
        <select name="attribute" class="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white">
            <option value="전체">전체 속성</option>
            <option value="불꽃" {'selected' if attribute=='불꽃' else ''}>불꽃</option>
            <option value="물" {'selected' if attribute=='물' else ''}>물</option>
            <option value="풀" {'selected' if attribute=='풀' else ''}>풀</option>
            <option value="전기" {'selected' if attribute=='전기' else ''}>전기</option>
            <option value="무색" {'selected' if attribute=='무색' else ''}>무색</option>
        </select>
        <button type="submit" class="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-2 rounded-lg transition">검색</button>
    </form>

    <h2 class="text-xl font-bold text-gray-900 mb-4">등록된 카드 목록</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {posts_html if posts_html else "<div class='col-span-full text-center py-12 text-gray-400 bg-white rounded-xl border border-gray-100'>등록된 카드가 없습니다.</div>"}
    </div>
    """
    return layout("포켓몬 카드 마켓", content, current_user)

@app.get("/write", response_class=HTMLResponse)
def write_page(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
    content = """
    <div class="max-w-lg mx-auto bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
        <h2 class="text-2xl font-bold mb-6 text-gray-900">포켓몬 카드 등록</h2>
        <form action="/write" method="post" enctype="multipart/form-data" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">글 제목</label>
                <input type="text" name="title" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">포켓몬 이름</label>
                <input type="text" name="pokemon_name" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">속성</label>
                <select name="attribute" class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white">
                    <option value="불꽃">불꽃</option>
                    <option value="물">물</option>
                    <option value="풀">풀</option>
                    <option value="전기">전기</option>
                    <option value="무색">무색</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">가격 및 교환 조건</label>
                <input type="text" name="price" required class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">카드 사진</label>
                <input type="file" name="file" class="w-full px-3 py-2 border rounded-lg file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100">
            </div>
            <div class="pt-4 flex gap-3">
                <a href="/" class="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold py-2 rounded-lg text-center transition">취소</a>
                <button type="submit" class="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 rounded-lg transition">등록하기</button>
            </div>
        </form>
    </div>
    """
    return layout("카드 등록", content, current_user)

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
    img_tag = f"<img src='/{img}' class='w-full max-h-96 object-contain rounded-xl mb-6 bg-gray-900'>" if img else ""
    
    comments_html = ""
    for c_user, content in comments:
        comments_html += f"""
        <div class="bg-gray-50 p-3 rounded-lg border border-gray-100">
            <span class="font-semibold text-gray-900 text-sm">{c_user}</span>
            <p class="text-gray-700 mt-1">{content}</p>
        </div>
        """
        
    comment_form = ""
    if current_user:
        comment_form = f"""
        <form action="/post/{pid}/comment" method="post" class="flex gap-2 mt-4">
            <input type="text" name="content" placeholder="거래 제안이나 댓글을 입력하세요" required class="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none">
            <button type="submit" class="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-5 py-2 rounded-lg transition">등록</button>
        </form>
        """
    else:
        comment_form = "<p class='text-sm text-gray-500 bg-gray-50 p-3 rounded-lg text-center'>댓글을 남기려면 <a href='/login' class='text-indigo-600 font-semibold hover:underline'>로그인</a>이 필요합니다.</p>"
        
    content = f"""
    <div class="max-w-2xl mx-auto bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
        <a href="/" class="inline-block text-sm text-indigo-600 font-semibold mb-6 hover:underline">← 목록으로 돌아가기</a>
        {img_tag}
        <div class="flex justify-between items-start mb-4">
            <div>
                <span class="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-600 mb-2 inline-block">{attr}</span>
                <h1 class="text-2xl font-bold text-gray-900">{title}</h1>
            </div>
            <span class="text-sm text-gray-400">작성자: {author}</span>
        </div>
        <div class="space-y-2 text-gray-700 bg-gray-50 p-4 rounded-xl mb-6">
            <p><b>포켓몬:</b> {p_name}</p>
            <p><b>가격/조건:</b> <span class="text-indigo-600 font-bold">{price}</span></p>
        </div>
        
        <hr class="my-6 border-gray-100">
        
        <h3 class="font-bold text-lg text-gray-900 mb-4">💬 거래 제안 및 댓글</h3>
        <div class="space-y-3 mb-6">
            {comments_html if comments_html else "<p class='text-sm text-gray-400 text-center py-4'>아직 댓글이 없습니다.</p>"}
        </div>
        {comment_form}
    </div>
    """
    return layout(title, content, current_user)

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
