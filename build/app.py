from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import tempfile
import subprocess
import os

app = FastAPI()

@app.post("/convert")
async def convert_audio(file: UploadFile = File(...)):
    # Einfacher Check
    if not file.filename.lower().endswith(".m4a"):
        raise HTTPException(status_code=400, detail="Nur .m4a wird akzeptiert")

    # Temporäre Dateien
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.m4a")
        output_path = os.path.join(tmpdir, "output.mp3")

        # Upload speichern
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # ffmpeg ausführen
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-codec:a", "libmp3lame",
            "-qscale:a", "2",
            output_path,
        ]

        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail="ffmpeg Fehler: " + process.stderr.decode(errors="ignore"))

        # MP3 zurückgeben
        def iterfile():
            with open(output_path, "rb") as f:
                while True:
                    chunk = f.read(1024 * 1024)
                    if not chunk:
                        break
                    yield chunk

        return StreamingResponse(
            iterfile(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f'attachment; filename="{os.path.splitext(file.filename)[0]}.mp3"'
            }
        )