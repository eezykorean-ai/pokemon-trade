from fastapi import FastAPI, Request, Form, Response, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
import os
import bcrypt
import uuid
from supabase import create_client, Client

app = FastAPI()

# Supabase 연결 설정 (렌더 환경변수에서 가져옴)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 공통 레이아웃 템플릿 (디스클레이머 포함) ---
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
        <title>K-POKEMON EXCHANGE</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen text-gray-800 flex flex-col">
        <nav class="bg-white border-b border-gray-100 sticky top-0 z-50 shadow-sm">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                <a href="/" class="text-xl font-extrabold text-gray-900 tracking-tight flex items-center gap-1">K-POKEMON EXCHANGE</a>
                <div class="flex items-center space-x-3">
                    {nav_auth}
                </div>
            </div>
        </nav>
        
        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-grow w-full">
            {body_content}
        </main>

        <!-- 디스클레이머 (저작권 안내문) -->
        <footer class="bg-white border-t border-gray-200 mt-auto py-8">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                <h4 class="text-sm font-bold text-gray-600 mb-2 tracking-wider">DISCLAIMER</h4>
                <p class="text-xs text-gray-400 mb-1">본 사이트는 포켓몬 카드 수집가들을 위한 개인 간 트레이딩(교환) 플랫폼입니다.</p>
                <p class="text-xs text-gray-400 mb-1">본 서비스는 (주)포켓몬코리아, Nintendo, Creatures, GAME FREAK 등 공식 권리자와 어떠한 제휴 및 관련도 없음을 명시합니다.</p>
                <p class="text-xs text-gray-400 mb-4">등록된 모든 상품의 교환 및 거래 책임은 거래 당사자에게 있습니다.</p>
                <p class="text-xs text-gray-300">&copy; 2026 K-POKEMON EXCHANGE. All Rights Reserved.</p>
            </div>
        </footer>
    </body>
    </html>
    """

# 1. 메인 페이지
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, search: str = "", attribute: str = "all"):
    user = request.cookies.get("user")
    
    response = supabase.table("posts").select("*").order("id", desc=True).execute()
    posts = response.data
    
    filtered_posts = []
    for p in posts:
        match_search = search.lower() in p.get("pokemon_name", "").lower() if search else True
        match_attr = (attribute == "all" or p.get("attribute") == attribute)
        if match_search and match_attr:
            filtered_posts.append(p)
            
    search_value = search if search else ""
    attr_options = ["all", "불꽃", "물", "풀", "전기", "무색", "격투", "악", "초마련", "강철", "드래곤", "페어리"]
    attr_html = ""
    for opt in attr_options:
        selected = "selected" if attribute == opt else ""
        label = "모든 속성" if opt == "all" else opt
        attr_html += f'<option value="{opt}" {selected}>{label}</option>'

    body = f"""
    <div class="mb-8">
        <form action="/" method="GET" class="flex gap-2 justify-center max-w-2xl mx-auto">
            <input type="text" name="search" value="{search_value}" placeholder="포켓몬 이름 검색..." class="flex-grow px-4 py-2 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
            <select name="attribute" class="px-4 py-2 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
                {attr_html}
            </select>
            <button type="submit" class="px-6 py-2 bg-gray-900 text-white font-semibold rounded-xl hover:bg-gray-800 transition">검색</button>
        </form>
    </div>
    """

    if not filtered_posts:
        body += '<div class="text-center text-gray-500 mt-20">등록된 카드가 없습니다.</div>'
    else:
        body += '<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">'
        for post in filtered_posts:
            is_completed = post.get("status") == "completed"
            opacity_class = "opacity-50 grayscale" if is_completed else ""
            badge = '<div class="absolute top-2 right-2 bg-red-600 text-white text-xs font-bold px-2 py-1 rounded shadow-sm z-10">교환완료</div>' if is_completed else ""
            
            # 등급 배지 색상 결정 (등급 카드면 보라색, 싱글 카드면 회색)
            grade_value = post.get('grade', '싱글 카드')
            if grade_value == "싱글 카드":
                grade_badge_color = "bg-gray-100 text-gray-600"
            else:
                grade_badge_color = "bg-purple-100 text-purple-800"

            body += f"""
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition relative {opacity_class}">
                {badge}
                <div class="h-48 bg-gray-100 overflow-hidden flex items-center justify-center">
                    <img src="{post.get('image_url')}" alt="{post.get('title')}" class="w-full h-full object-cover">
                </div>
                <div class="p-4">
                    <div class="flex items-center gap-2 mb-2">
                        <span class="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs font-semibold rounded">{post.get('attribute', '속성없음')}</span>
                        <span class="px-2 py-0.5 {grade_badge_color} text-xs font-bold rounded shadow-sm">{grade_value}</span>
                    </div>
                    <h3 class="text-xs text-gray-500 font-medium mb-1">{post.get('pokemon_name')}</h3>
                    <h2 class="text-lg font-bold text-gray-900 mb-2 truncate">{post.get('title')}</h2>
                    <p class="text-sm text-gray-600 line-clamp-2 mb-3">{post.get('trade_condition')}</p>
                    <div class="text-xs text-gray-400 font-medium text-right">작성자: {post.get('author')}</div>
                </div>
            </div>
            """
        body += '</div>'

    return layout(body, user)

# 2. 회원가입 폼
@app.get("/signup", response_class=HTMLResponse)
async def signup_form():
    body = """
    <div class="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-sm border border-gray-100 mt-10">
        <h2 class="text-2xl font-bold text-gray-900 mb-6 text-center">회원가입</h2>
        <form action="/signup" method="POST" class="flex flex-col gap-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">아이디</label>
                <input type="text" name="username" required class="w-full px-4 py-2 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
                <input type="password" name="password" required class="w-full px-4 py-2 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            <button type="submit" class="w-full py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition mt-2">가입하기</button>
        </form>
    </div>
    """
    return layout(body)

# 3. 회원가입 처리
@app.post("/signup")
async def process_signup(username: str = Form(...), password: str = Form(...)):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        supabase.table("users").insert({
            "username": username,
            "password": hashed_password
        }).execute()
        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        return HTMLResponse(layout(f"<div class='text-center text-red-500 mt-10'>오류가 발생했습니다.<br>상세 오류: {str(e)}</div>"))

# 4. 로그인 폼
@app.get("/login", response_class=HTMLResponse)
async def login_form():
    body = """
    <div class="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-sm border border-gray-100 mt-10">
        <h2 class="text-2xl font-bold text-gray-900 mb-6 text-center">로그인</h2>
        <form action="/login" method="POST" class="flex flex-col gap-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">아이디</label>
                <input type="text" name="username" required class="w-full px-4 py-2 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
                <input type="password" name="password" required class="w-full px-4 py-2 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            <button type="submit" class="w-full py-3 bg-gray-900 text-white font-bold rounded-xl hover:bg-gray-800 transition mt-2">로그인</button>
        </form>
    </div>
    """
    return layout(body)

# 5. 로그인 처리
@app.post("/login")
async def process_login(response: Response, username: str = Form(...), password: str = Form(...)):
    res = supabase.table("users").select("*").eq("username", username).execute()
    users = res.data
    if users and bcrypt.checkpw(password.encode('utf-8'), users[0]['password'].encode('utf-8')):
        redirect = RedirectResponse(url="/", status_code=303)
        redirect.set_cookie(key="user", value=username)
        return redirect
    else:
        return HTMLResponse(layout("<div class='text-center text-red-500 mt-10'>아이디/비밀번호 오류입니다.</div>"))

# 6. 로그아웃
@app.get("/logout")
async def logout(response: Response):
    redirect = RedirectResponse(url="/", status_code=303)
    redirect.delete_cookie("user")
    return redirect

# 7. 새 교환 등록 폼 (전문가용 등급 선택 기능 탑재)
@app.get("/write", response_class=HTMLResponse)
async def write_form(request: Request):
    user = request.cookies.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    body = f"""
    <div class="max-w-2xl mx-auto bg-white p-8 rounded-2xl shadow-sm border border-gray-100 mt-6">
        <h2 class="text-2xl font-bold text-gray-900 mb-6 text-center">새 교환 등록</h2>
        <form action="/write" method="POST" enctype="multipart/form-data" class="flex flex-col gap-5">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">제목</label>
                <input type="text" name="title" required placeholder="예: 뮤츠 특일 피카츄로 교환 원합니다" class="w-full px-4 py-2 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">포켓몬 이름</label>
                    <input type="text" name="pokemon_name" required placeholder="예: 뮤츠" class="w-full px-4 py-2 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">속성</label>
                    <select name="attribute" class="w-full px-4 py-2 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
                        <option value="무색">무색</option>
                        <option value="불꽃">불꽃</option>
                        <option value="물">물</option>
                        <option value="풀">풀</option>
                        <option value="전기">전기</option>
                        <option value="격투">격투</option>
                        <option value="악">악</option>
                        <option value="초마련">초마련</option>
                        <option value="강철">강철</option>
                        <option value="드래곤">드래곤</option>
                        <option value="페어리">페어리</option>
                    </select>
                </div>
            </div>

            <!-- 카드 종류 및 전문 등급 선택 영역 -->
            <div class="p-5 bg-gray-50 border border-gray-200 rounded-xl">
                <label class="block text-sm font-bold text-gray-800 mb-2">카드 인증 상태</label>
                <select id="card_type" name="card_type" onchange="toggleGradeFields()" class="w-full px-4 py-2 border rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white mb-4 shadow-sm">
                    <option value="싱글 카드">싱글 카드 (미인증 일반 카드)</option>
                    <option value="등급 카드">등급 카드 (전문 기관 인증 완료)</option>
                </select>

                <!-- 등급 카드 선택 시 나타나는 숨겨진 칸 -->
                <div id="grade_fields" class="hidden grid-cols-2 gap-4 transition-all duration-300">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">인증 기관</label>
                        <select name="grading_company" class="w-full px-4 py-2 border rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white">
                            <option value="PSA">PSA</option>
                            <option value="BRG">BRG</option>
                            <option value="BGS">BGS</option>
                            <option value="CGC">CGC</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">등급 점수</label>
                        <select name="grade_score" class="w-full px-4 py-2 border rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white">
                            <option value="10">10 (Gem Mint)</option>
                            <option value="9.5">9.5 (Mint+)</option>
                            <option value="9">9 (Mint)</option>
                            <option value="8">8 (NM-MT)</option>
                            <option value="7">7 (NM)</option>
                            <option value="6">6 (EX-MT)</option>
                            <option value="5">5 이하 (Play)</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- 자바스크립트로 등급 입력칸 끄고 켜기 -->
            <script>
                function toggleGradeFields() {{
                    const type = document.getElementById('card_type').value;
                    const fields = document.getElementById('grade_fields');
                    if (type === '등급 카드') {{
                        fields.classList.remove('hidden');
                        fields.classList.add('grid');
                    }} else {{
                        fields.classList.add('hidden');
                        fields.classList.remove('grid');
                    }}
                }}
            </script>

            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">교환 조건 / 설명</label>
                <textarea name="trade_condition" required rows="4" placeholder="원하는 카드나 상태 등을 적어주세요." class="w-full px-4 py-2 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"></textarea>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">카드 사진 첨부 (스마트폰 앨범 지원)</label>
                <input type="file" name="image" accept="image/*" required class="w-full px-4 py-2 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white cursor-pointer">
            </div>
            
            <button type="submit" class="w-full py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition mt-2">등록하기</button>
        </form>
    </div>
    """
    return layout(body, user)

# 8. 새 교환 등록 처리
@app.post("/write")
async def process_write(
    request: Request, 
    title: str = Form(...), 
    pokemon_name: str = Form(...), 
    attribute: str = Form(...), 
    card_type: str = Form(...),
    grading_company: str = Form(default="PSA"),
    grade_score: str = Form(default="10"),
    trade_condition: str = Form(...), 
    image: UploadFile = File(...)
):
    user = request.cookies.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    try:
        # 1. 파일 이름 난수화 및 읽기 (이미지가 덮어씌워지지 않게 고유 이름 생성)
        file_ext = image.filename.split('.')[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        image_bytes = await image.read()
        
        # 2. Supabase Storage 'images' 버킷에 파일 업로드
        supabase.storage.from_("images").upload(
            path=file_name,
            file=image_bytes,
            file_options={"content-type": image.content_type}
        )
        
        # 3. 업로드된 이미지의 공개 인터넷 주소(URL) 가져오기
        image_url = supabase.storage.from_("images").get_public_url(file_name)
        
        # 4. 카드 등급 글자 예쁘게 합치기
        if card_type == "싱글 카드":
            final_grade = "싱글 카드"
        else:
            final_grade = f"{grading_company} {grade_score}"
            
        # 5. 데이터베이스에 전체 정보 저장 (방금 만든 final_grade를 grade 칸에 넣음!)
        supabase.table("posts").insert({
            "title": title,
            "pokemon_name": pokemon_name,
            "attribute": attribute,
            "grade": final_grade, 
            "trade_condition": trade_condition,
            "image_url": image_url,
            "author": user,
            "status": "active"
        }).execute()
        
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        return HTMLResponse(layout(f"<div class='text-center text-red-500 mt-10'>글 등록 중 오류가 발생했습니다.<br>상세 오류: {str(e)}</div>"))

# 9. 마이페이지
@app.get("/mypage", response_class=HTMLResponse)
async def mypage(request: Request):
    user = request.cookies.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    response = supabase.table("posts").select("*").eq("author", user).order("id", desc=True).execute()
    my_posts = response.data
    
    body = f"""
    <div class="mb-8 border-b pb-4">
        <h2 class="text-2xl font-bold text-gray-900">마이페이지</h2>
        <p class="text-sm text-gray-500 mt-1">내가 등록한 교환 글을 관리하세요.</p>
    </div>
    """
    
    if not my_posts:
        body += '<div class="text-center text-gray-500 mt-20">등록한 교환 글이 없습니다.</div>'
    else:
        body += '<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">'
        for post in my_posts:
            is_completed = post.get("status") == "completed"
            opacity_class = "opacity-50 grayscale" if is_completed else ""
            badge = '<div class="absolute top-2 right-2 bg-red-600 text-white text-xs font-bold px-2 py-1 rounded z-10">교환완료</div>' if is_completed else ""
            
            btn_text = "판매중으로 변경" if is_completed else "교환 완료하기"
            btn_color = "bg-gray-500 hover:bg-gray-600" if is_completed else "bg-green-600 hover:bg-green-700"
            
            grade_value = post.get('grade', '싱글 카드')
            if grade_value == "싱글 카드":
                grade_badge_color = "bg-gray-100 text-gray-600"
            else:
                grade_badge_color = "bg-purple-100 text-purple-800"

            body += f"""
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden relative flex flex-col h-full">
                <div class="{opacity_class} transition duration-300 flex-grow">
                    {badge}
                    <div class="h-48 bg-gray-100 overflow-hidden flex items-center justify-center">
                        <img src="{post.get('image_url')}" alt="{post.get('title')}" class="w-full h-full object-cover">
                    </div>
                    <div class="p-4 border-b border-gray-50">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs font-semibold rounded">{post.get('attribute', '속성없음')}</span>
                            <span class="px-2 py-0.5 {grade_badge_color} text-xs font-bold rounded shadow-sm">{grade_value}</span>
                        </div>
                        <h3 class="text-xs text-gray-500 font-medium mb-1">{post.get('pokemon_name')}</h3>
                        <h2 class="text-lg font-bold text-gray-900 mb-2 truncate">{post.get('title')}</h2>
                    </div>
                </div>
                
                <div class="p-3 bg-gray-50 mt-auto">
                    <form action="/toggle_status/{post.get('id')}" method="POST" class="w-full">
                        <button type="submit" class="w-full py-2 {btn_color} text-white text-sm font-bold rounded-lg shadow-sm transition">
                            {btn_text}
                        </button>
                    </form>
                </div>
            </div>
            """
        body += '</div>'

    return layout(body, user)

# 10. 교환 상태 토글 처리
@app.post("/toggle_status/{post_id}")
async def toggle_status(post_id: int, request: Request):
    user = request.cookies.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    res = supabase.table("posts").select("status").eq("id", post_id).eq("author", user).execute()
    if not res.data:
        return RedirectResponse(url="/mypage", status_code=303)
        
    current_status = res.data[0].get("status")
    new_status = "active" if current_status == "completed" else "completed"
    
    supabase.table("posts").update({"status": new_status}).eq("id", post_id).execute()
    
    return RedirectResponse(url="/mypage", status_code=303)