import os
import subprocess
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

app = FastAPI()


def cleanup_files(*files: str):
    """Função auxiliar para remover arquivos temporários."""
    for file in files:
        try:
            os.remove(file)
        except Exception as e:
            print(f"Erro ao remover {file}: {e}")


@app.post("/optimize-video")
async def optimize_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    # Salva o arquivo recebido em um arquivo temporário
    try:
        suffix = os.path.splitext(file.filename)[1] or ".mp4"
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
            input_filename = tmp_in.name
            content = await file.read()
            tmp_in.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {e}")

    # Define o nome do arquivo de saída
    output_filename = input_filename + "_optimized.mp4"

    # Comando do ffmpeg para otimizar o vídeo:
    # - Reencode com codec H.264 para vídeo (libx264)
    # - Reencode com codec AAC para áudio
    # - Define uma taxa de bits para o vídeo (ex.: 1000k)
    command = [
        "ffmpeg",
        "-i", input_filename,
        "-vcodec", "libx264",
        "-acodec", "aac",
        "-b:v", "1000k",
        "-y",  # sobrescreve arquivo de saída se existir
        output_filename
    ]

    try:
        # Executa o comando do ffmpeg
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        # Limpa o arquivo de entrada em caso de erro
        cleanup_files(input_filename)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao otimizar vídeo: {e.stderr.decode('utf-8')}"
        )

    # Agenda a remoção dos arquivos temporários após a resposta ser enviada
    background_tasks.add_task(cleanup_files, input_filename, output_filename)

    # Retorna o vídeo otimizado como resposta
    return FileResponse(
        path=output_filename,
        media_type="video/mp4",
        filename="optimized.mp4"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8011, reload=True)
