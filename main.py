from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
import tempfile
import os
import uvicorn
import asyncio
import subprocess

app = FastAPI()

def compress_video_ffmpeg(input_video_path, output_video_path, scale_factor=0.5):
    """
    Utiliza o FFmpeg dentro de um container Docker para redimensionar o vídeo.
    Essa abordagem garante o uso de uma versão do FFmpeg compatível com a libc 2.35.
    """
    # Assume que os arquivos temporários estão no mesmo diretório (geralmente /tmp)
    common_dir = os.path.dirname(input_video_path)
    input_filename = os.path.basename(input_video_path)
    output_filename = os.path.basename(output_video_path)
    
    # Monta o comando Docker que executa o FFmpeg do container.
    # Aqui usamos uma imagem que utiliza uma versão compatível com a libc 2.35,
    # por exemplo, "jrottenberg/ffmpeg:4.3.1-ubuntu".
    command = [
        "docker", "run", "--rm",
        "-v", f"{common_dir}:/tmp",
        "jrottenberg/ffmpeg:4.3.1-ubuntu",
        "-y",  # sobrescreve arquivo de saída se existir
        "-i", f"/tmp/{input_filename}",
        "-vf", f"scale=iw*{scale_factor}:ih*{scale_factor}",
        f"/tmp/{output_filename}"
    ]
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        error_msg = result.stderr.decode('utf-8')
        raise Exception(f"Erro ao processar o vídeo: {error_msg}")

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
    realiza a compressão utilizando FFmpeg via Docker e retorna o vídeo otimizado.
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
        await loop.run_in_executor(None, compress_video_ffmpeg, input_path, output_path, scale)
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
