from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from moviepy import VideoFileClip
import tempfile
import os
import uvicorn

app = FastAPI()

def compress_video(input_video_path, output_video_path, crf_value=28):
    # Carregar o vídeo original
    video_clip = VideoFileClip(input_video_path)
    
    # Escrever o vídeo comprimido com configurações otimizadas
    video_clip.write_videofile(
        output_video_path,
        codec="libx264",  # Codec utilizado para compressão eficiente
        audio_codec="aac",  # Codec de áudio para compatibilidade
        threads=4,  # Utilize 4 threads para acelerar a compressão
        preset="ultrafast",  # Preset para acelerar o processo (pode aumentar o tamanho do arquivo)
        ffmpeg_params=["-crf", str(crf_value)],  # Ajusta o valor de CRF para a compressão
        logger=None  # Desativa logs detalhados para melhorar performance
    )

@app.post("/compress/")
async def compress_video_api(video: UploadFile = File(...), crf: int = 28):
    # Usando NamedTemporaryFile para garantir que o arquivo temporário seja criado corretamente
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_input_video:
        temp_input_video.write(await video.read())
        temp_input_video_path = temp_input_video.name
    
    # Usando NamedTemporaryFile para o arquivo de saída
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output_video:
        temp_output_video_path = temp_output_video.name
    
    try:
        # Chamar a função para compactar o vídeo
        compress_video(temp_input_video_path, temp_output_video_path, crf)
        
        # Retornar o vídeo comprimido como resposta
        return FileResponse(temp_output_video_path, media_type='video/mp4', filename='compressed_video.mp4')
    except Exception as e:
        return {"error": str(e)}
    finally:
        # Limpeza dos arquivos temporários
        os.remove(temp_input_video_path)
        os.remove(temp_output_video_path)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8011)
