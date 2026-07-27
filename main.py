import os
import uuid
import bcrypt
from fastapi import FastAPI, Request, Form, Response, Cookie, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from supabase import create_client, Client

app = FastAPI()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 공통 레이아웃 템플릿
def layout(body_content: str, user: str = None):
    nav_auth = ""
    if user:
        nav_auth = f"""
            <span class="text-sm font-medium text-gray-700">안녕하세요, <b class="text-blue-600">{user}</b>님!</span>
            <a href="/mypage" class="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600">마이페이지</a>
            <a href="/write" class="px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-700 transition">새 교환 등록</a>
            <a href="/logout" class="px-3 py-2 text-sm text-gray-500 hover:text-gray-900">로그아웃</a>
        """
    else:
        nav_auth = """
            <a href="/login" class="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600">로그인</a>
            <a href="/signup" class="px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-700 transition">회원가입</a>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>포켓몬 카드 교환소</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen text-gray-800">
        <nav class="bg-white border-b border-gray-100 sticky top-0 z-50 shadow-sm">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                <a href="/" class="text-xl font-extrabold text-blue-600 tracking-tight flex items-center gap-1">⚡ 포켓몬 교환소</a>
                <div class="flex items-center space-x-3">
                    {nav_auth}
                </div>
            </div>
        </nav>
        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {body_content}
        </main>
    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
def index(user: str = Cookie(None), q: str = None, attribute: str = None):
    try:
        query = supabase.table("posts").select("*").order("created_at", desc=True)
        if attribute:
            query = query.eq("attribute", attribute)
        if q:
            query = query.ilike("pokemon_name", f"%{q}%")
        
        res = query.execute()
        posts = res.data if res.data else []
    except Exception:
        posts = []

    posts_html = ""
    if not posts:
        posts_html = """
        <div class="col-span-full text-center py-20 text-gray-400 bg-white rounded-2xl border border-gray-100 shadow-sm">
            조건에 맞는 교환 글이 없습니다.
        </div>
        """
    else:
        for post in posts:
            attr = post.get("attribute", "기타")
            if attr == "불꽃": badge_style = "bg-red-100 text-red-600 border-red-200"
            elif attr == "물": badge_style = "bg-blue-100 text-blue-600 border-blue-200"
            elif attr == "풀": badge_style = "bg-green-100 text-green-600 border-green-200"
            elif attr == "전기": badge_style = "bg-amber-100 text-amber-600 border-amber-200"
            else: badge_style = "bg-gray-100 text-gray-600 border-gray-200"

            status = post.get("status")
            if status == "completed":
                status_badge = '<span class="px-2.5 py-1 text-xs font-semibold bg-gray-900 text-white rounded-full shadow-sm">교환완료</span>'
                card_opacity = "opacity-60 grayscale-[30%]"
            else:
                status_badge = '<span class="px-2.5 py-1 text-xs font-semibold bg-emerald-500 text-white rounded-full shadow-sm">교환대기</span>'
                card_opacity = ""

            img_url = post.get("image_url")
            img_tag = f'<img src="{img_url}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500">' if img_url else '<div class="w-full h-full flex items-center justify-center text-gray-400 text-sm bg-gray-100">이미지 없음</div>'

            posts_html += f"""
            <a href="/posts/{post.get('id')}" class="group bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden flex flex-col {card_opacity}">
                <div class="relative w-full h-56 bg-gray-50 overflow-hidden">
                    {img_tag}
                    <div class="absolute top-3 left-3">{status_badge}</div>
                    <div class="absolute top-3 right-3">
                        <span class="px-2.5 py-1 text-xs font-semibold rounded-full shadow-sm border {badge_style}">{attr}</span>
                    </div>
                </div>
                <div class="p-5 flex flex-col flex-grow justify-between">
                    <div>
                        <h3 class="font-bold text-gray-900 text-lg group-hover:text-blue-600 transition-colors truncate">{post.get('title')}</h3>
                        <p class="text-sm text-gray-500 mt-1 truncate">포켓몬: <span class="text-gray-700 font-medium">{post.get('pokemon_name')}</span></p>
                    </div>
                    <div class="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between">
                        <span class="text-xs text-gray-400">희망 교환</span>
                        <span class="text-sm font-bold text-gray-900 truncate max-w-[140px]">{post.get('trade_condition')}</span>
                    </div>
                </div>
            </a>
            """

    content = f"""
    <div class="mb-8 flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        <div>
            <h1 class="text-2xl font-extrabold text-gray-900">포켓몬 카드 교환소</h1>
            <p class="text-sm text-gray-500 mt-1">원하는 포켓몬을 안전하고 간편하게 교환해 보세요.</p>
        </div>
        <form action="/" method="get" class="flex gap-2 w-full md:w-auto">
            <select name="attribute" class="px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 text-sm outline-none">
                <option value="">모든 속성</option>
                <option value="불꽃" {'selected' if attribute=='불꽃' else ''}>불꽃</option>
                <option value="물" {'selected' if attribute=='물' else ''}>물</option>
                <option value="풀" {'selected' if attribute=='풀' else ''}>풀</option>
                <option value="전기" {'selected' if attribute=='전기' else ''}>전기</option>
                <option value="기타" {'selected' if attribute=='기타' else ''}>기타</option>
            </select>
            <input type="text" name="q" value="{q if q else ''}" placeholder="포켓몬 검색..." class="px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 text-sm outline-none flex-grow md:w-48">
            <button type="submit" class="px-4 py-2 bg-gray-900 text-white font-semibold rounded-xl hover:bg-gray-800 transition text-sm">검색</button>
        </form>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {posts_html}
    </div>
    """
    return HTMLResponse(layout(content, user))

@app.get("/login", response_class=HTMLResponse)
def login_page():
    content = """
    <div class="max-w-md mx-auto bg-white p-8 rounded-2xl border border-gray-100 shadow-sm">
        <h2 class="text-2xl font-bold text-gray-900 mb-6 text-center">로그인</h2>
        <form action="/login" method="post" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">아이디</label>
                <input type="text" name="username" required class="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
                <input type="password" name="password" required class="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none">
            </div>
            <button type="submit" class="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition">로그인</button>
        </form>
    </div>
    """
    return HTMLResponse(layout(content))

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    res = supabase.table("users").select("*").eq("username", username).execute()
    if res.data:
        user_data = res.data[0]
        # 입력된 비밀번호와 DB에 저장된 암호화된 비밀번호 비교
        try:
            if bcrypt.checkpw(password.encode('utf-8'), user_data['password'].encode('utf-8')):
                response = RedirectResponse(url="/", status_code=303)
                response.set_cookie(key="user", value=username, max_age=2592000)
                return response
        except ValueError:
            pass # 암호화되지 않은 기존 비밀번호 로그인 방지
    return RedirectResponse(url="/login", status_code=303)

@app.get("/signup", response_class=HTMLResponse)
def signup_page():
    content = """
    <div class="max-w-md mx-auto bg-white p-8 rounded-2xl border border-gray-100 shadow-sm">
        <h2 class="text-2xl font-bold text-gray-900 mb-6 text-center">회원가입</h2>
        <form action="/signup" method="post" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">아이디</label>
                <input type="text" name="username" required class="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
                <input type="password" name="password" required class="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none">
            </div>
            <button type="submit" class="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition">가입하기</button>
        </form>
    </div>
    """
    return HTMLResponse(layout(content))

@app.post("/signup")
def signup(username: str = Form(...), password: str = Form(...)):
    # 비밀번호 단방향 암호화 처리
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    supabase.table("users").insert({"username": username, "password": hashed_password}).execute()
    return RedirectResponse(url="/login", status_code=303)

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="user")
    return response

@app.get("/mypage", response_class=HTMLResponse)
def my_page(user: str = Cookie(None)):
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    res = supabase.table("posts").select("*").eq("author", user).order("created_at", desc=True).execute()
    my_posts = res.data if res.data else []

    posts_html = ""
    for post in my_posts:
        status_txt = "완료됨" if post.get("status") == "completed" else "대기중"
        posts_html += f"""
        <div class="flex items-center justify-between py-3 border-b border-gray-100">
            <div>
                <a href="/posts/{post.get('id')}" class="font-semibold text-gray-900 hover:text-blue-600">{post.get('title')}</a>
                <p class="text-sm text-gray-500 mt-1">포켓몬: {post.get('pokemon_name')} | 상태: {status_txt}</p>
            </div>
            <form action="/posts/{post.get('id')}/delete" method="post">
                <button type="submit" class="text-sm text-red-500 hover:underline">삭제</button>
            </form>
        </div>
        """
        
    content = f"""
    <div class="max-w-3xl mx-auto bg-white p-8 rounded-2xl border border-gray-100 shadow-sm">
        <h2 class="text-2xl font-bold text-gray-900 mb-6">👤 {user}님의 마이페이지</h2>
        <h3 class="text-lg font-bold text-gray-800 mb-4 pb-2 border-b-2 border-gray-900">내가 등록한 교환 글</h3>
        <div class="space-y-2">
            {posts_html if posts_html else '<p class="text-gray-400 text-sm py-4">등록한 교환 글이 없습니다.</p>'}
        </div>
    </div>
    """
    return HTMLResponse(layout(content, user))

@app.get("/write", response_class=HTMLResponse)
def write_page(user: str = Cookie(None)):
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    content = """
    <div class="max-w-xl mx-auto bg-white p-8 rounded-2xl border border-gray-100 shadow-sm">
        <h2 class="text-2xl font-bold text-gray-900 mb-6">새 교환 글 작성</h2>
        <form action="/write" method="post" enctype="multipart/form-data" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">제목</label>
                <input type="text" name="title" required class="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none">
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">포켓몬 이름</label>
                    <input type="text" name="pokemon_name" required class="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">속성</label>
                    <select name="attribute" class="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none">
                        <option value="불꽃">불꽃</option>
                        <option value="물">물</option>
                        <option value="풀">풀</option>
                        <option value="전기">전기</option>
                        <option value="기타">기타</option>
                    </select>
                </div>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">희망 교환 조건</label>
                <input type="text" name="trade_condition" required class="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">사진 업로드</label>
                <input type="file" name="file" class="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
            </div>
            <button type="submit" class="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition">등록하기</button>
        </form>
    </div>
    """
    return HTMLResponse(layout(content, user))

@app.post("/write")
def write_post(
    title: str = Form(...),
    pokemon_name: str = Form(...),
    attribute: str = Form(...),
    trade_condition: str = Form(...),
    file: UploadFile = File(None),
    user: str = Cookie(None)
):
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    image_url = None
    if file and file.filename:
        file_ext = file.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_bytes = file.file.read()
        supabase.storage.from_("images").upload(file_name, file_bytes, {"content-type": file.content_type})
        image_url = supabase.storage.from_("images").get_public_url(file_name)

    supabase.table("posts").insert({
        "title": title,
        "pokemon_name": pokemon_name,
        "attribute": attribute,
        "trade_condition": trade_condition,
        "image_url": image_url,
        "author": user,
        "status": "pending"
    }).execute()

    return RedirectResponse(url="/", status_code=303)

@app.get("/posts/{post_id}", response_class=HTMLResponse)
def post_detail(post_id: int, user: str = Cookie(None)):
    res = supabase.table("posts").select("*").eq("id", post_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Post not found")
    post = res.data[0]

    c_res = supabase.table("comments").select("*").eq("post_id", post_id).order("created_at", desc=False).execute()
    comments = c_res.data if c_res.data else []

    comments_html = ""
    for c in comments:
        del_btn = ""
        if user == c.get("author"):
            del_btn = f'''
            <form action="/comments/{c.get("id")}/delete" method="post" class="inline">
                <button type="submit" class="text-xs text-red-500 hover:underline">삭제</button>
            </form>
            '''
        comments_html += f"""
        <div class="py-3 border-b border-gray-100 flex justify-between items-center">
            <div>
                <span class="font-semibold text-sm text-gray-900">{c.get("author")}</span>
                <p class="text-gray-700 text-sm mt-1">{c.get("content")}</p>
            </div>
            {del_btn}
        </div>
        """

    post_actions = ""
    if user == post.get("author"):
        complete_btn = ""
        if post.get("status") != "completed":
            complete_btn = f"""
            <form action="/posts/{post_id}/complete" method="post" class="inline">
                <button type="submit" class="px-4 py-2 text-sm font-semibold text-white bg-emerald-500 rounded-xl hover:bg-emerald-600 transition shadow-sm">교환 완료하기</button>
            </form>
            """
        post_actions = f"""
        <div class="flex gap-2">
            {complete_btn}
            <form action="/posts/{post_id}/delete" method="post" class="inline">
                <button type="submit" class="px-4 py-2 text-sm font-semibold text-red-600 bg-red-50 rounded-xl hover:bg-red-100 transition">게시글 삭제</button>
            </form>
        </div>
        """

    content = f"""
    <div class="max-w-2xl mx-auto bg-white p-8 rounded-2xl border border-gray-100 shadow-sm space-y-6">
        <div class="flex justify-between items-start">
            <div>
                <span class="text-xs font-semibold px-2.5 py-1 bg-blue-50 text-blue-600 rounded-full">{post.get("attribute")}</span>
                <h1 class="text-2xl font-bold text-gray-900 mt-2">{post.get("title")}</h1>
                <p class="text-sm text-gray-500 mt-1">작성자: {post.get("author")}</p>
            </div>
            {post_actions}
        </div>
        
        {f'<div class="w-full h-80 bg-gray-50 rounded-xl overflow-hidden"><img src="{post.get("image_url")}" class="w-full h-full object-cover"></div>' if post.get("image_url") else ''}
        
        <div class="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-xl text-sm">
            <div><span class="text-gray-400">포켓몬:</span> <span class="font-medium">{post.get("pokemon_name")}</span></div>
            <div><span class="text-gray-400">희망 조건:</span> <span class="font-medium">{post.get("trade_condition")}</span></div>
        </div>

        <div class="border-t border-gray-100 pt-6">
            <h3 class="font-bold text-gray-900 mb-4">댓글</h3>
            <div class="space-y-2 mb-6">
                {comments_html if comments_html else '<p class="text-sm text-gray-400">작성된 댓글이 없습니다.</p>'}
            </div>
            
            {f'''
            <form action="/posts/{post_id}/comments" method="post" class="flex gap-2">
                <input type="text" name="content" placeholder="댓글을 입력하세요..." required class="flex-grow px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm">
                <button type="submit" class="px-5 py-2 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition text-sm">등록</button>
            </form>
            ''' if user else '<p class="text-sm text-gray-400 text-center py-2 bg-gray-50 rounded-xl">댓글을 작성하려면 로그인이 필요합니다.</p>'}
        </div>
        <div class="pt-4">
            <a href="/" class="text-sm font-medium text-blue-600 hover:underline">&larr; 목록으로 돌아가기</a>
        </div>
    </div>
    """
    return HTMLResponse(layout(content, user))

@app.post("/posts/{post_id}/complete")
def complete_post(post_id: int, user: str = Cookie(None)):
    res = supabase.table("posts").select("author").eq("id", post_id).execute()
    if res.data and res.data[0].get("author") == user:
        supabase.table("posts").update({"status": "completed"}).eq("id", post_id).execute()
    return RedirectResponse(url=f"/posts/{post_id}", status_code=303)

@app.post("/posts/{post_id}/comments")
def add_comment(post_id: int, content: str = Form(...), user: str = Cookie(None)):
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    supabase.table("comments").insert({
        "post_id": post_id,
        "content": content,
        "author": user
    }).execute()
    return RedirectResponse(url=f"/posts/{post_id}", status_code=303)

@app.post("/posts/{post_id}/delete")
def delete_post(post_id: int, user: str = Cookie(None)):
    res = supabase.table("posts").select("author").eq("id", post_id).execute()
    if res.data and res.data[0].get("author") == user:
        supabase.table("posts").delete().eq("id", post_id).execute()
    return RedirectResponse(url="/", status_code=303)

@app.post("/comments/{comment_id}/delete")
def delete_comment(comment_id: int, user: str = Cookie(None)):
    res = supabase.table("comments").select("post_id, author").eq("id", comment_id).execute()
    if res.data:
        comment = res.data[0]
        if comment.get("author") == user:
            post_id = comment.get("post_id")
            supabase.table("comments").delete().eq("id", comment_id).execute()
            return RedirectResponse(url=f"/posts/{post_id}", status_code=303)
    return RedirectResponse(url="/", status_code=303)