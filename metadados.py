import os
import rawpy
import exifread
from PIL import Image
import pillow_heif  # pip install pillow-heif
import pandas as pd

# Diretório que contém as imagens
DIR = "imagens/"

def parse_filename(fname):
    base = os.path.splitext(fname)[0]
    partes = base.split("_")
    if len(partes) < 3:
        return None
    objeto, iluminacao, camera = partes[0], partes[1], "_".join(partes[2:])
    return objeto, iluminacao, camera

def get_metadata(path, ext):
    meta = {
        "espaco_cor": None,
        "compressao": None,
        "camera_marca": None,
        "camera_modelo": None
    }

    if ext == ".dng":
        try:
            with rawpy.imread(path) as raw:
                # DNG → geralmente RAW sem compressão perceptível
                meta["espaco_cor"] = raw.color_desc
                meta["compressao"] = "RAW (DNG)"
        except:
            pass

        # Tentativa de EXIF complementar
        try:
            with open(path, "rb") as f:
                tags = exifread.process_file(f, details=False)
                meta["camera_marca"] = str(tags.get("Image Make"))
                meta["camera_modelo"] = str(tags.get("Image Model"))
        except:
            pass

    else:
        try:
            img = Image.open(path)
            exif = img.getexif()

            # Espaço de cor
            meta["espaco_cor"] = img.mode

            # Compressão
            if ext == ".jpg":
                meta["compressao"] = "JPEG"
            elif ext == ".heic":
                meta["compressao"] = "HEIC/HEIF"

            # EXIF (se existir)
            if exif:
                meta["camera_marca"] = exif.get(271)   # Make
                meta["camera_modelo"] = exif.get(272)  # Model

        except:
            pass

    return meta

# Estrutura final: { (objeto, ilumi): DataFrame }
tabelas = {}

for fname in os.listdir(DIR):
    path = os.path.join(DIR, fname)
    if not os.path.isfile(path):
        continue

    ext = os.path.splitext(fname)[1].lower()
    if ext not in [".dng", ".jpg", ".jpeg", ".heic"]:
        continue

    info = parse_filename(fname)
    if not info:
        continue

    objeto, iluminacao, camera = info

    meta = get_metadata(path, ext)
    meta.update({
        "arquivo": fname,
        "camera": camera,
        "extensao": ext
    })

    chave = (objeto, iluminacao)

    if chave not in tabelas:
        tabelas[chave] = []

    tabelas[chave].append(meta)

# Convertendo listas para DataFrames
for chave in tabelas:
    tabelas[chave] = pd.DataFrame(tabelas[chave])

# --- Exemplo de uso ---
# mostrar tabelas encontradas
for (obj, ilum), tabela in tabelas.items():
    print(f"\n===== Tabela: objeto={obj}, iluminacao={ilum} =====")
    print(tabela)
