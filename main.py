from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
import tempfile
import os
import uvicorn
import subprocess

app = FastAPI()

def compress_video(input_video_path, output_video_path, crf_value=28):
    # Comando FFmpeg para compressão do vídeo
    command = [
        'ffmpeg',
        '-i', input_video_path,
        '-vcodec', 'libx264',
        '-preset', 'ultrafast',
        '-crf', str(crf_value),
        '-acodec', 'aac',
        '-y',  # Sobrescreve o arquivo de saída, se existir
        output_video_path
    ]
    try:
        # Executa o comando FFmpeg e captura saída e erros
        result = subprocess.run(
            command, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode()
        print("Erro durante a compressão:", error_message)
        raise Exception(f"Falha na compressão do vídeo: {error_message}")

def cleanup_file(path: str):
    try:
        os.remove(path)
    except Exception as e:
        print(f"Falha ao remover o arquivo {path}: {e}")

@app.post("/compress/")
async def compress_video_api(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    crf: int = 28
):
    # Cria arquivo temporário para o input
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_input:
        input_path = temp_input.name
        temp_input.write(await video.read())

    # Cria arquivo temporário para o output
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
        output_path = temp_output.name

    try:
        compress_video(input_path, output_path, crf)
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
