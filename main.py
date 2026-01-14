from fastapi import FastAPI
from routers import users, posts,comments,likes

app = FastAPI(title="Social Media API")

app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(likes.router)

@app.get("/")
def home():
    return {"message": "서버 정상 가동 중. /docs로 접속하세요."}