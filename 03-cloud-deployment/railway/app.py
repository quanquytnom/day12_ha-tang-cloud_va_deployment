"""
Agent Railway-ready.
Railway inject PORT env var tự động — agent phải dùng os.getenv("PORT").
"""
import os
import time
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from utils.mock_llm import ask

app = FastAPI(title="Agent on Railway", version="1.0.0")
START_TIME = time.time()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


HTML_PAGE = """
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Agent</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto;
           padding: 0 16px; background: #0f172a; color: #e2e8f0; }
    h1 { font-size: 1.5rem; }
    .box { background: #1e293b; border-radius: 12px; padding: 20px; margin-top: 16px; }
    textarea { width: 100%; box-sizing: border-box; padding: 10px; border-radius: 8px;
               border: 1px solid #334155; background: #0f172a; color: #e2e8f0; font-size: 1rem; }
    button { margin-top: 12px; padding: 10px 20px; border: none; border-radius: 8px;
             background: #6366f1; color: white; font-size: 1rem; cursor: pointer; }
    button:disabled { opacity: .5; cursor: not-allowed; }
    #out { margin-top: 16px; white-space: pre-wrap; min-height: 24px; line-height: 1.5; }
    .muted { color: #94a3b8; font-size: .85rem; }
  </style>
</head>
<body>
  <h1>🤖 AI Agent</h1>
  <p class="muted">Hỏi gì đó rồi bấm Gửi. Câu trả lời đến từ agent đang chạy trên cloud.</p>
  <div class="box">
    <textarea id="q" rows="3" placeholder="Ví dụ: What is Docker?"></textarea>
    <button id="btn" onclick="ask()">Gửi</button>
    <div id="out"></div>
  </div>

  <script>
    async function ask() {
      const q = document.getElementById('q').value.trim();
      const out = document.getElementById('out');
      const btn = document.getElementById('btn');
      if (!q) { out.textContent = 'Hãy nhập câu hỏi.'; return; }
      btn.disabled = true;
      out.textContent = 'Đang hỏi...';
      try {
        const res = await fetch('/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: q })
        });
        const data = await res.json();
        out.textContent = data.answer || JSON.stringify(data);
      } catch (e) {
        out.textContent = 'Lỗi: ' + e;
      } finally {
        btn.disabled = false;
      }
    }
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def root():
    """Trang UI chat — phục vụ HTML ngay tại trang chủ."""
    return HTML_PAGE


@app.post("/ask")
async def ask_agent(request: Request):
    body = await request.json()
    question = body.get("question", "")
    if not question:
        raise HTTPException(422, "question required")
    return {
        "question": question,
        "answer": ask(question),
        "platform": "Railway",
    }


@app.get("/health")
def health():
    """
    Railway sẽ check endpoint này định kỳ.
    Trả về 200 = healthy. Non-200 = Railway restart container.
    """
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "platform": "Railway",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    # ✅ Railway inject PORT — PHẢI đọc từ env
    port = int(os.getenv("PORT", 8000))
    print(f"Starting on port {port} (from PORT env var)")
    uvicorn.run(app, host="0.0.0.0", port=port)
