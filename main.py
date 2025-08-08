import os
import shutil
import uuid
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
from amzqr import amzqr

app = FastAPI()

# Vercel 환경은 /tmp 디렉토리에만 파일 쓰기를 허용합니다.
TEMP_DIR = "/tmp/temp_images"
OUTPUT_DIR = "/tmp/generated_qrs"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

@app.post("/generate-qr")
async def generate_qr(
    image: UploadFile = File(...),
    data: str = Form(...),
    color: str = Form(...),
    version: int = Form(...)
):
    try:
        # 1. 업로드된 이미지 임시 저장
        temp_image_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_{image.filename}")
        with open(temp_image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # 2. QR 코드 생성 준비
        is_color = color.lower() == 'color'
        
        # amzqr 라이브러리는 파일 이름을 직접 제어하기 어려워, 생성 후 파일명을 예측해야 함
        # 라이브러리 기본 동작: {data}_{level}_{version}_{colored or not}_{picture_name}.gif
        # 여기서는 간단하게 고유한 파일명을 만들고, 생성 후 해당 파일을 찾습니다.
        unique_name = f"{uuid.uuid4()}.gif"
        output_path = os.path.join(OUTPUT_DIR, unique_name)

        # Vercel 환경의 읽기 전용 파일 시스템 오류를 해결하기 위해 HOME을 /tmp로 설정
        original_home = os.environ.get("HOME")
        os.environ["HOME"] = "/tmp"

        try:
            # 3. amazing-qr 실행
            # amzqr.run()은 (성공여부, 최종 파일명) 튜플을 반환합니다.
            version, level, qr_name = amzqr.run(
                words=data,
                version=version,  # QR 코드 버전 (복잡도)
                level='H',   # 오류 복원 수준 (L, M, Q, H)
                picture=temp_image_path,
                colorized=is_color,
                contrast=1.0,
                brightness=1.0,
                save_name=unique_name, # 저장될 파일명 지정
                save_dir=OUTPUT_DIR
            )
        finally:
            # HOME 환경 변수를 원래대로 복원
            if original_home is None:
                del os.environ["HOME"]
            else:
                os.environ["HOME"] = original_home

        # 4. 임시 이미지 파일 삭제
        os.remove(temp_image_path)

        if not os.path.exists(output_path):
             raise HTTPException(status_code=500, detail=f"QR 코드 파일 생성 실패: {qr_name}")

        # 5. 생성된 QR 코드를 FileResponse로 직접 반환하고, 전송 후 파일을 삭제합니다.
        return FileResponse(output_path, media_type="image/gif", background=BackgroundTask(os.remove, output_path))

    except Exception as e:
        # 오류 발생 시 임시 파일이 있다면 삭제
        if 'temp_image_path' in locals() and os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        # QR 코드 생성 과정에서 실패했다면, 생성된 파일도 삭제 시도
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
        raise HTTPException(status_code=500, detail=str(e))

# 정적 파일 제공
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# 앱 실행을 위한 uvicorn 설정 (터미널에서 직접 실행 시)
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

#  uvicorn main:app --reload 