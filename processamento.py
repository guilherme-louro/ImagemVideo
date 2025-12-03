import os
from PIL import Image
from pillow_heif import register_heif_opener
import logging

# Registrar opener para imagens HEIC
register_heif_opener()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def processar_imagens():
    # Lista de pastas a serem processadas
    pastas_origem = ['caneca', 'controle', 'jk', 'stitch', 'urso']
    
    # Configurações
    tamanho_final = (1944, 1944)  # 1944x1944 pixels
    
    for pasta in pastas_origem:
        # Verificar se a pasta de origem existe
        if not os.path.exists(pasta):
            logging.warning(f"Pasta '{pasta}' não encontrada. Pulando...")
            continue
        
        # Criar pasta de destino
        pasta_destino = f"{pasta}_resize"
        os.makedirs(pasta_destino, exist_ok=True)
        logging.info(f"Processando pasta: {pasta} -> {pasta_destino}")
        
        # Processar cada imagem na pasta
        imagens_processadas = 0
        erros = 0
        
        for arquivo in os.listdir(pasta):
            # Verificar se é uma imagem (suporta vários formatos)
            extensoes_validas = ('.jpg', '.jpeg', '.png', '.heic', '.HEIC', '.bmp', '.gif')
            if not arquivo.lower().endswith(extensoes_validas):
                continue
            
            caminho_origem = os.path.join(pasta, arquivo)
            
            try:
                # Abrir imagem
                with Image.open(caminho_origem) as img:
                    # Converter para RGB se necessário (para imagens com transparência)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # Obter dimensões originais
                    largura, altura = img.size
                    
                    # 1. Criar imagem quadrada centralizada (lado = altura)
                    if largura > altura:
                        # Se a largura for maior, cortar as laterais
                        esquerda = (largura - altura) // 2
                        direita = esquerda + altura
                        img_quadrada = img.crop((esquerda, 0, direita, altura))
                    elif largura < altura:
                        # Se a altura for maior, criar uma nova imagem com fundo branco
                        img_quadrada = Image.new('RGB', (altura, altura), (255, 255, 255))
                        # Colar a imagem original no centro
                        esquerda = (altura - largura) // 2
                        img_quadrada.paste(img, (esquerda, 0))
                    else:
                        # Já é quadrada
                        img_quadrada = img
                    
                    # 2. Redimensionar para 1944x1944
                    img_redimensionada = img_quadrada.resize(tamanho_final, Image.Resampling.LANCZOS)
                    
                    # 3. Salvar a imagem
                    # Mudar extensão para .jpg (opcional, pode manter a original)
                    nome_arquivo, _ = os.path.splitext(arquivo)
                    caminho_destino = os.path.join(pasta_destino, f"{nome_arquivo}.jpg")
                    
                    # Salvar como JPEG com qualidade 95%
                    img_redimensionada.save(caminho_destino, 'JPEG', quality=95, optimize=True)
                    
                    imagens_processadas += 1
                    logging.info(f"  ✓ Processado: {arquivo} -> {nome_arquivo}.jpg")
                    
            except Exception as e:
                erros += 1
                logging.error(f"  ✗ Erro ao processar {arquivo}: {str(e)}")
        
        logging.info(f"Pasta {pasta}: {imagens_processadas} imagens processadas, {erros} erros")
    
    logging.info("Processamento concluído!")

if __name__ == "__main__":
    processar_imagens()