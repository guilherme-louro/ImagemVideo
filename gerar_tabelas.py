import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

class GeradorTabelasMinimalista:
    def __init__(self, csv_path: str):
        """Inicializa com o arquivo CSV"""
        self.df = pd.read_csv(csv_path)
    
    def criar_tabela_grupo(self, df_grupo: pd.DataFrame, objeto: str, tipo_luz: str, output_dir: str):
        """Cria uma tabela para um grupo específico"""
        
        # Criar DataFrame com a ordem de colunas exata
        dados_tabela = pd.DataFrame({
            'Objeto': [objeto] * len(df_grupo),
            'Luz': df_grupo['Luz'],
            'Camera': df_grupo['Camera'],
            'SSIM': df_grupo['SSIM'].apply(lambda x: f"{x:.4f}"),
            'MSE': df_grupo['MSE'].apply(lambda x: f"{x:.2f}")
        })
        
        # Ordenar por Camera e Luz
        dados_tabela = dados_tabela.sort_values(['Camera', 'Luz'])
        
        # Configurar figura
        num_linhas = len(dados_tabela)
        fig, ax = plt.subplots(figsize=(12, max(4, num_linhas * 0.3)))
        ax.axis('off')
        
        # Criar tabela
        tabela = ax.table(
            cellText=dados_tabela.values,
            colLabels=dados_tabela.columns,
            cellLoc='center',
            loc='center',
            colWidths=[0.15, 0.15, 0.25, 0.25, 0.25]  # Ajustar larguras
        )
        
        # Estilização mínima - SEM CORES ALTERNADAS
        tabela.auto_set_font_size(False)
        tabela.set_fontsize(10)
        tabela.scale(1.2, 1.8)
        
        # Cabeçalho simples
        for j in range(len(dados_tabela.columns)):
            cell = tabela[(0, j)]
            cell.set_facecolor('#f0f0f0')  # Cinza muito claro
            cell.set_text_props(weight='bold', color='black')
        
        # Linhas do corpo - todas brancas, sem formatação especial
        for i in range(1, num_linhas + 1):
            for j in range(len(dados_tabela.columns)):
                cell = tabela[(i, j)]
                cell.set_facecolor('white')
        
        # Salvar imagem
        nome_arquivo = f"{objeto}_{tipo_luz}.png"
        caminho = os.path.join(output_dir, nome_arquivo)
        
        plt.tight_layout()
        plt.savefig(caminho, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        
        return caminho
    
    def gerar_todas_tabelas(self, output_dir: str = 'tabelas_simples'):
        """Gera todas as tabelas separadas por objeto e tipo de luz"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Extrair tipo básico de luz
        def get_tipo_luz(classificacao):
            return 'amarela' if 'amarela' in str(classificacao).lower() else 'branca'
        
        self.df['Tipo_Luz'] = self.df['Classificacao_Luz'].apply(get_tipo_luz)
        
        tabelas_geradas = []
        
        # Processar cada combinação Objeto x Tipo_Luz
        grupos = self.df.groupby(['Objeto', 'Tipo_Luz'])
        
        for (objeto, tipo_luz), grupo in grupos:
            try:
                caminho = self.criar_tabela_grupo(grupo, objeto, tipo_luz, output_dir)
                tabelas_geradas.append(caminho)
                print(f"✓ {objeto}_{tipo_luz}.png")
            except Exception as e:
                print(f"✗ Erro em {objeto}_{tipo_luz}: {e}")
        
        return tabelas_geradas

def main():
    """Função principal"""
    
    # Configurações padrão
    csv_path = 'resultados_metricas.csv'
    output_dir = 'tabelas_resultado'
    
    # Aceitar argumentos da linha de comando
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    # Verificar se o arquivo existe
    if not os.path.exists(csv_path):
        print(f"Arquivo não encontrado: {csv_path}")
        return
    
    print("Gerando tabelas...")
    print(f"CSV: {csv_path}")
    print(f"Saída: {output_dir}")
    print("-" * 40)
    
    try:
        gerador = GeradorTabelasMinimalista(csv_path)
        tabelas = gerador.gerar_todas_tabelas(output_dir)
        
        print("\n" + "=" * 40)
        print(f"Concluído! {len(tabelas)} tabelas geradas em '{output_dir}'")
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main()