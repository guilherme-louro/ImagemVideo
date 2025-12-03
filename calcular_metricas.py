import os
import pandas as pd
import numpy as np
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import mean_squared_error as mse
from skimage.io import imread
from skimage.color import rgb2gray
import logging
from typing import Dict, Tuple

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AnalisadorImagens:
    def __init__(self):
        # Mapeamento de classificação de luz
        self.classificacao_luz = {
            'inc100': 'amarela forte',
            'inc40': 'amarela fraca',
            'd65': 'branca forte',
            'd50': 'branca fraca'
        }
        
        # Mapeamento de câmeras (baseado nos padrões de nome de arquivo)
        self.padroes_camera = {
            'dsc-h50': 'Sony DSC-H50',
            '15pro': 'iPhone 15 Pro',
            's24': 'Samsung S24',
            's20fe': 'Samsung S20 FE',
        }
    
    def detectar_camera(self, nome_arquivo: str) -> str:
        """Detecta a câmera usada baseado no nome do arquivo"""
        nome_lower = nome_arquivo.lower()
        
        for padrao, camera in self.padroes_camera.items():
            if padrao in nome_lower:
                return camera
        
        # Se não encontrar padrão conhecido, extrai do nome
        partes = nome_lower.split('_')
        if len(partes) >= 3:
            return partes[-1].split('.')[0].upper()
        
        return 'Desconhecida'
    
    def detectar_luz(self, nome_arquivo: str) -> Tuple[str, str]:
        """Detecta o tipo de luz e sua classificação"""
        nome_lower = nome_arquivo.lower()
        
        for luz in ['inc100', 'inc40', 'd65', 'd50']:
            if luz in nome_lower:
                classificacao = self.classificacao_luz.get(luz, 'Desconhecida')
                return luz.upper(), classificacao
        
        # Tentar encontrar padrões alternativos
        if 'inc' in nome_lower:
            return 'INC', 'amarela'
        elif 'd' in nome_lower:
            return 'D', 'branca'
        
        return 'Desconhecida', 'Desconhecida'
    
    def calcular_metricas(self, img_ref, img_comp):
        """Calcula SSIM e MSE entre duas imagens"""
        try:
            # Converter para escala de cinza para SSIM
            img_ref_gray = rgb2gray(img_ref)
            img_comp_gray = rgb2gray(img_comp)
            
            # Calcular SSIM
            ssim_value = ssim(
                img_ref_gray, 
                img_comp_gray,
                data_range=img_ref_gray.max() - img_ref_gray.min(),
                win_size=7  # Tamanho da janela para SSIM
            )
            
            # Calcular MSE para cada canal e tirar a média
            mse_r = mse(img_ref[:,:,0], img_comp[:,:,0])
            mse_g = mse(img_ref[:,:,1], img_comp[:,:,1])
            mse_b = mse(img_ref[:,:,2], img_comp[:,:,2])
            mse_value = (mse_r + mse_g + mse_b) / 3
            
            return ssim_value, mse_value
            
        except Exception as e:
            logging.error(f"Erro ao calcular métricas: {e}")
            return None, None
    
    def processar_pasta(self, pasta_objeto: str):
        """Processa uma pasta de objeto (ex: caneca_resize)"""
        dados = []
        nome_objeto = pasta_objeto.replace('_resize', '')
        
        logging.info(f"Processando objeto: {nome_objeto}")
        
        # Verificar subpastas
        subpastas = ['amarela', 'branca']
        
        for subpasta in subpastas:
            caminho_subpasta = os.path.join(pasta_objeto, subpasta)
            
            if not os.path.exists(caminho_subpasta):
                logging.warning(f"Subpasta não encontrada: {caminho_subpasta}")
                continue
            
            # Determinar imagem de referência baseado na subpasta
            if subpasta == 'amarela':
                padrao_ref = f"{nome_objeto}_INC100_DSC-H50"
            else:  # branca
                padrao_ref = f"{nome_objeto}_D65_DSC-H50"
            
            # Encontrar imagem de referência
            imagem_ref = None
            caminho_ref = None
            
            for arquivo in os.listdir(caminho_subpasta):
                if padrao_ref.lower() in arquivo.lower():
                    caminho_ref = os.path.join(caminho_subpasta, arquivo)
                    break
            
            if not caminho_ref:
                logging.warning(f"Imagem de referência não encontrada para {nome_objeto}/{subpasta}")
                continue
            
            # Carregar imagem de referência
            try:
                imagem_ref = imread(caminho_ref)
                logging.info(f"Carregada referência: {os.path.basename(caminho_ref)}")
            except Exception as e:
                logging.error(f"Erro ao carregar imagem de referência: {e}")
                continue
            
            # Processar outras imagens
            for arquivo in os.listdir(caminho_subpasta):
                caminho_arquivo = os.path.join(caminho_subpasta, arquivo)
                
                # Pular a imagem de referência
                if caminho_arquivo == caminho_ref:
                    continue
                
                # Verificar se é uma imagem
                if not arquivo.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    continue
                
                try:
                    # Carregar imagem para comparação
                    img_comp = imread(caminho_arquivo)
                    
                    # Verificar se as imagens têm o mesmo tamanho
                    if imagem_ref.shape != img_comp.shape:
                        logging.warning(f"Tamanhos diferentes: {arquivo} {imagem_ref.shape} vs {img_comp.shape}")
                        # Redimensionar se necessário (opcional)
                        continue
                    
                    # Calcular métricas
                    ssim_val, mse_val = self.calcular_metricas(imagem_ref, img_comp)
                    
                    if ssim_val is not None and mse_val is not None:
                        # Extrair informações do nome do arquivo
                        camera = self.detectar_camera(arquivo)
                        luz, classificacao_luz = self.detectar_luz(arquivo)
                        
                        # Adicionar aos dados apenas os atributos solicitados
                        dados.append({
                            'Objeto': nome_objeto,
                            'Camera': camera,
                            'Luz': luz,
                            'Classificacao_Luz': classificacao_luz,
                            'SSIM': round(ssim_val, 4),
                            'MSE': round(mse_val, 2)
                        })
                        
                        logging.info(f"  Processado: {arquivo} - SSIM: {ssim_val:.4f}, MSE: {mse_val:.2f}")
                    
                except Exception as e:
                    logging.error(f"Erro ao processar {arquivo}: {e}")
        
        return dados
    
    def gerar_relatorio_csv(self, dados_totais):
        """Gera relatório CSV apenas com os atributos solicitados"""
        if not dados_totais:
            logging.warning("Nenhum dado para gerar relatório")
            return
        
        # Criar DataFrame apenas com as colunas solicitadas
        df = pd.DataFrame(dados_totais)
        
        # Ordenar as colunas como solicitado
        colunas = ['Objeto', 'Camera', 'Luz', 'Classificacao_Luz', 'SSIM', 'MSE']
        df = df[colunas]
        
        # Ordenar os dados por Objeto e Camera para melhor organização
        df = df.sort_values(['Objeto', 'Camera', 'Luz'])
        
        # Salvar em CSV
        nome_arquivo = 'resultados_metricas.csv'
        df.to_csv(nome_arquivo, index=False, encoding='utf-8')
        logging.info(f"Arquivo CSV criado: {nome_arquivo}")
        
        return df
    

def main():
    """Função principal"""
    analisador = AnalisadorImagens()
    dados_totais = []
    
    # Lista de pastas a serem processadas
    pastas_objetos = ['caneca_resize', 'controle_resize', 'jk_resize', 'stitch_resize', 'urso_resize']
    
    # Processar cada pasta
    for pasta in pastas_objetos:
        if os.path.exists(pasta):
            dados = analisador.processar_pasta(pasta)
            dados_totais.extend(dados)
        else:
            logging.warning(f"Pasta não encontrada: {pasta}")
    
    # Gerar relatório em CSV
    if dados_totais:
        df = analisador.gerar_relatorio_csv(dados_totais)
        print(f"\n✅ Relatório gerado com sucesso!")

    else:
        print("❌ Nenhum dado foi processado.")

if __name__ == "__main__":
    main()