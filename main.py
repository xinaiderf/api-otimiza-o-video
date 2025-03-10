from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from moviepy.editor import VideoFileClip
import tempfile
import os
import uvicorn

app = FastAPI()

def compress_video(input_video_path, output_video_path, crf_value=28):
    # Usa o gerenciador de contexto para garantir que o vídeo seja fechado após a conversão
    with VideoFileClip(input_video_path) as video_clip:
        video_clip.write_videofile(
            output_video_path,
            codec="libx264",         # Codec para compressão eficiente
            audio_codec="aac",        # Codec de áudio para compatibilidade
            preset="ultrafast",       # Preset para acelerar o processo (pode aumentar o tamanho do arquivo)
            ffmpeg_params=["-crf", str(crf_value)],  # Ajusta o valor de CRF para a compressão
            logger=None,              # Desativa logs detalhados para melhorar a performance
            progress_bar=False        # Remove a barra de progresso para reduzir overhead
        )

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
