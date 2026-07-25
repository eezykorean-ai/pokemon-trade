from fastapi import FastAPI, Form, File, UploadFile, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from supabase import create_client, Client
import uuid
from typing import Optional

app = FastAPI()

# 정적 파일 마운트 (CSS 등)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Supabase 연동 설정
SUPABASE_URL = "https://jdnasvonwrgiitdenfsv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpkbmFzdm9ud3JnaWl0ZGVuZnN2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ5OTA2NjcsImV4cCI6MjEwMDU2NjY2N30.V1G_lU7lOsfJ34_4EjsZEGblRFA-5mDi35_sayiPEnk"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_current_user(request: Request) -> Optional[str]:
    return request.cookies.get("username")

# KREAM 스타일 공통 레이아웃
def layout(title: str, content: str, current_user: Optional[str] = None):
    nav = f"""
    <nav class="sticky top-0 z-50 bg-white border-b border-gray-200">
        <div class="max-w-6xl mx-auto px-6 h-16 flex justify-between items-center">
            <a href="/" class="text-lg font-black tracking-tighter text-black uppercase">K-POKEMON EXCHANGE</a>
            <div class="flex items-center space-x-6 text-sm font-medium text-gray-700">
                {f'<span class="text-black font-semibold">{current_user}님</span> <a href="/write" class="bg-black text-white px-4 py-2 rounded-md hover:bg-gray-800 transition">새 교환 등록</a> <a href="/logout" class="text-gray-400 hover:text-black transition">로그아웃</a>' if current_user else '<a href="/login" class="hover:text-black transition">로그인</a> <a href="/signup" class="bg-black text-white px-4 py-2 rounded-md hover:bg-gray-800 transition">회원가입</a>'}
            </div>
        </div>
    </nav>
    """
    
    footer = """
    <footer class="border-t border-gray-200 py-10 mt-12 bg-gray-50">
        <div class="max-w-6xl mx-auto px-6 text-center">
            <p class="text-xs font-black text-gray-600 mb-2 uppercase tracking-widest">Disclaimer</p>
            <p class="text-xs text-gray-400 mb-4 leading-relaxed">
                본 사이트는 포켓몬 카드 수집가들을 위한 개인 간 트레이딩(교환) 플랫폼입니다.<br>
                본 서비스는 (주)포켓몬코리아, Nintendo, Creatures, GAME FREAK 등 공식 권리자와 어떠한 제휴 및 관련도 없음을 명시합니다.<br>
                등록된 모든 상품의 교환 및 거래 책임은 거래 당사자에게 있습니다.
            </p>
            <p class="text-xs text-gray-300">&copy; 2026 K-POKEMON EXCHANGE. All Rights Reserved.</p>
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
    </div>
    """
    return layout("회원가입", content)

@app.post("/signup")
def signup(username: str = Form(...), password: str = Form(...)):
    existing = supabase.table("users").select("*").eq("username", username).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")
    
    supabase.table("users").insert({"username": username, "password": password}).execute()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login", response_class=HTMLResponse)
def login_page():
    content = """
    <div class="max-w-md mx-auto py-12">
        <div class="text-center mb-8">
            <h2 class="text-2xl font-black tracking-tight">LOGIN</h2>
            <p class="text-sm text-gray-500 mt-1">로그인하여 가치를 교환하세요.</p>
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
    </div>
    """
    return layout("로그인", content)

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
    if not user.data:
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
    
    query = supabase.table("posts").select("*").order("id", desc=True)
    
    if q:
        query = query.or_(f"pokemon_name.ilike.%{q}%,title.ilike.%{q}%")
    if attribute and attribute != "전체":
        query = query.eq("attribute", attribute)
        
    posts = query.execute().data
    
    posts_html = ""
    for post in posts:
        pid = post['id']
        title = post['title']
        p_name = post['pokemon_name']
        attr = post['attribute']
        price = post['price']
        img = post['image_url']
        author = post['username']
        
        img_tag = f"<img src='{img}' class='w-full h-64 object-cover bg-gray-50 group-hover:scale-105 transition duration-300'>" if img else "<div class='w-full h-64 bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-400'>NO IMAGE</div>"

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
    <div class="mb-10">
        <form method="get" action="/" class="flex gap-2 max-w-2xl mx-auto">
            <input type="text" name="q" placeholder="원하는 카드 검색" value="{q if q else ''}" class="flex-1 h-12 px-4 border border-gray-300 rounded-lg text-sm focus:border-black focus:outline-none transition">
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
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
        {posts_html if posts_html else "<div class='col-span-full py-24 text-center text-gray-400 text-sm'>등록된 카드가 없습니다.</div>"}
    </div>
    """
    return layout("K-POKEMON EXCHANGE", content, current_user)

@app.get("/write", response_class=HTMLResponse)
def write_page(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
    content = """
    <div class="max-w-xl mx-auto py-10">
        <h2 class="text-2xl font-black tracking-tight mb-8 text-center">NEW TRADE</h2>
        <form action="/write" method="post" enctype="multipart/form-data" class="space-y-6">
            <div>
                <label class="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">교환 제목</label>
                <input type="text" name="title" required placeholder="예: [S급] 리자몽 VMAX 교환합니다" class="w-full h-12 px-4 border border-gray-300 rounded-lg focus:border-black focus:outline-none transition">
            </div>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">보유 포켓몬 이름</label>
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
                <label class="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">원하는 조건 (교환 희망 카드)</label>
                <input type="text" name="price" required placeholder="예: 물 속성 레어 카드 1:1 교환" class="w-full h-12 px-4 border border-gray-300 rounded-lg focus:border-black focus:outline-none transition">
            </div>
            
            <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <label class="block text-xs font-bold uppercase tracking-wider text-black mb-2">상품 이미지 등록</label>
                <input type="file" name="file" class="w-full py-2 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-bold file:bg-black file:text-white hover:file:bg-gray-800 transition mb-3">
                <p class="text-xs text-red-500 font-bold leading-relaxed">
                    🚨 주의: 직접 촬영한 '실물 카드 사진'만 업로드해 주세요.
                </p>
            </div>

            <div class="flex gap-4 pt-4">
                <a href="/" class="flex-1 h-12 flex items-center justify-center border border-gray-300 text-black font-bold rounded-lg hover:bg-gray-50 transition">취소</a>
                <button type="submit" class="flex-1 h-12 bg-black text-white font-bold rounded-lg hover:bg-gray-800 transition">등록하기</button>
            </div>
        </form>
    </div>
    """
    return layout("교환 등록", content, current_user)

@app.post("/write")
async def write_post(
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
        file_ext = file.filename.split('.')[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_bytes = await file.read()
        
        # Supabase Storage에 이미지 업로드
        supabase.storage.from_("images").upload(file_name, file_bytes, {"content-type": file.content_type})
        image_url = supabase.storage.from_("images").get_public_url(file_name)
        
    supabase.table("posts").insert({
        "title": title,
        "pokemon_name": pokemon_name,
        "attribute": attribute,
        "price": price,
        "image_url": image_url,
        "username": current_user
    }).execute()
    
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/post/{post_id}", response_class=HTMLResponse)
def post_detail(post_id: int, request: Request):
    current_user = get_current_user(request)
    
    post_res = supabase.table("posts").select("*").eq("id", post_id).execute()
    if not post_res.data:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    post = post_res.data[0]
    
    comments_res = supabase.table("comments").select("*").eq("post_id", post_id).order("id").execute()
    comments = comments_res.data
    
    img = post['image_url']
    img_tag = f"<img src='{img}' class='w-full max-h-[500px] object-contain bg-gray-50 rounded-xl mb-6'>" if img else ""
    
    # 댓글 삭제 버튼 추가 로직
    comments_html = ""
    for c in comments:
        delete_btn = ""
        if current_user == c['username']:
            delete_btn = f"""
            <form action="/comment/{c['id']}/delete" method="post" class="inline m-0 p-0">
                <button type="submit" class="text-xs text-red-400 hover:text-red-600 font-bold transition ml-4">삭제</button>
            </form>
            """
        
        comments_html += f"""
        <div class="py-3 border-b border-gray-100 flex justify-between items-center text-sm">
            <div>
                <span class="font-bold text-black mr-2">{c['username']}</span>
                <span class="text-gray-700">{c['content']}</span>
            </div>
            {delete_btn}
        </div>
        """
        
    if current_user:
        comment_form = f"""
        <form action="/post/{post['id']}/comment" method="post" class="flex gap-2 mt-6">
            <input type="text" name="content" placeholder="교환 제안을 댓글로 남겨보세요" required class="flex-1 h-12 px-4 border border-gray-300 rounded-lg text-sm focus:border-black focus:outline-none transition">
            <button type="submit" class="h-12 px-6 bg-black text-white text-sm font-bold rounded-lg hover:bg-gray-800 transition">등록</button>
        </form>
        """
    else:
        comment_form = "<div class='py-4 text-center bg-gray-50 rounded-lg text-xs text-gray-500'>댓글을 작성하려면 <a href='/login' class='underline font-bold text-black'>로그인</a>이 필요합니다.</div>"
    
    # 본인 게시글 삭제 버튼 추가 로직
    post_delete_btn = ""
    if current_user == post['username']:
        post_delete_btn = f"""
        <form action="/post/{post['id']}/delete" method="post" class="text-right mt-4" onsubmit="return confirm('정말로 이 교환글을 삭제하시겠습니까?');">
            <button type="submit" class="text-xs text-red-500 hover:text-red-700 font-bold underline transition">게시글 삭제하기</button>
        </form>
        """
        
    content = f"""
    <div class="max-w-3xl mx-auto py-10">
        <a href="/" class="text-xs font-bold text-gray-400 hover:text-black transition mb-6 inline-block">&larr; BACK TO LIST</a>
        {img_tag}
        <div class="border-b border-gray-200 pb-6 mb-6">
            <div class="flex justify-between items-center mb-2">
                <span class="text-xs font-bold text-black uppercase tracking-wider">{post['attribute']}</span>
                <span class="text-xs text-gray-400">TRADER: {post['username']}</span>
            </div>
            <h1 class="text-2xl font-black text-black mb-4">{post['title']}</h1>
            <div class="flex justify-between items-center bg-gray-50 p-4 rounded-xl">
                <span class="text-xs text-gray-500 font-medium">포켓몬: {post['pokemon_name']}</span>
                <span class="text-2xl font-black text-black">{post['price']}</span>
            </div>
            {post_delete_btn}
        </div>

        <div>
            <h3 class="font-bold text-base mb-4">💬 교환 제안 및 문의</h3>
            <div class="divide-y divide-gray-100 mb-4">
                {comments_html if comments_html else "<div class='py-8 text-center text-gray-400 text-xs'>작성된 제안이 없습니다.</div>"}
            </div>
            {comment_form}
        </div>
    </div>
    """
    return layout(post['title'], content, current_user)

@app.post("/post/{post_id}/comment")
def add_comment(post_id: int, request: Request, content: str = Form(...)):
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
        
    supabase.table("comments").insert({
        "post_id": post_id,
        "username": current_user,
        "content": content
    }).execute()
    
    return RedirectResponse(url=f"/post/{post_id}", status_code=status.HTTP_303_SEE_OTHER)

# 게시글 삭제 엔드포인트
@app.post("/post/{post_id}/delete")
def delete_post(post_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    post_res = supabase.table("posts").select("*").eq("id", post_id).execute()
    if not post_res.data:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    post = post_res.data[0]
    if post["username"] != current_user:
        raise HTTPException(status_code=403, detail="본인의 게시글만 삭제할 수 있습니다.")
    
    # 이미지 파일이 있으면 Storage에서도 깔끔하게 삭제
    if post["image_url"]:
        file_name = post["image_url"].split("/")[-1]
        supabase.storage.from_("images").remove([file_name])
        
    # 데이터베이스에서 글 삭제
    supabase.table("posts").delete().eq("id", post_id).execute()
    
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

# 댓글 삭제 엔드포인트
@app.post("/comment/{comment_id}/delete")
def delete_comment(comment_id: int, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
        
    comment_res = supabase.table("comments").select("*").eq("id", comment_id).execute()
    if not comment_res.data:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    
    comment = comment_res.data[0]
    if comment["username"] != current_user:
        raise HTTPException(status_code=403, detail="본인의 댓글만 삭제할 수 있습니다.")
        
    # 데이터베이스에서 댓글 삭제
    supabase.table("comments").delete().eq("id", comment_id).execute()
    
    return RedirectResponse(url=f"/post/{comment['post_id']}", status_code=status.HTTP_303_SEE_OTHER)