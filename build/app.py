from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
import tempfile
import subprocess
import os
from pathlib import Path

app = FastAPI()

@app.post("/convert")
async def convert_audio(file: UploadFile = File(...)):
    # Dateiname + Endung ermitteln (zur Not Default)
    original_name = file.filename or "audio.m4a"
    suffix = Path(original_name).suffix or ".m4a"

    # Kein harter Check mehr auf ".m4a" – ffmpeg kommt mit den Bytes klar,
    # egal wie die Datei heißt.
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, f"input{suffix}")
        output_path = os.path.join(tmpdir, "output.mp3")

        # Upload speichern
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # ffmpeg ausführen
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-codec:a", "libmp3lame",
            "-qscale:a", "2",
            output_path,
        ]
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if process.returncode != 0 or not os.path.exists(output_path):
            # ffmpeg ist gescheitert – Log zurückgeben
            err = process.stderr.decode(errors="ignore")
            raise HTTPException(status_code=500, detail=f"ffmpeg error: {err}")

        # MP3 einlesen, solange der Temp-Ordner noch existiert
        with open(output_path, "rb") as f:
            data = f.read()

    # Hier ist der Temp-Ordner schon weg – aber "data" liegt im Speicher 👍
    return Response(
        content=data,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'attachment; filename="{Path(original_name).stem}.mp3"'
        }
    )