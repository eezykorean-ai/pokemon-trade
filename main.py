from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI()

if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

class InventoryItem(BaseModel):
    user_id: int
    card_name: str
    card_grade: str
    image_data: str
    inventory_type: str

class TradeOffer(BaseModel):
    inventory_id: int
    offerer_name: str
    offer_message: str
    offered_card: str

class OfferResponse(BaseModel):
    offer_id: int
    status: str

def init_db():
    conn = sqlite3.connect('pokemon_trade.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_inventory (
            inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_name TEXT,
            card_grade TEXT,
            image_data TEXT,
            type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_offers (
            offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_id INTEGER,
            offerer_name TEXT,
            offer_message TEXT,
            offered_card TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/", response_class=HTMLResponse)
def serve_webpage():
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PokéTrade — Premium Card Market</title>
        <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css" />
        <style>
            :root {
                --bg-color: #f8f9fa;
                --card-bg: #ffffff;
                --text-main: #111111;
                --text-sub: #868e96;
                --border-color: #e9ecef;
                --primary: #f15746;
                --have-color: #fa5252;
                --want-color: #228be6;
                --radius-sm: 12px;
                --radius-lg: 20px;
            }

            body {
                font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
                background-color: var(--bg-color);
                color: var(--text-main);
                margin: 0;
                padding: 0;
                -webkit-font-smoothing: antialiased;
                letter-spacing: -0.3px;
            }

            /* 상단 네비게이션 */
            header {
                position: sticky; top: 0; z-index: 100;
                background: rgba(255, 255, 255, 0.85);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border-bottom: 1px solid var(--border-color);
                padding: 0 40px;
                height: 72px;
                display: flex; justify-content: space-between; align-items: center;
            }
            .brand { display: flex; align-items: center; gap: 12px; cursor: pointer; }
            .brand img { width: 36px; height: 36px; object-fit: contain; }
            .brand h1 { margin: 0; font-size: 1.25rem; font-weight: 900; letter-spacing: -0.5px; }

            .btn-inbox {
                background: #f1f3f5; color: var(--text-main); border: none;
                padding: 10px 18px; border-radius: 20px; font-weight: 700; font-size: 0.85rem;
                cursor: pointer; transition: all 0.2s;
            }
            .btn-inbox:hover { background: #e9ecef; }

            /* 메인 레이아웃 */
            .main-container {
                max-width: 1400px; margin: 40px auto; padding: 0 24px;
                display: grid; grid-template-columns: 360px 1fr; gap: 32px;
            }
            @media (max-width: 950px) {
                .main-container { grid-template-columns: 1fr; }
            }

            /* 좌측 등록 카드 패널 */
            .upload-card {
                background: var(--card-bg); border: 1px solid var(--border-color);
                border-radius: var(--radius-lg); padding: 32px; height: fit-content;
                box-shadow: 0 4px 24px rgba(0,0,0,0.03);
            }
            .upload-card h2 { font-size: 1.2rem; font-weight: 800; margin-top: 0; margin-bottom: 24px; }

            .field { margin-bottom: 20px; }
            .field label { display: block; font-size: 0.8rem; font-weight: 700; color: var(--text-sub); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
            .field input[type="text"], .field select, .field input[type="file"] {
                width: 100%; padding: 13px 16px; background: #f8f9fa; border: 1px solid var(--border-color);
                border-radius: var(--radius-sm); font-size: 0.95rem; box-sizing: border-box; outline: none; transition: all 0.2s;
                font-family: inherit; color: var(--text-main);
            }
            .field input:focus, .field select:focus { border-color: var(--text-main); background: white; box-shadow: 0 0 0 3px rgba(17,17,17,0.05); }

            /* 라디오 셀렉터 */
            .type-pick { display: flex; gap: 8px; }
            .type-pick label { flex: 1; cursor: pointer; }
            .type-pick input { display: none; }
            .pick-box {
                display: block; text-align: center; padding: 12px; background: #f8f9fa;
                border: 1px solid var(--border-color); border-radius: var(--radius-sm);
                font-weight: 700; font-size: 0.85rem; color: var(--text-sub); transition: all 0.2s;
            }
            .type-pick input[value="HAVE"]:checked + .pick-box { border-color: var(--have-color); background: #fff5f5; color: var(--have-color); }
            .type-pick input[value="WANT"]:checked + .pick-box { border-color: var(--want-color); background: #e7f5ff; color: var(--want-color); }

            .btn-submit {
                width: 100%; background: var(--text-main); color: white; border: none;
                padding: 14px; border-radius: var(--radius-sm); font-weight: 800; font-size: 0.95rem;
                cursor: pointer; transition: background 0.2s; margin-top: 10px; font-family: inherit;
            }
            .btn-submit:hover { background: #333; }

            /* 우측 피드 섹션 및 탭 필터 */
            .feed-header-wrap { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
            .feed-title { font-size: 1.3rem; font-weight: 900; margin: 0; }
            
            .filter-tabs { display: flex; gap: 6px; background: #edeef2; padding: 4px; border-radius: 12px; }
            .tab-btn {
                background: transparent; border: none; padding: 8px 16px; border-radius: 9px;
                font-size: 0.85rem; font-weight: 700; color: var(--text-sub); cursor: pointer; transition: all 0.2s;
                font-family: inherit;
            }
            .tab-btn.active { background: white; color: var(--text-main); box-shadow: 0 2px 8px rgba(0,0,0,0.06); }

            .card-grid {
                display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 24px;
            }

            /* 카드 디자인 */
            .market-card {
                background: var(--card-bg); border: 1px solid var(--border-color);
                border-radius: var(--radius-lg); overflow: hidden; display: flex; flex-direction: column;
                transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s cubic-bezier(0.16, 1, 0.3, 1); position: relative;
            }
            .market-card:hover { transform: translateY(-6px); box-shadow: 0 16px 32px rgba(0,0,0,0.08); }

            .status-badge {
                position: absolute; top: 14px; left: 14px; padding: 6px 12px; border-radius: 8px;
                font-size: 0.7rem; font-weight: 800; color: white; letter-spacing: 0.5px; z-index: 2;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }
            .badge-have { background: var(--have-color); }
            .badge-want { background: var(--want-color); }

            .btn-card-delete {
                position: absolute; top: 14px; right: 14px; background: rgba(0,0,0,0.5); color: white;
                backdrop-filter: blur(4px); border: none; width: 28px; height: 28px; border-radius: 50%; font-size: 0.75rem;
                cursor: pointer; z-index: 2; display: flex; align-items: center; justify-content: center;
                transition: background 0.2s;
            }
            .btn-card-delete:hover { background: #fa5252; }

            .card-thumb {
                width: 100%; height: 260px; background: #f1f3f5; display: flex; align-items: center; justify-content: center;
                padding: 24px; box-sizing: border-box; position: relative;
            }
            .card-thumb img { max-width: 100%; max-height: 100%; object-fit: contain; filter: drop-shadow(0 10px 16px rgba(0,0,0,0.12)); }

            .card-details { padding: 20px; display: flex; flex-direction: column; flex-grow: 1; justify-content: space-between; }
            .card-name { font-weight: 800; font-size: 1.05rem; color: var(--text-main); margin-bottom: 6px; }
            .card-grade-tag { font-size: 0.75rem; font-weight: 700; color: #495057; background: #f1f3f5; padding: 5px 10px; border-radius: 6px; width: fit-content; margin-bottom: 16px; }

            .btn-offer-trigger {
                width: 100%; background: #f8f9fa; color: var(--text-main); border: 1px solid var(--border-color);
                padding: 11px; border-radius: var(--radius-sm); font-weight: 700; font-size: 0.85rem; cursor: pointer;
                transition: all 0.2s; font-family: inherit;
            }
            .btn-offer-trigger:hover { background: var(--text-main); color: white; border-color: var(--text-main); }

            /* 모달 디자인 */
            .modal-wrap {
                display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.4); backdrop-filter: blur(6px);
                justify-content: center; align-items: center; z-index: 1000;
            }
            .modal-body {
                background: white; width: 420px; max-width: 90%; padding: 36px;
                border-radius: var(--radius-lg); position: relative; box-shadow: 0 24px 48px rgba(0,0,0,0.15);
                animation: modalUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }
            @keyframes modalUp {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .modal-close {
                position: absolute; top: 20px; right: 20px; background: #f1f3f5; border: none;
                width: 32px; height: 32px; border-radius: 50%; cursor: pointer; color: var(--text-sub);
                display: flex; align-items: center; justify-content: center; font-weight: bold;
            }
            .modal-close:hover { background: #e9ecef; color: var(--text-main); }
            .modal-body h3 { margin-top: 0; font-size: 1.25rem; font-weight: 900; margin-bottom: 6px; }

            /* 교환함 리스트 스타일 */
            .offer-card-item { background: #f8f9fa; border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 16px; margin-bottom: 12px; }
            .offer-card-item p { margin: 4px 0; font-size: 0.9rem; }
            .action-btns { display: flex; gap: 8px; margin-top: 12px; }
            .btn-act-accept { flex: 1; background: #2f9e44; color: white; border: none; padding: 10px; border-radius: 8px; font-weight: 700; cursor: pointer; font-family: inherit; }
            .btn-act-reject { flex: 1; background: #fa5252; color: white; border: none; padding: 10px; border-radius: 8px; font-weight: 700; cursor: pointer; font-family: inherit; }
        </style>
    </head>
    <body>

        <header>
            <div class="brand" onclick="location.reload()">
                <img src="/static/logo.png" alt="로고">
                <h1>PokéTrade</h1>
            </div>
            <button class="btn-inbox" onclick="openInbox()">✉️ 교환함 확인</button>
        </header>

        <div class="main-container">
            <!-- 좌측 등록 폼 -->
            <div class="upload-card">
                <h2>새 카드 등록</h2>
                <form id="uploadForm">
                    <div class="field">
                        <label>카드 명칭 / 품번</label>
                        <input type="text" id="cardName" placeholder="예: 리자몽 ex (sv2a)" required>
                    </div>
                    <div class="field">
                        <label>컨디션 / 등급</label>
                        <select id="cardGrade">
                            <option value="미감정 (Raw)">미감정 (Raw)</option>
                            <option value="PSA 10 (Gem Mint)">PSA 10 (Gem Mint)</option>
                            <option value="PSA 9 (Mint)">PSA 9 (Mint)</option>
                            <option value="PSA 8 (NM-MT)">PSA 8 (NM-MT)</option>
                            <option value="PSA 7 (NM)">PSA 7 (NM)</option>
                            <option value="PSA 6 (EX-MT)">PSA 6 (EX-MT)</option>
                            <option value="PSA 5 (EX)">PSA 5 (EX)</option>
                            <option value="PSA 4 (VG-EX)">PSA 4 (VG-EX)</option>
                            <option value="PSA 3 (VG)">PSA 3 (VG)</option>
                            <option value="PSA 2 (Good)">PSA 2 (Good)</option>
                            <option value="PSA 1 (Poor)">PSA 1 (Poor)</option>
                            <option value="BGS 9.5">BGS 9.5 (Pristine)</option>
                        </select>
                    </div>
                    <div class="field">
                        <label>거래 유형</label>
                        <div class="type-pick">
                            <label><input type="radio" name="type" value="HAVE" checked><span class="pick-box">내어줌 (HAVE)</span></label>
                            <label><input type="radio" name="type" value="WANT"><span class="pick-box">구함 (WANT)</span></label>
                        </div>
                    </div>
                    <div class="field">
                        <label>상품 이미지</label>
                        <input type="file" id="cardImage" accept="image/*" required>
                    </div>
                    <button type="submit" class="btn-submit">마켓에 등록하기</button>
                </form>
            </div>

            <!-- 우측 피드 -->
            <div>
                <div class="feed-header-wrap">
                    <h2 class="feed-title">Market Feed</h2>
                    <div class="filter-tabs">
                        <button class="tab-btn active" onclick="setFilter('ALL', this)">전체</button>
                        <button class="tab-btn" onclick="setFilter('HAVE', this)">내어줌 (HAVE)</button>
                        <button class="tab-btn" onclick="setFilter('WANT', this)">구함 (WANT)</button>
                    </div>
                </div>
                <div class="card-grid" id="cardGrid"></div>
            </div>
        </div>

        <!-- 교환 제안 모달 -->
        <div class="modal-wrap" id="tradeModal">
            <div class="modal-body">
                <button class="modal-close" onclick="closeModal('tradeModal')">✕</button>
                <h3>교환 제안</h3>
                <p id="targetCardText" style="font-size: 0.85rem; color: var(--text-sub); margin-bottom: 20px;"></p>
                <form id="offerForm">
                    <input type="hidden" id="targetInventoryId">
                    <div class="field">
                        <label>닉네임</label>
                        <input type="text" id="offererName" placeholder="사용할 닉네임 입력" required>
                    </div>
                    <div class="field">
                        <label>제시할 카드</label>
                        <input type="text" id="offeredCard" placeholder="교환 제안할 카드 이름" required>
                    </div>
                    <div class="field">
                        <label>제안 메시지</label>
                        <input type="text" id="offerMessage" placeholder="간단한 인사 및 메시지" required>
                    </div>
                    <button type="submit" class="btn-submit">제안 전송하기</button>
                </form>
            </div>
        </div>

        <!-- 내 교환함 모달 -->
        <div class="modal-wrap" id="inboxModal">
            <div class="modal-body" style="width: 520px;">
                <button class="modal-close" onclick="closeModal('inboxModal')">✕</button>
                <h3>받은 교환 제안함</h3>
                <div id="inboxContent" style="margin-top: 20px; max-height: 60vh; overflow-y: auto;"></div>
            </div>
        </div>

        <script>
            let allCards = [];
            let currentFilter = 'ALL';

            async function loadCards() {
                const res = await fetch('/api/cards');
                allCards = await res.json();
                renderGrid();
            }

            function setFilter(filterType, btnElement) {
                currentFilter = filterType;
                document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
                btnElement.classList.add('active');
                renderGrid();
            }

            function renderGrid() {
                const grid = document.getElementById('cardGrid');
                grid.innerHTML = '';
                
                const filtered = allCards.filter(card => {
                    if (currentFilter === 'ALL') return true;
                    return card.type === currentFilter;
                });

                if (filtered.length === 0) {
                    grid.innerHTML = '<p style="color:var(--text-sub); grid-column: 1/-1; text-align:center; padding: 40px 0;">등록된 카드가 없습니다.</p>';
                    return;
                }
                
                filtered.forEach(card => {
                    const isHave = card.type === 'HAVE';
                    const badgeClass = isHave ? 'badge-have' : 'badge-want';
                    const badgeText = isHave ? 'HAVE' : 'WANT';
                    
                    const el = document.createElement('div');
                    el.className = 'market-card';
                    el.innerHTML = `
                        <span class="status-badge ${badgeClass}">${badgeText}</span>
                        <button class="btn-card-delete" onclick="deleteCard(${card.inventory_id})" title="삭제">✕</button>
                        <div class="card-thumb"><img src="${card.image_data}"></div>
                        <div class="card-details">
                            <div>
                                <div class="card-name">${card.card_name}</div>
                                <div class="card-grade-tag">${card.card_grade}</div>
                            </div>
                            <button class="btn-offer-trigger" onclick="openTradeModal(${card.inventory_id}, '${card.card_name}')">교환 제안</button>
                        </div>
                    `;
                    grid.appendChild(el);
                });
            }

            async function deleteCard(inventoryId) {
                if (!confirm('정말 이 카드를 삭제하시겠습니까?')) return;
                const res = await fetch(`/api/cards/${inventoryId}`, { method: 'DELETE' });
                if (res.ok) {
                    loadCards();
                } else {
                    alert('삭제에 실패했습니다.');
                }
            }

            document.getElementById('uploadForm').addEventListener('submit', function(e) {
                e.preventDefault();
                const file = document.getElementById('cardImage').files[0];
                if (!file) return;
                
                const reader = new FileReader();
                reader.onload = async function(event) {
                    const payload = {
                        user_id: 1,
                        card_name: document.getElementById('cardName').value,
                        card_grade: document.getElementById('cardGrade').value,
                        image_data: event.target.result,
                        inventory_type: document.querySelector('input[name="type"]:checked').value
                    };
                    const res = await fetch('/api/cards', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    
                    if (res.ok) {
                        document.getElementById('uploadForm').reset();
                        loadCards();
                    }
                };
                reader.readAsDataURL(file);
            });

            function openTradeModal(id, name) {
                document.getElementById('targetInventoryId').value = id;
                document.getElementById('targetCardText').innerText = `'${name}' 카드 소유자에게 제안을 보냅니다.`;
                document.getElementById('tradeModal').style.display = 'flex';
            }

            function closeModal(id) {
                document.getElementById(id).style.display = 'none';
            }

            document.getElementById('offerForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                const payload = {
                    inventory_id: parseInt(document.getElementById('targetInventoryId').value),
                    offerer_name: document.getElementById('offererName').value,
                    offered_card: document.getElementById('offeredCard').value,
                    offer_message: document.getElementById('offerMessage').value
                };
                
                const res = await fetch('/api/offers', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (res.ok) {
                    alert('교환 제안이 성공적으로 전송되었습니다.');
                    closeModal('tradeModal');
                    document.getElementById('offerForm').reset();
                }
            });

            async function openInbox() {
                document.getElementById('inboxModal').style.display = 'flex';
                const res = await fetch('/api/my-offers');
                const offers = await res.json();
                const content = document.getElementById('inboxContent');
                content.innerHTML = '';
                
                if(offers.length === 0) {
                    content.innerHTML = '<p style="color:var(--text-sub); text-align:center; padding: 20px 0;">도착한 제안이 없습니다.</p>';
                    return;
                }
                
                offers.forEach(offer => {
                    const item = document.createElement('div');
                    item.className = 'offer-card-item';
                    
                    let statusHtml = '';
                    if(offer.status === 'ACCEPTED') statusHtml = '<b style="color:#2f9e44;">[수락 완료]</b>';
                    else if(offer.status === 'REJECTED') statusHtml = '<b style="color:#fa5252;">[거절됨]</b>';

                    item.innerHTML = `
                        <p style="font-size:0.8rem; color:var(--text-sub);">내 카드: ${offer.my_card_name}</p>
                        <p><b>${offer.offerer_name}</b> 님의 제안 카드: <b>${offer.offered_card}</b></p>
                        <p style="background:white; padding:10px; border-radius:8px; margin-top:8px; border:1px solid #e9ecef;">"${offer.offer_message}"</p>
                        <div style="margin-top:8px;">${statusHtml}</div>
                        ${offer.status === 'PENDING' ? `
                        <div class="action-btns">
                            <button class="btn-act-accept" onclick="respond(${offer.offer_id}, 'ACCEPTED')">수락</button>
                            <button class="btn-act-reject" onclick="respond(${offer.offer_id}, 'REJECTED')">거절</button>
                        </div>
                        ` : ''}
                    `;
                    content.appendChild(item);
                });
            }

            async function respond(id, status) {
                const res = await fetch('/api/offers/respond', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ offer_id: id, status: status })
                });
                if(res.ok) openInbox();
            }

            loadCards();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/cards")
def get_cards():
    conn = sqlite3.connect('pokemon_trade.db')
    cursor = conn.cursor()
    cursor.execute("SELECT inventory_id, card_name, card_grade, image_data, type FROM user_inventory ORDER BY inventory_id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"inventory_id": r[0], "card_name": r[1], "card_grade": r[2], "image_data": r[3], "type": r[4]} for r in rows]

@app.post("/api/cards")
def add_card(item: InventoryItem):
    conn = sqlite3.connect('pokemon_trade.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_inventory (user_id, card_name, card_grade, image_data, type) VALUES (?, ?, ?, ?, ?)",
        (item.user_id, item.card_name, item.card_grade, item.image_data, item.inventory_type)
    )
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/api/cards/{inventory_id}")
def delete_card(inventory_id: int):
    conn = sqlite3.connect('pokemon_trade.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trade_offers WHERE inventory_id = ?", (inventory_id,))
    cursor.execute("DELETE FROM user_inventory WHERE inventory_id = ?", (inventory_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/offers")
def send_offer(offer: TradeOffer):
    conn = sqlite3.connect('pokemon_trade.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO trade_offers (inventory_id, offerer_name, offer_message, offered_card) VALUES (?, ?, ?, ?)",
        (offer.inventory_id, offer.offerer_name, offer.offer_message, offer.offered_card)
    )
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/my-offers")
def get_my_offers():
    conn = sqlite3.connect('pokemon_trade.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.offer_id, o.offerer_name, o.offered_card, o.offer_message, o.status, i.card_name
        FROM trade_offers o
        JOIN user_inventory i ON o.inventory_id = i.inventory_id
        WHERE i.user_id = 1
        ORDER BY o.offer_id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{
        "offer_id": r[0],
        "offerer_name": r[1],
        "offered_card": r[2],
        "offer_message": r[3],
        "status": r[4],
        "my_card_name": r[5]
    } for r in rows]

@app.post("/api/offers/respond")
def respond_offer(response: OfferResponse):
    conn = sqlite3.connect('pokemon_trade.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE trade_offers SET status = ? WHERE offer_id = ?",
        (response.status, response.offer_id)
    )
    conn.commit()
    conn.close()
    return {"status": "success"}