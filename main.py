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

# KREAM 스타일 공통 레이아웃 + 저작권 면책 조항 추가
def layout(title: str, content: str, current_user: Optional[str] = None):
    nav = f"""
    <nav class="sticky top-0 z-50 bg-white border-b border-gray-200">
        <div class="max-w-6xl mx-auto px-6 h-16 flex justify-between items-center">
            <a href="/" class="text-lg font-black tracking-tighter text-black uppercase">K-POKEMON</a>
            <div class="flex items-center space-x-6 text-sm font-medium text-gray-700">
                {f'<span class="text-black font-semibold">{current_user}님</span> <a href="/write" class="bg-black text-white px-4 py-2 rounded-md hover:bg-gray-800 transition">새 카드 등록</a> <a href="/logout" class="text-gray-400 hover:text-black transition">로그아웃</a>' if current_user else '<a href="/login" class="hover:text-black transition">로그인</a> <a href="/signup" class="bg-black text-white px-4 py-2 rounded-md hover:bg-gray-800 transition">회원가입</a>'}
            </div>
        </div>
    </nav>
    """
    
    footer = """
    <footer class="border-t border-gray-200 py-10 mt-12 bg-gray-50">
        <div class="max-w-6xl mx-auto px-6 text-center">
            <p class="text-xs font-black text-gray-600 mb-2 uppercase tracking-widest">Disclaimer</p>
            <p class="text-xs text-gray-400 mb-4 leading-relaxed">
                본 사이트는 포켓몬 카드 수집가들을 위한 개인 간 중고 거래 플랫폼입니다.<br>
                본 서비스는 (주)포켓몬코리아, Nintendo, Creatures, GAME FREAK 등 공식 권리자와 어떠한 제휴 및 관련도 없음을 명시합니다.<br>
                등록된 모든 상품의 거래 책임은 거래 당사자에게 있습니다.
            </p>
            <p class="text-xs text-gray-300">&copy; 2026 POKEMON TRADE MARKET. All Rights Reserved.</p>
        </div>
    </footer>
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
    <body class="bg-white text-black font-sans antialiased min-h-screen flex flex-col justify-between">
        <div>
            {nav}
            <main class="max-w-6xl mx-auto px-6 py-10">
                {content}
            </main>
        </div>
        {footer}
    </body>
    </html>
    """

@app.get("/signup", response_class=HTMLResponse)
def signup_page():
    content = """
    <div class="max-w-md mx-auto py-12">
        <div class="text-center mb-8">
            <h2 class="text-2xl font-black tracking-tight">JOIN</h2>
            <p class="text-sm text-gray-500 mt-1">포켓몬 마켓 멤버가 되어보세요.</p>
        </div>
        <form action="/signup" method="post" class="space-y-4">
            <div>
                <label class="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">Username</label>
                <input type="text" name="username" required class="w-full h-12 px-4 border border-gray-300 rounded-lg focus:border-black focus:outline-none transition">
            </div>
            <div>
                <label class="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">Password</label>
                <input type="password" name="password" required class="w-full h-12 px-4 border border-gray-300 rounded-lg focus:border-black focus:outline-none transition">
            </div>
            <button type="submit" class="w-full h-12 bg-black text-white font-bold rounded-lg hover:bg-gray-800 transition mt-2">가입하기</button>
        </form>
        <div class="mt-6 text-center text-xs text-gray-500">
            이미 계정이 있으신가요? <a href="/login" class="text-black font-bold underline">로그인</a>
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
    <div class="max-w-md mx-auto py-12">
        <div class="text-center mb-8">
            <h2 class="text-2xl font-black tracking-tight">LOGIN</h2>
            <p class="text-sm text-gray-500 mt-1">로그인하여 거래를 시작하세요.</p>
        </div>
        <form action="/login" method="post" class="space-y-4">
            <div>
                <label class="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">Username</label>
                <input type="text" name="username" required class="w-full h-12 px-4 border border-gray-300 rounded-lg focus:border-black focus:outline-none transition">
            </div>
            <div>
                <label class="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">Password</label>
                <input type="password" name="password" required class="w-full h-12 px-4 border border-gray-300 rounded-lg focus:border-black focus:outline-none transition">
            </div>
            <button type="submit" class="w-full h-12 bg-black text-white font-bold rounded-lg hover:bg-gray-800 transition mt-2">로그인</button>
        </form>
        <div class="mt-6 text-center text-xs text-gray-500">
            계정이 없으신가요? <a href="/signup" class="text-black font-bold underline">회원가입</a>
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
        img_tag = f"<img src='/{img}' class='w-full h-64 object-cover bg-gray-50 group-hover:scale-105 transition duration-300'>" if img else "<div class='w-full h-64 bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-400'>NO IMAGE</div>"

        posts_html += f"""
        <a href="/post/{pid}" class="group block bg-white border border-gray-200 rounded-xl overflow-hidden hover:border-black transition">
            <div class="overflow-hidden">
                {img_tag}
            </div>
            <div class="p-4">
                <div class="flex items-center justify-between text-xs text-gray-400 mb-1">
                    <span class="font-bold text-black uppercase tracking-wider">{attr}</span>
                    <span>{author}</span>
                </div>
                <h3 class="font-bold text-sm text-gray-900 truncate mb-2">{title}</h3>
                <div class="pt-2 border-t border-gray-100 flex justify-between items-center">
                    <span class="text-xs text-gray-500">{p_name}</span>
                    <span class="font-black text-base text-black">{price}</span>
                </div>
            </div>
        </a>
        """
        
    content = f"""
    <!-- 검색 및 필터 영역 -->
    <div class="mb-10">
        <form method="get" action="/" class="flex gap-2 max-w-2xl mx-auto">
            <input type="text" name="q" placeholder="브랜드, 모델, 포켓몬 이름 검색" value="{q if q else ''}" class="flex-1 h-12 px-4 border border-gray-300 rounded-lg text-sm focus:border-black focus:outline-none transition">
            <select name="attribute" class="h-12 px-4 border border-gray-300 rounded-lg text-sm bg-white focus:border-black focus:outline-none transition">
                <option value="전체">모든 속성</option>
                <option value="불꽃" {'selected' if attribute=='불꽃' else ''}>불꽃</option>
                <option value="물" {'selected' if attribute=='물' else ''}>물</option>
                <option value="풀" {'selected' if attribute=='풀' else ''}>풀</option>
                <option value="전기" {'selected' if attribute=='전기' else ''}>전기</option>
                <option value="무색" {'selected' if attribute=='무색' else ''}>무색</option>
            </select>
            <button type="submit" class="h-12 px-6 bg-black text-white text-sm font-bold rounded-lg hover:bg-gray-800 transition">검색</button>
        </form>
    </div>

    <!-- 카드 리스트 그리드 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
        {posts_html if posts_html else "<div class='col-span-full py-24 text-center text-gray-400 text-sm'>등록된 상품이 없습니다.</div>"}
    </div>
    """
    return layout("POKEMON MARKET", content, current_user)

@app.get("/write", response_class=HTMLResponse)
def write_page(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
    content = """
    <div class="max-w-xl mx-auto py-10">
        <h2 class="text-2xl font-black tracking-tight mb-8 text-center">NEW PRODUCT</h2>
        <form action="/write" method="post" enctype="multipart/form-data" class="space-y-6">
            <div>
                <label class="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">상품 제목</label>
                <input type="text" name="title" required placeholder="예: [미사용] 리자몽 VMAX 레어 카드" class="w-full h-12 px-4 border border-gray-300 rounded-lg focus:border-black focus:outline-none transition">
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">포켓몬 이름</label>
                    <input type="text" name="pokemon_name" required placeholder="예: 리자몽" class="w-full h-12 px-4 border border-gray-300 rounded-lg focus:border-black focus:outline-none transition">
                </div>
                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">속성</label>
                    <select name="attribute" class="w-full h-12 px-4 border border-gray-300 rounded-lg bg-white focus:border-black focus:outline-none transition">
                        <option value="불꽃">불꽃</option>
                        <option value="물">물</option>
                        <option value="풀">풀</option>
                        <option value="전기">전기</option>
                        <option value="무색">무색</option>
                    </select>
                </div>
            </div>
            <div>
                <label class="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">가격 또는 교환 조건</label>
                <input type="text" name="price" required placeholder="예: 45,000원 또는 피카츄 카드와 교환" class="w-full h-12 px-4 border border-gray-300 rounded-lg focus:border-black focus:outline-none transition">
            </div>
            
            <!-- 사진 업로드 주의사항 추가 -->
            <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <label class="block text-xs font-bold uppercase tracking-wider text-black mb-2">상품 이미지 등록</label>
                <input type="file" name="file" class="w-full py-2 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-bold file:bg-black file:text-white hover:file:bg-gray-800 transition mb-3">
                <p class="text-xs text-red-500 font-bold leading-relaxed">
                    🚨 주의: 저작권 보호를 위해 반드시 본인이 직접 촬영한 '실물 카드 사진'만 업로드해 주세요.<br>
                    (인터넷에 있는 공식 일러스트 캡처본 등은 무단 도용으로 간주되어 삭제될 수 있습니다.)
                </p>
            </div>

            <div class="flex gap-4 pt-4">
                <a href="/" class="flex-1 h-12 flex items-center justify-center border border-gray-300 text-black font-bold rounded-lg hover:bg-gray-50 transition">취소</a>
                <button type="submit" class="flex-1 h-12 bg-black text-white font-bold rounded-lg hover:bg-gray-800 transition">등록하기</button>
            </div>
        </form>
    </div>
    """
    return layout("상품 등록", content, current_user)

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
    img_tag = f"<img src='/{img}' class='w-full max-h-[500px] object-contain bg-gray-50 rounded-xl mb-6'>" if img else ""
    
    comments_html = ""
    for c_user, content in comments:
        comments_html += f"""
        <div class="py-3 border-b border-gray-100 flex justify-between items-center text-sm">
            <div>
                <span class="font-bold text-black mr-2">{c_user}</span>
                <span class="text-gray-700">{content}</span>
            </div>
        </div>
        """
        
    comment_form = ""
    if current_user:
        comment_form = f"""
        <form action="/post/{pid}/comment" method="post" class="flex gap-2 mt-6">
            <input type="text" name="content" placeholder="거래 제안이나 댓글을 입력하세요" required class="flex-1 h-12 px-4 border border-gray-300 rounded-lg text-sm focus:border-black focus:outline-none transition">
            <button type="submit" class="h-12 px-6 bg-black text-white text-sm font-bold rounded-lg hover:bg-gray-800 transition">등록</button>
        </form>
        """
    else:
        comment_form = "<div class='py-4 text-center bg-gray-50 rounded-lg text-xs text-gray-500'>댓글을 작성하려면 <a href='/login' class='underline font-bold text-black'>로그인</a>이 필요합니다.</div>"
        
    content = f"""
    <div class="max-w-3xl mx-auto py-10">
        <a href="/" class="text-xs font-bold text-gray-400 hover:text-black transition mb-6 inline-block">&larr; BACK TO LIST</a>
        {img_tag}
        <div class="border-b border-gray-200 pb-6 mb-6">
            <div class="flex justify-between items-center mb-2">
                <span class="text-xs font-bold text-black uppercase tracking-wider">{attr}</span>
                <span class="text-xs text-gray-400">SELLER: {author}</span>
            </div>
            <h1 class="text-2xl font-black text-black mb-4">{title}</h1>
            <div class="flex justify-between items-center bg-gray-50 p-4 rounded-xl">
                <span class="text-xs text-gray-500 font-medium">포켓몬: {p_name}</span>
                <span class="text-2xl font-black text-black">{price}</span>
            </div>
        </div>

        <div>
            <h3 class="font-bold text-base mb-4">💬 거래 제안 및 문의</h3>
            <div class="divide-y divide-gray-100 mb-4">
                {comments_html if comments_html else "<div class='py-8 text-center text-gray-400 text-xs'>작성된 댓글이 없습니다.</div>"}
            </div>
            {comment_form}
        </div>
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