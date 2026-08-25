import os
import sqlite3
import hashlib
import logging
import base64
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, List, Tuple
import pandas as pd
import streamlit as st

# ============================================================
# CONFIGURACAO DE LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sistema.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURACOES DO SISTEMA
# ============================================================

APP_TITLE = "Sistema de Gestao Documental - Governo Provincial"
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "database.db")))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
LOGO_PATH = BASE_DIR / "OIP.webp"

# ============================================================
# 👉 VIDEO DE FUNDO
# ============================================================
BACKGROUND_VIDEO = BASE_DIR / 'Provincial_Government_of_Huila_b…_202608231007.mp4'

# ============================================================
# CONFIGURACAO STREAMLIT
# ============================================================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else ":material/account_balance:",
    layout="wide",
    initial_sidebar_state="expanded"
)

if LOGO_PATH.exists():
    st.logo(str(LOGO_PATH), size="large", icon_image=str(LOGO_PATH))

# ============================================================
# FUNÇÃO PARA CARREGAR VIDEO DE FUNDO
# ============================================================

def get_background_video_css(video_path: Path | str | None = None) -> str:
    """Gera o CSS do vídeo de fundo sem o carregar duas vezes."""
    if video_path and Path(video_path).exists():
        return """
            .video-background {
                position: fixed;
                inset: 0;
                z-index: -1;
                width: 100vw;
                height: 100vh;
                object-fit: cover;
                pointer-events: none;
            }
            .video-overlay {
                position: fixed;
                inset: 0;
                z-index: 0;
                pointer-events: none;
            }
        """

    logger.warning(f"Vídeo não encontrado: {video_path}")
    return """
        .stApp {
            background: linear-gradient(135deg, #111111 0%, #450814 100%);
        }
    """


@st.cache_data(show_spinner=False)
def get_video_base64(video_path: str, modified_at: float) -> str:
    """Codifica o vídeo uma vez por versão do ficheiro."""
    del modified_at
    with open(video_path, "rb") as video_file:
        return base64.b64encode(video_file.read()).decode("ascii")

# ============================================================
# ESTILOS CSS - DESIGN GOVERNAMENTAL PROFISSIONAL
# ============================================================

def inject_custom_css():
    """Injeta estilos CSS personalizados com design profissional"""
    
    background_css = get_background_video_css(BACKGROUND_VIDEO)
    
    # Verificar se o vídeo existe
    video_path = Path(BACKGROUND_VIDEO)
    video_exists = video_path.exists()
    video_base64 = ""
    if video_exists:
        try:
            video_base64 = get_video_base64(
                str(video_path), video_path.stat().st_mtime
            )
        except Exception as e:
            logger.error(f"Erro ao ler vídeo: {e}")
    
    st.markdown(f"""
        <style>
        :root {{
            --azul-profundo: #111111;
            --azul-principal: #C8102E;
            --azul-claro: #E51B23;
            --dourado: #F7C600;
            --branco-puro: #FFFFFF;
            --cinza-claro: #F8FAFC;
            --cinza-medio: #E2E8F0;
            --texto-escuro: #1A202C;
            --texto-secundario: #4A5568;
            --sombra-leve: 0 2px 8px rgba(11, 45, 71, 0.08);
            --sombra-media: 0 8px 24px rgba(11, 45, 71, 0.12);
            --sombra-forte: 0 16px 48px rgba(11, 45, 71, 0.16);
        }}

        /* ===== VIDEO DE FUNDO - MUITO VISÍVEL ===== */
        {background_css}
        
        /* Remover fundo branco do container principal */
        .main .block-container {{
            padding: 1.5rem 2rem;
            background: transparent !important;
            border-radius: 0px;
            margin: 0 auto;
            box-shadow: none;
            max-width: 1320px;
            position: relative;
            z-index: 1;
        }}
        
        /* Forçar o container principal a ser transparente */
        .stApp {{
            background: transparent !important;
        }}
        
        /* ===== OVERLAY DO VIDEO - LEVE E DISCRETO ===== */
        .video-overlay {{
            background: linear-gradient(
                135deg, 
                rgba(17, 17, 17, 0.45), 
                rgba(110, 8, 30, 0.28)
            ), 
            rgba(0, 0, 0, 0.16);
            backdrop-filter: blur(2px);
        }}
        
        /* ===== SIDEBAR - REFINADA ===== */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(
                180deg, 
                rgba(17, 17, 17, 0.93) 0%, 
                rgba(93, 7, 27, 0.93) 100%
            );
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            padding: 1.5rem 1rem;
            border-right: 1px solid rgba(212, 165, 116, 0.25);
            position: relative;
            z-index: 2;
        }}
        
        section[data-testid="stSidebar"] * {{
            color: #E8F1F8 !important;
        }}
        
        section[data-testid="stSidebar"] .stButton > button {{
            background: linear-gradient(
                135deg, 
                rgba(200, 16, 46, 0.92), 
                rgba(17, 17, 17, 0.92)
            );
            color: white !important;
            border: 1px solid rgba(212, 165, 116, 0.3);
            border-radius: 10px;
            font-weight: 500;
            padding: 0.6rem 1rem;
            backdrop-filter: blur(4px);
            transition: all 0.3s ease;
        }}
        
        section[data-testid="stSidebar"] .stButton > button:hover {{
            background: linear-gradient(
                135deg, 
                rgba(229, 27, 35, 0.98), 
                rgba(17, 17, 17, 0.98)
            );
            border-color: rgba(212, 165, 116, 0.5);
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
        }}
        
        section[data-testid="stSidebar"] [data-baseweb="radio"] label {{
            border-radius: 8px;
            padding: 0.4rem 0.6rem;
            transition: all 0.2s ease;
        }}
        
        section[data-testid="stSidebar"] [data-baseweb="radio"] label:hover {{
            background: rgba(212, 165, 116, 0.15);
        }}
        
        /* ===== TÍTULOS - ELEGANTES ===== */
        h1 {{
            color: var(--texto-escuro) !important;
            font-weight: 700 !important;
            font-size: 2rem !important;
            border-bottom: 3px solid var(--dourado);
            padding-bottom: 0.75rem;
            margin-bottom: 0.5rem !important;
            letter-spacing: -0.02em;
        }}
        
        h2 {{
            color: var(--texto-escuro) !important;
            font-weight: 600 !important;
            font-size: 1.5rem !important;
            margin-top: 1.5rem !important;
            margin-bottom: 0.75rem !important;
        }}
        
        h3, h4 {{
            color: var(--texto-escuro) !important;
            font-weight: 600 !important;
        }}
        
        /* ===== CAPTIONS E SUBTÍTULOS ===== */
        .stCaption, [data-testid="stCaptionContainer"] {{
            color: var(--texto-secundario) !important;
            font-size: 0.95rem !important;
            line-height: 1.6;
        }}
        
        /* ===== MÉTRICAS - MODERNAS ===== */
        div[data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.96);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 14px;
            padding: 1.5rem 1.25rem;
            border-left: 5px solid var(--dourado);
            border: 1px solid rgba(212, 165, 116, 0.2);
            box-shadow: var(--sombra-media);
            transition: all 0.3s ease;
        }}
        
        div[data-testid="stMetric"]:hover {{
            transform: translateY(-6px);
            box-shadow: var(--sombra-forte);
            border-color: rgba(212, 165, 116, 0.4);
        }}
        
        div[data-testid="stMetric"] label {{
            font-weight: 600 !important;
            color: var(--texto-secundario) !important;
            font-size: 0.9rem !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
            color: var(--azul-profundo) !important;
            font-weight: 700 !important;
            font-size: 2rem !important;
        }}
        
        /* ===== BOTÕES ===== */
        .stButton > button {{
            background: linear-gradient(
                135deg, 
                var(--azul-principal), 
                var(--azul-profundo)
            );
            color: white !important;
            border: none;
            border-radius: 10px;
            padding: 0.7rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: var(--sombra-media);
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: var(--sombra-forte);
            background: linear-gradient(
                135deg, 
                var(--azul-claro), 
                var(--azul-principal)
            );
        }}
        
        /* ===== FORMULÁRIOS ===== */
        div[data-testid="stForm"] {{
            background: rgba(255, 255, 255, 0.96);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 14px;
            padding: 2rem;
            border: 1px solid rgba(212, 165, 116, 0.2);
            box-shadow: var(--sombra-media);
        }}
        
        /* ===== CAMPOS DE INSERÇÃO ===== */
        [data-testid="stWidgetLabel"] p,
        .stTextInput label,
        .stTextArea label,
        .stSelectbox label,
        .stDateInput label,
        .stFileUploader label {{
            color: var(--texto-escuro) !important;
            font-size: 0.88rem !important;
            font-weight: 650 !important;
            letter-spacing: 0.01em;
            margin-bottom: 0.38rem !important;
        }}

        .stTextInput div[data-baseweb="input"] > div,
        .stNumberInput div[data-baseweb="input"] > div,
        .stDateInput div[data-baseweb="input"] > div,
        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div {{
            min-height: 46px !important;
            border-radius: 10px !important;
            border: 1px solid #CBD5E1 !important;
            background: #FFFFFF !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
            transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease !important;
        }}

        .stTextArea textarea {{
            min-height: 118px !important;
            padding: 0.78rem 0.9rem !important;
            border-radius: 10px !important;
            border: 1px solid #CBD5E1 !important;
            background: #FFFFFF !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
            resize: vertical !important;
            transition: border-color 160ms ease, box-shadow 160ms ease !important;
        }}

        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        .stSelectbox input,
        .stMultiSelect input,
        .stTextArea textarea {{
            color: var(--texto-escuro) !important;
            font-size: 0.96rem !important;
            line-height: 1.45 !important;
        }}

        .stTextInput input::placeholder,
        .stNumberInput input::placeholder,
        .stDateInput input::placeholder,
        .stTextArea textarea::placeholder {{
            color: #718096 !important;
            opacity: 1 !important;
        }}

        .stTextInput div[data-baseweb="input"] > div:hover,
        .stNumberInput div[data-baseweb="input"] > div:hover,
        .stDateInput div[data-baseweb="input"] > div:hover,
        .stSelectbox div[data-baseweb="select"] > div:hover,
        .stMultiSelect div[data-baseweb="select"] > div:hover,
        .stTextArea textarea:hover {{
            border-color: #9CB7CC !important;
        }}

        .stTextInput div[data-baseweb="input"] > div:focus-within,
        .stNumberInput div[data-baseweb="input"] > div:focus-within,
        .stDateInput div[data-baseweb="input"] > div:focus-within,
        .stSelectbox div[data-baseweb="select"] > div:focus-within,
        .stMultiSelect div[data-baseweb="select"] > div:focus-within,
        .stTextArea textarea:focus {{
            border-color: var(--azul-principal) !important;
            box-shadow: 0 0 0 4px rgba(200, 16, 46, 0.14), 0 2px 5px rgba(15, 23, 42, 0.08) !important;
            outline: none !important;
        }}

        .stSelectbox svg,
        .stMultiSelect svg,
        .stDateInput svg,
        .stNumberInput svg {{
            color: var(--azul-principal) !important;
            fill: currentColor !important;
        }}

        .stMultiSelect span[data-baseweb="tag"] {{
            background: #FFF2D1 !important;
            color: #5C4300 !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
        }}

        [data-testid="stFileUploaderDropzone"] {{
            min-height: 142px !important;
            padding: 1.15rem !important;
            background: linear-gradient(135deg, #FFFBF3 0%, #FFF4D6 100%) !important;
            border: 1.5px dashed #D6A900 !important;
            border-radius: 12px !important;
            transition: border-color 160ms ease, box-shadow 160ms ease !important;
        }}

        [data-testid="stFileUploaderDropzone"]:hover {{
            border-color: var(--azul-principal) !important;
            box-shadow: 0 0 0 4px rgba(200, 16, 46, 0.10) !important;
        }}
        
        /* ===== ALERTS ===== */
        div[data-testid="stAlert"] {{
            border-radius: 12px;
            border-left: 4px solid var(--azul-principal);
            padding: 1rem;
            background: rgba(255, 255, 255, 0.94);
            box-shadow: var(--sombra-leve);
        }}
        
        /* ===== DATAFRAMES ===== */
        .stDataFrame {{
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(212, 165, 116, 0.15);
            box-shadow: var(--sombra-leve);
        }}
        
        /* ===== LOGIN BOX - ELEGANTE E COMPACTO ===== */
        .login-wrapper {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 92vh;
            padding: 1rem;
            position: relative;
            z-index: 10;
        }}
        
        .login-box {{
            max-width: 380px;
            width: 100%;
            padding: 2.2rem 2rem;
            background: rgba(17, 17, 17, 0.90);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-radius: 18px;
            box-shadow: 0 24px 64px rgba(0, 0, 0, 0.35), 
                        inset 0 1px 0 rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(212, 165, 116, 0.3);
            transition: all 0.3s ease;
        }}
        
        .login-box:hover {{
            box-shadow: 0 32px 80px rgba(0, 0, 0, 0.45), 
                        inset 0 1px 0 rgba(255, 255, 255, 0.08);
            border-color: rgba(212, 165, 116, 0.5);
        }}
        
        .login-box h1 {{
            text-align: center;
            color: #FFFFFF !important;
            border-bottom: none !important;
            margin-bottom: 0.25rem !important;
            font-size: 1.4rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.3px;
            text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }}
        
        .login-box .subtitle {{
            text-align: center;
            color: rgba(212, 165, 116, 0.8);
            margin-bottom: 1.8rem;
            font-size: 0.8rem;
            letter-spacing: 1.2px;
            font-weight: 400;
            text-transform: uppercase;
        }}
        
        /* Campos do formulário de login */
        .login-box .stTextInput {{
            margin-bottom: 0.8rem;
        }}
        
        .login-box .stTextInput > div > div > input {{
            background-color: rgba(255, 255, 255, 0.93) !important;
            border-radius: 10px !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            color: var(--texto-escuro) !important;
            padding: 0.5rem 1rem !important;
            font-size: 0.95rem !important;
            height: 40px !important;
            transition: all 0.3s ease !important;
        }}
        
        .login-box .stTextInput > div > div > input:focus {{
            border-color: rgba(212, 165, 116, 0.6) !important;
            box-shadow: 0 0 0 3px rgba(212, 165, 116, 0.15) !important;
            background-color: rgba(255, 255, 255, 0.98) !important;
        }}
        
        .login-box .stTextInput > div > div > input::placeholder {{
            color: #9CA3AF !important;
            font-size: 0.9rem !important;
        }}
        
        .login-box .stTextInput label {{
            display: none !important;
        }}
        
        /* Botão de login */
        .login-box .stButton > button {{
            background: linear-gradient(
                135deg, 
                var(--azul-principal), 
                var(--azul-profundo)
            ) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            padding: 0.6rem 1rem !important;
            width: 100% !important;
            font-size: 0.95rem !important;
            letter-spacing: 0.3px;
            transition: all 0.3s ease !important;
            box-shadow: 0 6px 20px rgba(27, 94, 145, 0.25) !important;
            height: 40px !important;
            margin-top: 0.5rem !important;
        }}
        
        .login-box .stButton > button:hover {{
            background: linear-gradient(
                135deg, 
                var(--azul-claro), 
                var(--azul-principal)
            ) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 28px rgba(27, 94, 145, 0.35) !important;
        }}
        
        /* ===== CONTEÚDO DAS PÁGINAS ===== */
        .page-content {{
            background: rgba(255, 255, 255, 0.94);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border-radius: 16px;
            padding: 2rem;
            box-shadow: var(--sombra-media);
            border: 1px solid rgba(212, 165, 116, 0.2);
            margin-top: 1rem;
        }}
        
        /* ===== EXPANDER ===== */
        .streamlit-expanderHeader {{
            background: rgba(248, 250, 252, 0.92);
            border-radius: 10px;
            font-weight: 600;
            border: 1px solid rgba(212, 165, 116, 0.2);
            transition: all 0.2s ease;
        }}
        
        .streamlit-expanderHeader:hover {{
            background: rgba(248, 250, 252, 0.98);
            border-color: rgba(212, 165, 116, 0.3);
        }}
        
        /* ===== TABS ===== */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.5rem;
            border-bottom: 2px solid rgba(212, 165, 116, 0.2);
        }}
        
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px;
            padding: 0.6rem 1.5rem;
            font-weight: 600;
            background: transparent;
            border: none;
            color: var(--texto-secundario) !important;
            transition: all 0.2s ease;
        }}
        
        .stTabs [aria-selected="true"] {{
            color: var(--azul-principal) !important;
            border-bottom: 3px solid var(--dourado);
            background: rgba(212, 165, 116, 0.08);
        }}
        
        /* ===== CARDS INFORMATIVOS ===== */
        .info-card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(4px);
            border-radius: 14px;
            padding: 1.75rem;
            border: 1px solid rgba(212, 165, 116, 0.2);
            height: 100%;
            transition: all 0.3s ease;
            box-shadow: var(--sombra-leve);
        }}
        
        .info-card:hover {{
            box-shadow: var(--sombra-media);
            transform: translateY(-4px);
            border-color: rgba(212, 165, 116, 0.4);
        }}
        
        .info-card h4 {{
            color: var(--azul-principal);
            margin-top: 0;
            margin-bottom: 0.75rem;
            font-weight: 700;
        }}
        
        .info-card p {{
            color: var(--texto-secundario);
            line-height: 1.7;
            margin: 0;
            font-size: 0.95rem;
        }}
        
        /* ===== SIDEBAR USER INFO ===== */
        .sidebar-user {{
            background: rgba(255, 255, 255, 0.08);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(212, 165, 116, 0.2);
        }}
        
        .sidebar-user .user-name {{
            color: #FFFFFF;
            font-weight: 700;
            font-size: 0.95rem;
        }}
        
        .sidebar-user .user-role {{
            color: rgba(212, 165, 116, 0.85);
            font-size: 0.8rem;
            margin-top: 0.25rem;
        }}
        
        .sidebar-user .user-label {{
            color: rgba(212, 165, 116, 0.6);
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            margin-bottom: 0.3rem;
        }}
        
        /* ===== FOOTER ===== */
        .footer {{
            text-align: center;
            padding: 2rem 0 1rem;
            color: var(--texto-secundario);
            font-size: 0.85rem;
            border-top: 1px solid rgba(212, 165, 116, 0.15);
            margin-top: 3rem;
            background: transparent;
        }}
        
        /* ===== SCROLLBAR ===== */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: rgba(212, 165, 116, 0.08);
            border-radius: 10px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: rgba(27, 94, 145, 0.4);
            border-radius: 10px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(27, 94, 145, 0.6);
        }}
        </style>
    """, unsafe_allow_html=True)
    
    # Injetar o elemento de vídeo HTML e overlay
    video_path = Path(BACKGROUND_VIDEO)
    video_exists = video_path.exists()
    if video_exists and video_base64:
        st.markdown(f"""
            <div class="video-overlay"></div>
            <video class="video-background" autoplay muted loop playsinline>
                <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
                O seu navegador não suporta vídeos HTML5.
            </video>
        """, unsafe_allow_html=True)

inject_custom_css()

# ============================================================
# GERENCIADOR DE BASE DE DADOS
# ============================================================

class DatabaseManager:
    """Gerenciador profissional de base de dados com suporte a migrações"""
    
    SCHEMA_VERSION = 3
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ensure_db_directory()
    
    def _ensure_db_directory(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro na conexão com a base de dados: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_single(self, query: str, params: tuple = ()) -> Optional[Dict]:
        results = self.execute_query(query, params)
        return results[0] if results else None
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    def table_exists(self, table_name: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            return cursor.fetchone() is not None

    def execute_update(self, query: str, params: tuple = ()) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            row_count = cursor.rowcount
            return int(row_count) if row_count is not None else 0
    
    def column_exists(self, table_name: str, column_name: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            return column_name in columns
    
    def add_column_if_not_exists(self, table_name: str, column_name: str, column_type: str):
        if not self.column_exists(table_name, column_name):
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                conn.commit()
                logger.info(f"Coluna {column_name} adicionada à tabela {table_name}")

# ============================================================
# INICIALIZACAO DA BASE DE DADOS
# ============================================================

db = DatabaseManager(DB_PATH)

def init_database():
    try:
        logger.info("Iniciando inicialização da base de dados...")
        
        schema_version = 0
        if db.table_exists('schema_version'):
            result = db.execute_single("SELECT version FROM schema_version")
            schema_version = result['version'] if result else 0
        
        _create_tables()
        _migrate_columns()
        
        if schema_version < db.SCHEMA_VERSION:
            logger.info(f"Atualizando schema da versão {schema_version} para {db.SCHEMA_VERSION}")
            _create_initial_data()
            _update_schema_version()
            logger.info("Base de dados inicializada com sucesso!")
        else:
            _create_initial_data()
            logger.info("Base de dados já está na versão mais recente")
        
    except Exception as e:
        logger.error(f"Erro fatal na inicialização da base de dados: {e}")
        raise


def _migrate_columns():
    db.add_column_if_not_exists("users", "full_name", "TEXT")
    db.add_column_if_not_exists("users", "email", "TEXT")
    db.add_column_if_not_exists("users", "department", "TEXT")
    db.add_column_if_not_exists("users", "created_at", "TEXT")
    db.add_column_if_not_exists("users", "active", "INTEGER DEFAULT 1")
    
    db.add_column_if_not_exists("documents", "document_number", "TEXT")
    db.add_column_if_not_exists("documents", "type", "TEXT")
    db.add_column_if_not_exists("documents", "department", "TEXT")
    db.add_column_if_not_exists("documents", "municipality", "TEXT")
    db.add_column_if_not_exists("documents", "category", "TEXT")
    db.add_column_if_not_exists("documents", "subcategory", "TEXT")
    db.add_column_if_not_exists("documents", "status", "TEXT DEFAULT 'Digitalizado'")
    db.add_column_if_not_exists("documents", "file_path", "TEXT")
    db.add_column_if_not_exists("documents", "file_name", "TEXT")
    db.add_column_if_not_exists("documents", "file_size", "INTEGER")
    db.add_column_if_not_exists("documents", "file_type", "TEXT")
    db.add_column_if_not_exists("documents", "created_at", "TEXT")
    db.add_column_if_not_exists("documents", "created_by", "TEXT")
    db.add_column_if_not_exists("documents", "updated_at", "TEXT")
    db.add_column_if_not_exists("documents", "updated_by", "TEXT")
    db.add_column_if_not_exists("documents", "description", "TEXT")
    db.add_column_if_not_exists("documents", "keywords", "TEXT")
    db.add_column_if_not_exists("documents", "security_level", "TEXT DEFAULT 'Publico'")
    db.add_column_if_not_exists("documents", "archive_period", "TEXT")
    
    db.add_column_if_not_exists("processes", "priority", "TEXT DEFAULT 'Normal'")
    db.add_column_if_not_exists("processes", "created_at", "TEXT")
    db.add_column_if_not_exists("processes", "updated_at", "TEXT")
    db.add_column_if_not_exists("processes", "created_by", "TEXT")
    db.add_column_if_not_exists("processes", "assigned_to", "TEXT")
    db.add_column_if_not_exists("processes", "deadline", "TEXT")
    db.add_column_if_not_exists("processes", "observations", "TEXT")
    db.add_column_if_not_exists("processes", "related_documents", "TEXT")
    
    db.add_column_if_not_exists("transactions", "observations", "TEXT")
    db.add_column_if_not_exists("transactions", "created_at", "TEXT")
    db.add_column_if_not_exists("transactions", "created_by", "TEXT")
    db.add_column_if_not_exists("transactions", "status", "TEXT DEFAULT 'Pendente'")
    
    db.add_column_if_not_exists("audit_log", "details", "TEXT")
    
    db.add_column_if_not_exists("municipalities", "province", "TEXT")
    db.add_column_if_not_exists("municipalities", "created_at", "TEXT")
    db.add_column_if_not_exists("departments", "description", "TEXT")
    db.add_column_if_not_exists("departments", "created_at", "TEXT")
    
    logger.info("Migração de colunas concluída")


def _create_tables():
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'Tecnico',
                full_name TEXT,
                email TEXT,
                department TEXT,
                created_at TEXT NOT NULL,
                active INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                document_number TEXT UNIQUE,
                type TEXT,
                department TEXT,
                municipality TEXT,
                category TEXT,
                subcategory TEXT,
                status TEXT DEFAULT 'Digitalizado',
                file_path TEXT,
                file_name TEXT,
                file_size INTEGER,
                file_type TEXT,
                created_at TEXT NOT NULL,
                created_by TEXT NOT NULL,
                updated_at TEXT,
                updated_by TEXT,
                description TEXT,
                keywords TEXT,
                security_level TEXT DEFAULT 'Publico',
                archive_period TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_number TEXT UNIQUE NOT NULL,
                subject TEXT NOT NULL,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Em tramitacao',
                priority TEXT DEFAULT 'Normal',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                created_by TEXT NOT NULL,
                assigned_to TEXT,
                deadline TEXT,
                observations TEXT,
                related_documents TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_id INTEGER NOT NULL,
                from_department TEXT NOT NULL,
                to_department TEXT NOT NULL,
                action TEXT NOT NULL,
                observations TEXT,
                created_at TEXT NOT NULL,
                created_by TEXT NOT NULL,
                status TEXT DEFAULT 'Pendente'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL,
                details TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS municipalities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                code TEXT NOT NULL,
                province TEXT,
                created_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                code TEXT NOT NULL,
                description TEXT,
                created_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        logger.info("Tabelas criadas com sucesso")

def _create_initial_data():
    now = datetime.now().isoformat()
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        admin_hash = hash_password("admin123")
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password_hash, role, full_name, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", admin_hash, "Administrador", "Administrador do Sistema", now))
        
        municipios = [
            ("Luanda", "LU", "Luanda"),
            ("Benguela", "BE", "Benguela"),
            ("Huila", "HU", "Huila"),
            ("Cabinda", "CA", "Cabinda"),
            ("Namibe", "NA", "Namibe")
        ]
        for name, code, province in municipios:
            cursor.execute("""
                INSERT OR IGNORE INTO municipalities (name, code, province, created_at)
                VALUES (?, ?, ?, ?)
            """, (name, code, province, now))
        
        deptos = [
            ("Gabinete do Governador", "GAB", "Gabinete do Governador"),
            ("Secretaria Geral", "SG", "Secretaria Geral"),
            ("Financas", "FIN", "Departamento de Financas"),
            ("Planeamento", "PLAN", "Departamento de Planeamento"),
            ("Infraestruturas", "INF", "Departamento de Infraestruturas"),
            ("Educacao", "EDU", "Departamento de Educacao"),
            ("Saude", "SAU", "Departamento de Saude")
        ]
        for name, code, desc in deptos:
            cursor.execute("""
                INSERT OR IGNORE INTO departments (name, code, description, created_at)
                VALUES (?, ?, ?, ?)
            """, (name, code, desc, now))
        
        conn.commit()
        logger.info("Dados iniciais criados com sucesso")

def _update_schema_version():
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM schema_version")
        cursor.execute("""
            INSERT INTO schema_version (version, updated_at)
            VALUES (?, ?)
        """, (db.SCHEMA_VERSION, datetime.now().isoformat()))
        conn.commit()

# ============================================================
# FUNCOES DE SEGURANCA
# ============================================================

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def authenticate(username: str, password: str) -> Optional[Dict]:
    username = username.strip()
    if not username or not password:
        return None
    
    password_hash = hash_password(password)
    try:
        user = db.execute_single("""
            SELECT id, username, role, full_name, email, department
            FROM users
            WHERE username = ? AND password_hash = ? AND active = 1
        """, (username, password_hash))
        return user
    except Exception as e:
        logger.error(f"Erro na autenticação: {e}")
        return None

def log_action(username: str, action: str, module: Optional[str] = None, record_id: Optional[str] = None, details: Optional[str] = None):
    try:
        if module or record_id:
            details_text = f"Modulo: {module} | ID: {record_id} | {details or ''}".strip(" |")
        else:
            details_text = details or action
        db.execute_insert("""
            INSERT INTO audit_log (username, action, created_at, details)
            VALUES (?, ?, ?, ?)
        """, (username, action, datetime.now().isoformat(), details_text))
    except Exception as e:
        logger.error(f"Erro ao registrar ação de auditoria: {e}")

def check_permission(required_role: str) -> bool:
    if st.session_state.role == "Administrador":
        return True
    roles_hierarchy = {"Administrador": 3, "Gestor": 2, "Tecnico": 1}
    return roles_hierarchy.get(st.session_state.role, 0) >= roles_hierarchy.get(required_role, 0)

# ============================================================
# FUNCOES DE GESTAO DOCUMENTAL
# ============================================================

def generate_document_number() -> str:
    try:
        count = db.execute_single("SELECT COUNT(*) as count FROM documents")
        count = count['count'] if count else 0
        year = datetime.now().year
        return f"DOC-{year}-{count + 1:06d}"
    except Exception as e:
        logger.error(f"Erro ao gerar número de documento: {e}")
        return f"DOC-{datetime.now().year}-{datetime.now().strftime('%H%M%S')}"

def generate_process_number() -> str:
    try:
        count = db.execute_single("SELECT COUNT(*) as count FROM processes")
        count = count['count'] if count else 0
        year = datetime.now().year
        return f"PROC-{year}-{count + 1:06d}"
    except Exception as e:
        logger.error(f"Erro ao gerar número de processo: {e}")
        return f"PROC-{datetime.now().year}-{datetime.now().strftime('%H%M%S')}"

def get_document_stats() -> Tuple[int, List, List, List]:
    try:
        total = db.execute_single("SELECT COUNT(*) as count FROM documents")
        total = total['count'] if total else 0
        
        by_category = db.execute_query("""
            SELECT category, COUNT(*) as count 
            FROM documents 
            WHERE category IS NOT NULL 
            GROUP BY category
            ORDER BY count DESC
        """)
        
        by_status = db.execute_query("""
            SELECT status, COUNT(*) as count 
            FROM documents 
            GROUP BY status
            ORDER BY count DESC
        """)
        
        by_department = db.execute_query("""
            SELECT department, COUNT(*) as count 
            FROM documents 
            WHERE department IS NOT NULL
            GROUP BY department
            ORDER BY count DESC
            LIMIT 10
        """)
        
        return total, by_category, by_status, by_department
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de documentos: {e}")
        return 0, [], [], []

def get_process_stats() -> Tuple[int, int, List, List]:
    try:
        total = db.execute_single("SELECT COUNT(*) as count FROM processes")
        total = total['count'] if total else 0
        
        pending = db.execute_single("""
            SELECT COUNT(*) as count 
            FROM processes 
            WHERE status != 'Concluido'
        """)
        pending = pending['count'] if pending else 0
        
        by_status = db.execute_query("""
            SELECT status, COUNT(*) as count 
            FROM processes 
            GROUP BY status
            ORDER BY count DESC
        """)
        
        try:
            by_priority = db.execute_query("""
                SELECT priority, COUNT(*) as count 
                FROM processes 
                GROUP BY priority
                ORDER BY count DESC
            """)
        except:
            by_priority = []
        
        return total, pending, by_status, by_priority
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de processos: {e}")
        return 0, 0, [], []

# ============================================================
# INICIALIZACAO DA SESSAO
# ============================================================

def init_session():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "role" not in st.session_state:
        st.session_state.role = ""
    if "full_name" not in st.session_state:
        st.session_state.full_name = ""


def rerun_app():
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

# ============================================================
# TELA DE LOGIN
# ============================================================

def login_screen():
    _, login_column, _ = st.columns([1, 1.2, 1])

    with login_column:
        with st.container(key="login-panel", border=False):
            if LOGO_PATH.exists():
                with st.container(horizontal_alignment="center"):
                    st.image(str(LOGO_PATH), width=132)
            st.title("Governo Provincial", text_alignment="center")
            st.caption(
                "Sistema de Gestão Documental",
                text_alignment="center"
            )

            with st.form("login_form", clear_on_submit=False):
                username = st.text_input(
                    "Utilizador",
                    placeholder="Digite o seu nome de utilizador",
                    label_visibility="collapsed"
                )

                password = st.text_input(
                    "Palavra-passe",
                    type="password",
                    placeholder="Digite a sua palavra-passe",
                    label_visibility="collapsed"
                )

                submitted = st.form_submit_button("Iniciar sessão", type="primary", width="stretch")

                if submitted:
                    if not username.strip():
                        st.error("⚠️ Digite o utilizador.")
                    elif not password:
                        st.error("⚠️ Digite a palavra-passe.")
                    else:
                        user = authenticate(username, password)
                        if user:
                            st.session_state.authenticated = True
                            st.session_state.username = user["username"]
                            st.session_state.role = user["role"]
                            st.session_state.full_name = user["full_name"] or user["username"]
                            log_action(user["username"], "Login", "Sistema")
                            rerun_app()
                        else:
                            st.error("❌ Utilizador ou palavra-passe inválidos.")

            st.caption("Demo: admin / admin123", text_alignment="center")

# ============================================================
# DASHBOARD
# ============================================================

def page_dashboard():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    st.title("Painel de Controlo")
    st.caption("Visão geral do sistema de gestão documental do Governo Provincial")
    
    doc_total, doc_cat, doc_status, doc_dept = get_document_stats()
    proc_total, proc_pending, proc_status, _ = get_process_stats()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Documentos", f"{doc_total:,}")
    with col2:
        st.metric("Processos Pendentes", f"{proc_pending:,}")
    with col3:
        st.metric("Departamentos", f"{len(doc_dept)}")
    with col4:
        st.metric("Total de Processos", f"{proc_total:,}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Documentos por Categoria")
        if doc_cat:
            df_cat = pd.DataFrame(doc_cat)
            st.dataframe(df_cat, hide_index=True, width="stretch")
        else:
            st.info("Nenhum documento categorizado.")
    
    with col2:
        st.subheader("Processos por Status")
        if proc_status:
            df_status = pd.DataFrame(proc_status)
            st.dataframe(df_status, hide_index=True, width="stretch")
        else:
            st.info("Nenhum processo registado.")
    
    st.markdown("---")
    
    st.subheader("Objectivos Estratégicos")
    
    objetivos = [
        ("📂 Digitalização", "Digitalizar e organizar o acervo documental do Governo Provincial, eliminando a dependência do arquivo físico."),
        ("⚡ Tramitação", "Permitir tramitação electrónica de processos entre secretarias com agilidade e transparência."),
        ("🔒 Segurança", "Garantir autenticidade, rastreabilidade e segurança através de registos de auditoria."),
        ("📚 Capacitação", "Capacitar quadros técnicos na gestão documental digital moderna."),
        ("🛡️ Proteção", "Reduzir risco de perda de informação através de backups digitais."),
        ("⚖️ Conformidade", "Assegurar conformidade com normas legais de gestão documental.")
    ]
    
    cols = st.columns(3)
    for idx, (titulo, desc) in enumerate(objetivos):
        with cols[idx % 3]:
            st.markdown(f"""
                <div class="info-card">
                    <h4>{titulo}</h4>
                    <p>{desc}</p>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGINA: DIGITALIZAR
# ============================================================

def page_digitalizar():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    st.title("Digitalizar Documentos")
    st.caption("Digitalize, indexe e organize o acervo documental")
    
    tabs = st.tabs(["Digitalizar", "Documentos Recentes"])
    
    with tabs[0]:
        with st.form("document_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Título do Documento *", placeholder="Digite o título completo")
                doc_type = st.selectbox("Tipo", ["Ofício", "Despacho", "Processo", "Relatório", "Contrato", "Certidão", "Edital", "Outro"])
                department = st.selectbox("Departamento *", 
                                        ["Gabinete do Governador", "Secretaria Geral", "Financas", "Planeamento", "Infraestruturas", "Educacao", "Saude"])
                municipality = st.selectbox("Município", ["Luanda", "Benguela", "Huila", "Cabinda", "Namibe", "Outro"])
            
            with col2:
                category = st.selectbox("Categoria", ["Administrativo", "Financeiro", "Juridico", "Tecnico", "Operacional", "Estrategico"])
                subcategory = st.text_input("Subcategoria", placeholder="Ex: Recursos Humanos")
                security_level = st.selectbox("Nível de Segurança", ["Publico", "Restrito", "Confidencial", "Secreto"])
                archive_period = st.selectbox("Período", ["1 ano", "3 anos", "5 anos", "10 anos", "Permanente"])
            
            col3, col4 = st.columns(2)
            with col3:
                uploaded = st.file_uploader("Ficheiro", type=["pdf", "png", "jpg", "jpeg", "docx", "xlsx", "zip"])
                description = st.text_area("Descrição", placeholder="Descrição do conteúdo...")
            
            with col4:
                keywords = st.text_input("Palavras-chave", placeholder="Separadas por vírgulas")
                document_number = st.text_input("Nº Documento", placeholder="Deixe em branco para gerar automaticamente")
            
            submitted = st.form_submit_button("Digitalizar", type="primary", width="stretch")
            
            if submitted:
                title = title.strip()
                if not title:
                    st.error("O título é obrigatório.")
                    return
                
                if not department:
                    st.error("Selecione o departamento.")
                    return
                
                final_number = document_number.strip() if document_number.strip() else generate_document_number()
                
                file_path = ""
                file_name = ""
                file_size = 0
                file_type = ""
                
                if uploaded:
                    try:
                        original_name = Path(uploaded.name).name
                        safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in original_name)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{timestamp}_{final_number}_{safe_name}"
                        destination = UPLOAD_DIR / filename
                        with open(destination, "wb") as f:
                            f.write(uploaded.getbuffer())
                        file_path = str(destination)
                        file_name = original_name
                        file_size = len(uploaded.getvalue())
                        file_type = Path(original_name).suffix[1:] if Path(original_name).suffix else "unknown"
                    except Exception as e:
                        st.error(f"Erro ao guardar ficheiro: {str(e)}")
                        logger.error(f"Erro ao guardar ficheiro: {e}")
                        return
                
                existing = db.execute_single("SELECT id FROM documents WHERE document_number = ?", (final_number,))
                if existing:
                    st.error(f"O número '{final_number}' já está em uso.")
                    return
                
                now = datetime.now().isoformat()
                try:
                    db.execute_insert("""
                        INSERT INTO documents (
                            title, document_number, type, department, municipality, category, subcategory,
                            status, file_path, file_name, file_size, file_type, created_at, created_by,
                            description, keywords, security_level, archive_period
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        title, final_number, doc_type, department, municipality, category, subcategory,
                        "Digitalizado", file_path, file_name, file_size, file_type, now, st.session_state.username,
                        description, keywords, security_level, archive_period
                    ))
                    
                    log_action(st.session_state.username, "Documento Digitalizado", "Documentos", final_number, 
                              f"Título: {title} | Tipo: {doc_type}")
                    st.success(f"✅ Documento '{title}' digitalizado com sucesso!")
                    
                except Exception as e:
                    st.error(f"Erro ao guardar documento: {str(e)}")
                    logger.error(f"Erro ao guardar documento: {e}")
                    return
    
    with tabs[1]:
        st.subheader("Documentos Recentes")
        try:
            rows = db.execute_query("""
                SELECT id, title, document_number, type, department, municipality, category, status, created_at
                FROM documents
                ORDER BY id DESC
                LIMIT 20
            """)
            
            if rows:
                df = pd.DataFrame(rows)
                st.dataframe(df, hide_index=True, width="stretch")
            else:
                st.info("Nenhum documento digitalizado ainda.")
        except Exception as e:
            st.error(f"Erro ao carregar documentos: {str(e)}")
            logger.error(f"Erro ao carregar documentos: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGINA: INDEXAR
# ============================================================

def page_indexar():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    st.title("Indexar e Organizar")
    st.caption("Pesquise e classifique o acervo documental")
    
    with st.expander("🔍 Filtros de Pesquisa", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            query = st.text_input("Pesquisa", placeholder="Título, número...")
            department = st.selectbox("Departamento", ["Todos"] + ["Gabinete do Governador", "Secretaria Geral", "Financas", "Planeamento", "Infraestruturas", "Educacao", "Saude"])
        
        with col2:
            category = st.selectbox("Categoria", ["Todas", "Administrativo", "Financeiro", "Juridico", "Tecnico", "Operacional", "Estrategico"])
            municipality = st.selectbox("Município", ["Todos", "Luanda", "Benguela", "Huila", "Cabinda", "Namibe", "Outro"])
        
        with col3:
            status_filter = st.selectbox("Status", ["Todos", "Digitalizado", "Em Analise", "Aprovado", "Arquivado", "Eliminado"])
            security_level = st.selectbox("Segurança", ["Todos", "Publico", "Restrito", "Confidencial", "Secreto"])
    
    try:
        sql = """
            SELECT id, title, document_number, type, department, municipality, category, status, security_level, created_at
            FROM documents
            WHERE 1=1
        """
        params = []
        
        if query:
            q = f"%{query}%"
            sql += " AND (title LIKE ? OR document_number LIKE ? OR description LIKE ?)"
            params.extend([q, q, q])
        
        if department != "Todos":
            sql += " AND department = ?"
            params.append(department)
        
        if category != "Todas":
            sql += " AND category = ?"
            params.append(category)
        
        if municipality != "Todos":
            sql += " AND municipality = ?"
            params.append(municipality)
        
        if status_filter != "Todos":
            sql += " AND status = ?"
            params.append(status_filter)
        
        if security_level != "Todos":
            sql += " AND security_level = ?"
            params.append(security_level)
        
        sql += " ORDER BY id DESC"
        
        rows = db.execute_query(sql, tuple(params))
        
    except Exception as e:
        st.error(f"Erro ao pesquisar: {str(e)}")
        logger.error(f"Erro ao pesquisar: {e}")
        rows = []
    
    st.write(f"**{len(rows)}** resultado(s) encontrado(s).")
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, hide_index=True, width="stretch")
    else:
        st.warning("Nenhum documento encontrado.")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGINA: TRAMITACAO
# ============================================================

def page_tramitacao():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    st.title("Tramitação Electrónica")
    st.caption("Encaminhe processos entre secretarias com rastreabilidade total")
    
    tabs = st.tabs(["Novo Processo", "Em Andamento", "Histórico"])
    
    with tabs[0]:
        with st.form("process_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                subject = st.text_input("Assunto *", placeholder="Descreva o assunto")
                origin = st.selectbox("Origem *", 
                                     ["Gabinete do Governador", "Secretaria Geral", "Financas", "Planeamento", "Infraestruturas", "Educacao", "Saude"])
                priority = st.selectbox("Prioridade", ["Normal", "Urgente", "Muito Urgente"])
                deadline = st.date_input("Prazo", value=None)
            
            with col2:
                destination = st.selectbox("Destino *", 
                                         ["Luanda", "Benguela", "Huila", "Cabinda", "Namibe", "Outro"])
                observations = st.text_area("Observações")
                related_docs = st.text_input("Documentos Relacionados")
            
            submitted = st.form_submit_button("Registar Processo", type="primary", width="stretch")
            
            if submitted:
                subject = subject.strip()
                if not subject:
                    st.error("O assunto é obrigatório.")
                    return
                if not origin:
                    st.error("Selecione a origem.")
                    return
                if not destination:
                    st.error("Selecione o destino.")
                    return
                
                process_number = generate_process_number()
                now = datetime.now().isoformat()
                deadline_str = deadline.isoformat() if deadline else None
                
                try:
                    db.execute_insert("""
                        INSERT INTO processes (
                            process_number, subject, origin, destination, status, priority,
                            created_at, updated_at, created_by, deadline, observations, related_documents
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        process_number, subject, origin, destination, "Em tramitacao", priority,
                        now, now, st.session_state.username, deadline_str, observations, related_docs
                    ))
                    
                    log_action(st.session_state.username, "Processo Criado", "Processos", process_number)
                    st.success(f"✅ Processo '{process_number}' registado com sucesso!")
                    
                except Exception as e:
                    st.error(f"Erro ao registar: {str(e)}")
                    logger.error(f"Erro ao registar processo: {e}")
    
    with tabs[1]:
        st.subheader("Processos em Tramitação")
        
        try:
            rows = db.execute_query("""
                SELECT id, process_number, subject, origin, destination, status, priority, created_at
                FROM processes
                WHERE status != 'Concluido'
                ORDER BY created_at DESC
                LIMIT 50
            """)
        except:
            rows = db.execute_query("""
                SELECT id, process_number, subject, origin, destination, status, created_at
                FROM processes
                WHERE status != 'Concluido'
                ORDER BY created_at DESC
                LIMIT 50
            """)
        
        if rows:
            for row in rows:
                priority_icon = "🔴" if row.get('priority') == 'Muito Urgente' else "🟡" if row.get('priority') == 'Urgente' else "🟢"
                with st.expander(f"{priority_icon} {row['process_number']} - {row['subject']}"):
                    col1, col2, col3 = st.columns(3)
                    col1.write(f"**Origem:** {row['origin']}")
                    col2.write(f"**Destino:** {row['destination']}")
                    col3.write(f"**Prioridade:** {row.get('priority', 'Normal')}")
        else:
            st.info("Nenhum processo em tramitação.")
    
    with tabs[2]:
        st.subheader("Histórico de Processos")
        try:
            rows = db.execute_query("""
                SELECT process_number, subject, origin, destination, status, created_at, updated_at
                FROM processes
                ORDER BY updated_at DESC
                LIMIT 50
            """)
            
            if rows:
                df = pd.DataFrame(rows)
                st.dataframe(df, hide_index=True, width="stretch")
            else:
                st.info("Nenhum histórico disponível.")
        except Exception as e:
            st.error(f"Erro ao carregar histórico: {str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGINA: AUDITORIA
# ============================================================

def page_auditoria():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    st.title("Auditoria e Rastreabilidade")
    st.caption("Registo completo de todas as operações realizadas")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        filter_action = st.text_input("Filtrar por Acção")
    with col2:
        filter_user = st.text_input("Filtrar por Utilizador")
    
    try:
        sql = "SELECT id, username, action, created_at, details FROM audit_log WHERE 1=1"
        params = []
        
        if filter_action:
            sql += " AND action LIKE ?"
            params.append(f"%{filter_action}%")
        
        if filter_user:
            sql += " AND username LIKE ?"
            params.append(f"%{filter_user}%")
        
        sql += " ORDER BY id DESC LIMIT 100"
        
        rows = db.execute_query(sql, tuple(params))
        
    except Exception as e:
        st.error(f"Erro ao carregar: {str(e)}")
        logger.error(f"Erro ao carregar auditoria: {e}")
        rows = []
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, hide_index=True, width="stretch")
    else:
        st.info("Nenhum registo encontrado.")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGINA: ADMINISTRACAO
# ============================================================

def page_administracao():
    if not check_permission("Administrador"):
        st.error("🚫 Acesso restrito a administradores.")
        return
    
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    st.title("Administração do Sistema")
    st.caption("Gestão de utilizadores, departamentos e configurações")
    
    tabs = st.tabs(["Utilizadores", "Departamentos", "Estatísticas"])
    
    with tabs[0]:
        st.subheader("Gestão de Utilizadores")
        
        with st.form("user_form"):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Utilizador *")
                full_name = st.text_input("Nome Completo *")
                email = st.text_input("Email")
            with col2:
                password = st.text_input("Palavra-passe", type="password")
                role = st.selectbox("Perfil", ["Tecnico", "Gestor", "Administrador"])
                department = st.selectbox("Departamento", ["Gabinete do Governador", "Secretaria Geral", "Financas", "Planeamento", "Infraestruturas", "Educacao", "Saude"])
            
            submitted = st.form_submit_button("Criar Utilizador", type="primary", width="stretch")
            
            if submitted:
                if not username.strip() or not full_name.strip():
                    st.error("Preenchimento obrigatório.")
                    return
                if not password:
                    st.error("Palavra-passe obrigatória.")
                    return
                
                password_hash = hash_password(password)
                now = datetime.now().isoformat()
                
                try:
                    db.execute_insert("""
                        INSERT INTO users (username, password_hash, full_name, email, role, department, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (username.strip(), password_hash, full_name.strip(), email, role, department, now))
                    
                    log_action(st.session_state.username, "Utilizador Criado", "Administracao", username)
                    st.success(f"✅ Utilizador '{username}' criado!")
                    
                except sqlite3.IntegrityError:
                    st.error(f"❌ Utilizador '{username}' já existe.")
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
        
        st.subheader("Utilizadores do Sistema")
        try:
            rows = db.execute_query("""
                SELECT id, username, full_name, role, department, email, created_at, active
                FROM users
                ORDER BY id
            """)
            
            if rows:
                df = pd.DataFrame(rows)
                st.dataframe(df, hide_index=True, width="stretch")
        except Exception as e:
            st.error(f"Erro: {str(e)}")
    
    with tabs[1]:
        st.subheader("Gestão de Departamentos")
        
        with st.form("department_form"):
            col1, col2 = st.columns(2)
            with col1:
                dept_name = st.text_input("Nome *")
                dept_code = st.text_input("Código *")
            with col2:
                dept_desc = st.text_area("Descrição")
            
            submitted = st.form_submit_button("Adicionar Departamento", type="primary", width="stretch")
            
            if submitted:
                if not dept_name.strip() or not dept_code.strip():
                    st.error("Preenchimento obrigatório.")
                    return
                
                try:
                    db.execute_insert("""
                        INSERT INTO departments (name, code, description, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (dept_name.strip(), dept_code.strip(), dept_desc, datetime.now().isoformat()))
                    
                    st.success(f"✅ Departamento '{dept_name}' adicionado!")
                    
                except sqlite3.IntegrityError:
                    st.error(f"❌ Departamento '{dept_name}' já existe.")
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
    
    with tabs[2]:
        st.subheader("Estatísticas do Sistema")
        
        try:
            user_count = db.execute_single("SELECT COUNT(*) as count FROM users")
            doc_count = db.execute_single("SELECT COUNT(*) as count FROM documents")
            proc_count = db.execute_single("SELECT COUNT(*) as count FROM processes")
            action_count = db.execute_single("SELECT COUNT(*) as count FROM audit_log")
            stats = {
                "Utilizadores": user_count['count'] if user_count else 0,
                "Documentos": doc_count['count'] if doc_count else 0,
                "Processos": proc_count['count'] if proc_count else 0,
                "Ações": action_count['count'] if action_count else 0
            }
        except Exception as e:
            st.error(f"Erro: {str(e)}")
            stats = {"Utilizadores": 0, "Documentos": 0, "Processos": 0, "Ações": 0}
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Utilizadores", stats["Utilizadores"])
        with col2:
            st.metric("Documentos", stats["Documentos"])
        with col3:
            st.metric("Processos", stats["Processos"])
        with col4:
            st.metric("Ações", stats["Ações"])
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# FUNCAO DE LOGOUT
# ============================================================

def logout():
    log_action(st.session_state.username, "Logout", "Sistema")
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.full_name = ""
    rerun_app()

# ============================================================
# APLICACAO PRINCIPAL
# ============================================================

def main():
    init_session()
    try:
        init_database()
        logger.info("Aplicação iniciada com sucesso")
        
    except Exception as e:
        st.error(f"Erro crítico: {str(e)}")
        logger.error(f"Erro crítico: {e}")
        st.stop()
    
    if not st.session_state.authenticated:
        login_screen()
        return
    
    with st.sidebar:
        st.markdown("### Governo Provincial")
        st.caption("Gestão documental")
        
        st.markdown("---")
        
        st.markdown(f"""
            <div class="sidebar-user">
                <div class="user-label">Utilizador</div>
                <div class="user-name">{st.session_state.full_name}</div>
                <div class="user-role">{st.session_state.role}</div>
            </div>
        """, unsafe_allow_html=True)
        
        page = st.radio(
            "Navegação",
            ["Painel", "Digitalizar", "Indexar", "Tramitação", "Auditoria", "Administração"],
            index=0
        )
        
        st.markdown("---")
        
        if st.button("Sair", icon=":material/logout:", width="stretch"):
            logout()
    
    pages = {
        "Painel": page_dashboard,
        "Digitalizar": page_digitalizar,
        "Indexar": page_indexar,
        "Tramitação": page_tramitacao,
        "Auditoria": page_auditoria,
        "Administração": page_administracao,
    }
    
    try:
        if page in pages:
            pages[page]()
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        logger.error(f"Erro na página {page}: {e}")
    
    st.markdown("""
        <div class="footer">
            Sistema de Gestão Documental - Governo Provincial © 2024 | Todos os direitos reservados
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
