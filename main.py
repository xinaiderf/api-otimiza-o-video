from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
import tempfile
import os
import uvicorn
import cv2
import asyncio

app = FastAPI()

def compress_video_opencv(input_video_path, output_video_path, scale_factor=0.5):
    """
    Abre o vídeo de entrada, redimensiona os frames pelo scale_factor e regrava o vídeo.
    Uma redução na resolução pode diminuir o tamanho do arquivo, funcionando como uma otimização.
    """
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        raise Exception("Erro ao abrir o vídeo de entrada.")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Define nova resolução
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    
    # Define o codec e cria o VideoWriter; 'mp4v' é geralmente compatível com MP4
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (new_width, new_height))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Redimensiona o frame
        resized_frame = cv2.resize(frame, (new_width, new_height))
        out.write(resized_frame)
    
    cap.release()
    out.release()

def cleanup_file(path: str):
    try:
        os.remove(path)
    except Exception as e:
        print(f"Erro ao remover o arquivo {path}: {e}")

@app.post("/compress/")
async def compress_video_api(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    scale: float = 0.5
):
    """
    Endpoint que recebe o vídeo e um fator de escala (padrão 0.5, ou seja, 50% da resolução original),
    realiza a compressão utilizando OpenCV e retorna o vídeo otimizado.
    """
    # Salva o vídeo enviado em um arquivo temporário
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_input:
        input_path = temp_input.name
        temp_input.write(await video.read())
    
    # Cria um arquivo temporário para o vídeo de saída
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_output:
        output_path = temp_output.name

    try:
        # Executa a compressão em um executor para não bloquear o event loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, compress_video_opencv, input_path, output_path, scale)
    except Exception as e:
        cleanup_file(input_path)
        cleanup_file(output_path)
        return {"error": str(e)}
    
    # Agenda a remoção dos arquivos temporários após o envio da resposta
    background_tasks.add_task(cleanup_file, input_path)
    background_tasks.add_task(cleanup_file, output_path)
    
    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename="compressed_video.mp4"
    )

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8011)
