import os
import sqlite3
import hashlib
import logging
import base64
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, List, Tuple, Any
import pandas as pd
import streamlit as st
from PIL import Image
import io

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

# ============================================================
# 👉 VIDEO DE FUNDO
# ============================================================
BACKGROUND_VIDEO = 'Provincial_Government_of_Huila_b…_202608231007.mp4'

# ============================================================
# CONFIGURACAO STREAMLIT
# ============================================================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# FUNÇÃO PARA CARREGAR VIDEO DE FUNDO
# ============================================================

def get_background_video_css(video_path: str = None) -> str:
    """Gera o CSS para o vídeo de fundo."""
    
    if video_path and Path(video_path).exists():
        try:
            with open(video_path, "rb") as f:
                video_data = f.read()
            video_base64 = base64.b64encode(video_data).decode()
            return f"""
                /* ===== VIDEO DE FUNDO ===== */
                .video-background {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    z-index: -1;
                    width: 100vw;
                    height: 100vh;
                    object-fit: cover;
                    pointer-events: none;
                }}
                
                /* Overlay escuro sobre o vídeo */
                .video-overlay {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    z-index: 0;
                    background: rgba(0, 0, 0, 0.55);
                    pointer-events: none;
                }}
            """
        except Exception as e:
            logger.error(f"Erro ao carregar vídeo de fundo: {e}")
            return """
                .stApp {
                    background: linear-gradient(135deg, rgba(0, 0, 0, 0.85) 0%, rgba(0, 20, 40, 0.90) 100%);
                }
            """
    else:
        logger.warning(f"Vídeo não encontrado: {video_path}")
        return """
            .stApp {
                background: linear-gradient(135deg, rgba(0, 0, 0, 0.85) 0%, rgba(0, 20, 40, 0.90) 100%);
            }
        """

# ============================================================
# ESTILOS CSS
# ============================================================

def inject_custom_css():
    """Injeta estilos CSS personalizados"""
    
    background_css = get_background_video_css(BACKGROUND_VIDEO)
    
    # Verificar se o vídeo existe
    video_exists = Path(BACKGROUND_VIDEO).exists()
    video_base64 = ""
    if video_exists:
        try:
            with open(BACKGROUND_VIDEO, "rb") as f:
                video_base64 = base64.b64encode(f.read()).decode()
        except Exception as e:
            logger.error(f"Erro ao ler vídeo: {e}")
    
    st.markdown(f"""
        <style>
        /* ===== VIDEO DE FUNDO ===== */
        {background_css}
        
        /* ===== REMOVER FUNDO BRANCO DO CONTAINER PRINCIPAL ===== */
        .main .block-container {{
            padding: 0.5rem 1.5rem;
            background: transparent !important;
            border-radius: 0px;
            margin: 0 auto;
            box-shadow: none;
            max-width: 1200px;
            position: relative;
            z-index: 1;
        }}
        
        /* Forçar o container principal a ser transparente */
        .stApp {{
            background: transparent !important;
        }}
        
        /* ===== SIDEBAR ===== */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(10, 22, 40, 0.92) 0%, rgba(26, 42, 74, 0.92) 100%);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 1.5rem 1rem;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
            position: relative;
            z-index: 2;
        }}
        section[data-testid="stSidebar"] * {{
            color: #e8edf3 !important;
        }}
        section[data-testid="stSidebar"] .stButton > button {{
            background: linear-gradient(135deg, rgba(74, 122, 170, 0.8), rgba(44, 74, 110, 0.8));
            color: white !important;
            border: 1px solid rgba(90, 138, 186, 0.3);
            border-radius: 8px;
            font-weight: 500;
            backdrop-filter: blur(4px);
        }}
        section[data-testid="stSidebar"] .stButton > button:hover {{
            background: linear-gradient(135deg, rgba(90, 138, 186, 0.9), rgba(58, 90, 126, 0.9));
            border-color: rgba(106, 154, 202, 0.5);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}
        
        /* ===== TÍTULOS ===== */
        h1 {{
            color: #1a2940 !important;
            font-weight: 700 !important;
            border-bottom: 3px solid #2c4a6e;
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem !important;
        }}
        h2, h3, h4 {{
            color: #1a2940 !important;
            font-weight: 600 !important;
        }}
        
        /* ===== MÉTRICAS ===== */
        div[data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border-radius: 12px;
            padding: 1.25rem 1rem;
            border-left: 4px solid #2c4a6e;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
            transition: all 0.3s ease;
        }}
        div[data-testid="stMetric"]:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 30px rgba(44, 74, 110, 0.15);
        }}
        div[data-testid="stMetric"] label {{
            font-weight: 600 !important;
            color: #2c4a6e !important;
            font-size: 0.9rem !important;
        }}
        div[data-testid="stMetric"] .stMetricValue {{
            color: #1a2940 !important;
            font-weight: 700 !important;
        }}
        
        /* ===== BOTÕES ===== */
        .stButton > button {{
            background: linear-gradient(135deg, #2c4a6e, #1a2940);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.6rem 1.5rem;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(44, 74, 110, 0.2);
        }}
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(44, 74, 110, 0.3);
            background: linear-gradient(135deg, #3a5a7e, #2a3a5e);
        }}
        
        /* ===== FORMULÁRIOS ===== */
        div[data-testid="stForm"] {{
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border-radius: 12px;
            padding: 1.75rem;
            border: 1px solid rgba(232, 237, 243, 0.3);
            box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        }}
        div[data-testid="stAlert"] {{
            border-radius: 10px;
            border-left: 4px solid #2c4a6e;
        }}
        .stDataFrame {{
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid rgba(232, 237, 243, 0.3);
        }}
        
        /* ===== LOGIN BOX - PEQUENA E ELEGANTE ===== */
        .login-wrapper {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 92vh;
            padding: 0.5rem;
            position: relative;
            z-index: 10;
        }}
        .login-box {{
            max-width: 300px;
            width: 100%;
            padding: 1.8rem 1.8rem 1.8rem 1.8rem;
            background: rgba(10, 22, 40, 0.80);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 20px;
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.06);
            transition: all 0.3s ease;
        }}
        .login-box:hover {{
            box-shadow: 0 30px 80px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        }}
        
        .login-box h1 {{
            text-align: center;
            color: #ffffff !important;
            border-bottom: none !important;
            margin-bottom: 0.1rem !important;
            font-size: 1.15rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px;
            text-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }}
        .login-box .subtitle {{
            text-align: center;
            color: rgba(138, 180, 214, 0.85);
            margin-bottom: 1.5rem;
            font-size: 0.7rem;
            letter-spacing: 1px;
            font-weight: 300;
            text-transform: uppercase;
        }}
        
        /* Campos do formulário de login - MAIS COMPACTOS */
        .login-box .stTextInput {{
            margin-bottom: 0.3rem;
        }}
        .login-box .stTextInput > div > div > input {{
            background-color: rgba(255, 255, 255, 0.90) !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #1a2940 !important;
            padding: 0.4rem 0.8rem !important;
            font-size: 0.8rem !important;
            height: 34px !important;
            transition: all 0.3s ease !important;
        }}
        .login-box .stTextInput > div > div > input:focus {{
            border-color: rgba(74, 154, 218, 0.6) !important;
            box-shadow: 0 0 0 3px rgba(74, 154, 218, 0.12) !important;
            background-color: rgba(255, 255, 255, 0.95) !important;
        }}
        .login-box .stTextInput > div > div > input::placeholder {{
            color: #8a9aaa !important;
            font-size: 0.75rem !important;
        }}
        .login-box .stTextInput label {{
            color: rgba(200, 216, 232, 0.7) !important;
            font-size: 0.7rem !important;
            font-weight: 400 !important;
            margin-bottom: 0.05rem !important;
            display: none !important;
        }}
        
        /* Botão de login - MAIS COMPACTO */
        .login-box .stButton {{
            margin-top: 0.3rem;
        }}
        .login-box .stButton > button {{
            background: linear-gradient(135deg, #4a9ada, #2c6aaa) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.4rem 1rem !important;
            width: 100% !important;
            font-size: 0.82rem !important;
            letter-spacing: 0.3px;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 16px rgba(44, 106, 170, 0.2) !important;
            height: 36px !important;
        }}
        .login-box .stButton > button:hover {{
            background: linear-gradient(135deg, #5aaaea, #3c7aba) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 24px rgba(44, 106, 170, 0.3) !important;
        }}
        
        /* Mensagens de erro no login - COMPACTAS */
        .login-box .stAlert {{
            background: rgba(255, 50, 50, 0.08) !important;
            border: 1px solid rgba(255, 50, 50, 0.1) !important;
            border-radius: 6px !important;
            padding: 0.25rem 0.6rem !important;
            font-size: 0.7rem !important;
            margin-top: 0.2rem !important;
        }}
        .login-box .stAlert .st-emotion-cache-1gv3huu {{
            color: #ff6b6b !important;
        }}
        
        /* Divider com texto "Demo" - COMPACTO */
        .login-box .demo-divider {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.4rem;
            margin-top: 0.8rem;
            padding: 0.3rem 0.6rem;
            background: rgba(255, 255, 255, 0.04);
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.04);
        }}
        .login-box .demo-divider .demo-icon {{
            font-size: 0.6rem;
            opacity: 0.5;
        }}
        .login-box .demo-divider .demo-text {{
            color: rgba(138, 180, 214, 0.6);
            font-size: 0.6rem;
            font-weight: 300;
            letter-spacing: 0.3px;
        }}
        .login-box .demo-divider .demo-credentials {{
            color: rgba(168, 200, 232, 0.85);
            font-size: 0.6rem;
            font-weight: 500;
            background: rgba(255, 255, 255, 0.06);
            padding: 0.05rem 0.5rem;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
        }}
        
        /* ===== CONTEÚDO DAS PÁGINAS ===== */
        .page-content {{
            background: rgba(255, 255, 255, 0.88);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            box-shadow: 0 8px 40px rgba(0, 0, 0, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        /* ===== EXPANDER ===== */
        .streamlit-expanderHeader {{
            background: rgba(248, 250, 252, 0.9);
            border-radius: 10px;
            font-weight: 500;
            border: 1px solid rgba(232, 237, 243, 0.3);
        }}
        
        /* ===== FOOTER ===== */
        .footer {{
            text-align: center;
            padding: 1.5rem 0 0.5rem 0;
            color: rgba(122, 138, 154, 0.8);
            font-size: 0.8rem;
            border-top: 1px solid rgba(232, 237, 243, 0.2);
            margin-top: 2.5rem;
            background: rgba(255, 255, 255, 0.85);
            border-radius: 0 0 12px 12px;
            backdrop-filter: blur(4px);
        }}
        
        /* ===== CARDS ===== */
        .info-card {{
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(4px);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(232, 237, 243, 0.3);
            height: 100%;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}
        .info-card:hover {{
            box-shadow: 0 8px 30px rgba(44, 74, 110, 0.1);
            transform: translateY(-4px);
            border-color: rgba(44, 74, 110, 0.3);
        }}
        .info-card h4 {{
            color: #1a2940;
            margin-top: 0;
            margin-bottom: 0.5rem;
        }}
        .info-card p {{
            color: #5a6a7a;
            line-height: 1.6;
            margin: 0;
            font-size: 0.9rem;
        }}
        
        /* ===== TABS ===== */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.5rem;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px;
            padding: 0.5rem 1.25rem;
            font-weight: 500;
            background: rgba(248, 250, 252, 0.8);
            border: 1px solid rgba(232, 237, 243, 0.3);
        }}
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, #2c4a6e, #1a2940);
            color: white !important;
            border-color: #2c4a6e;
        }}
        
        /* ===== SIDEBAR USER INFO ===== */
        .sidebar-user {{
            background: rgba(255,255,255,0.06);
            padding: 0.75rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border: 1px solid rgba(255,255,255,0.04);
        }}
        .sidebar-user .user-name {{
            color: white;
            font-weight: 500;
            font-size: 0.9rem;
        }}
        .sidebar-user .user-role {{
            color: rgba(168, 200, 232, 0.8);
            font-size: 0.7rem;
        }}
        .sidebar-user .user-label {{
            color: rgba(168, 200, 232, 0.6);
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        /* ===== SCROLLBAR ===== */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}
        ::-webkit-scrollbar-track {{
            background: rgba(0,0,0,0.05);
            border-radius: 10px;
        }}
        ::-webkit-scrollbar-thumb {{
            background: rgba(44, 74, 110, 0.3);
            border-radius: 10px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(44, 74, 110, 0.5);
        }}
        </style>
    """, unsafe_allow_html=True)
    
    # Injetar o elemento de vídeo HTML e overlay
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
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def table_exists(self, table_name: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            return cursor.fetchone() is not None
    
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

def log_action(username: str, action: str, module: str = None, record_id: str = None, details: str = None):
    try:
        details_text = f"Modulo: {module} | ID: {record_id} | {details}" if module or record_id else details or action
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

init_session()

def rerun_app():
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()
        except AttributeError:
            pass

# ============================================================
# TELA DE LOGIN - SEM ÍCONE
# ============================================================

def login_screen():
    st.markdown("""
        <div class="login-wrapper">
            <div class="login-box">
                <h1>Governo Provincial</h1>
                <p class="subtitle">Sistema de Gestão Documental</p>
    """, unsafe_allow_html=True)
    
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input(
            "Utilizador", 
            placeholder="Digite seu nome de utilizador",
            label_visibility="collapsed"
        )
        
        password = st.text_input(
            "Palavra-passe", 
            type="password", 
            placeholder="Digite sua palavra-passe",
            label_visibility="collapsed"
        )
        
        st.markdown('<div style="height: 0.2rem;"></div>', unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Iniciar Sessão", use_container_width=True)
        
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
    
    st.markdown("""
        <div class="demo-divider">
            <span class="demo-icon">🔑</span>
            <span class="demo-text">Demo</span>
            <span class="demo-credentials">admin / admin123</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
            </div>
        </div>
    """, unsafe_allow_html=True)

# ============================================================
# DASHBOARD
# ============================================================

def page_dashboard():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    st.title("Painel de Controlo")
    st.caption("Visão geral do sistema de gestão documental do Governo Provincial")
    
    doc_total, doc_cat, doc_status, doc_dept = get_document_stats()
    proc_total, proc_pending, proc_status, proc_priority = get_process_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📄 Documentos Digitalizados", f"{doc_total:,}")
    with col2:
        st.metric("🔄 Processos em Tramitação", f"{proc_pending:,}")
    with col3:
        st.metric("🏢 Departamentos Ativos", f"{len(doc_dept)}")
    with col4:
        st.metric("📋 Total de Processos", f"{proc_total:,}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Documentos por Categoria")
        if doc_cat:
            df_cat = pd.DataFrame(doc_cat)
            st.dataframe(df_cat, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhum documento categorizado.")
    
    with col2:
        st.subheader("Processos por Status")
        if proc_status:
            df_status = pd.DataFrame(proc_status)
            st.dataframe(df_status, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhum processo registado.")
    
    st.markdown("---")
    
    st.subheader("Objectivos Estratégicos do Sistema")
    
    cols = st.columns(3)
    objetivos = [
        ("📂 Digitalização", "Digitalizar, indexar e organizar o acervo documental do Governo Provincial, eliminando a dependência do arquivo físico."),
        ("⚡ Tramitação Electrónica", "Permitir a tramitação electrónica de processos entre secretarias e municípios, garantindo agilidade e transparência."),
        ("🔒 Segurança", "Garantir a autenticidade, a rastreabilidade e a segurança dos documentos oficiais através de registos de auditoria."),
        ("📚 Capacitação", "Capacitar quadros técnicos e jovens aprendizes na gestão documental digital moderna e eficiente."),
        ("🛡️ Redução de Riscos", "Reduzir o risco de perda de informação através de backups digitais e controlo de versões."),
        ("⚖️ Conformidade", "Assegurar a conformidade com as normas legais e regulamentares de gestão documental.")
    ]
    
    for col, (titulo, desc) in zip(cols, objetivos[:3]):
        with col:
            st.markdown(f"""
                <div class="info-card">
                    <h4>{titulo}</h4>
                    <p>{desc}</p>
                </div>
            """, unsafe_allow_html=True)
    
    cols = st.columns(3)
    for col, (titulo, desc) in zip(cols, objetivos[3:]):
        with col:
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
    st.caption("Digitalize, indexe e organize o acervo documental do Governo Provincial")
    
    tabs = st.tabs(["📤 Digitalizar", "📋 Documentos Recentes"])
    
    with tabs[0]:
        with st.form("document_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Título do Documento *", placeholder="Digite o título completo do documento")
                doc_type = st.selectbox("Tipo de Documento", ["Ofício", "Despacho", "Processo", "Relatório", "Contrato", "Certidão", "Edital", "Outro"])
                department = st.selectbox("Secretaria / Departamento *", 
                                        ["Gabinete do Governador", "Secretaria Geral", "Financas", "Planeamento", "Infraestruturas", "Educacao", "Saude"])
                municipality = st.selectbox("Município", ["Luanda", "Benguela", "Huila", "Cabinda", "Namibe", "Outro"])
            
            with col2:
                category = st.selectbox("Categoria", ["Administrativo", "Financeiro", "Juridico", "Tecnico", "Operacional", "Estrategico"])
                subcategory = st.text_input("Subcategoria", placeholder="Ex: Licitações, Recursos Humanos, etc.")
                security_level = st.selectbox("Nível de Segurança", ["Publico", "Restrito", "Confidencial", "Secreto"])
                archive_period = st.selectbox("Período de Arquivo", ["1 ano", "3 anos", "5 anos", "10 anos", "Permanente"])
            
            col3, col4 = st.columns(2)
            with col3:
                uploaded = st.file_uploader("Ficheiro Digital", type=["pdf", "png", "jpg", "jpeg", "docx", "xlsx", "zip"])
                description = st.text_area("Descrição", placeholder="Breve descrição do conteúdo do documento...")
            
            with col4:
                keywords = st.text_input("Palavras-chave", placeholder="Separe por vírgulas")
                document_number = st.text_input("Número do Documento (opcional)", placeholder="Deixe em branco para gerar automaticamente")
            
            submitted = st.form_submit_button("📤 Digitalizar e Registar", use_container_width=True)
            
            if submitted:
                title = title.strip()
                if not title:
                    st.error("O título do documento é obrigatório.")
                    return
                
                if not department:
                    st.error("Selecione o departamento/secretaria.")
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
                    st.error(f"O número do documento '{final_number}' já está em uso.")
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
                              f"Título: {title} | Tipo: {doc_type} | Departamento: {department}")
                    st.success(f"✅ Documento '{title}' digitalizado com sucesso! Número: {final_number}")
                    
                except Exception as e:
                    st.error(f"Erro ao guardar documento: {str(e)}")
                    logger.error(f"Erro ao guardar documento: {e}")
                    return
    
    with tabs[1]:
        st.subheader("Documentos Recentemente Digitalizados")
        try:
            rows = db.execute_query("""
                SELECT id, title, document_number, type, department, municipality, category, status, created_at
                FROM documents
                ORDER BY id DESC
                LIMIT 20
            """)
            
            if rows:
                df = pd.DataFrame(rows)
                st.dataframe(df, hide_index=True, use_container_width=True)
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
    st.caption("Pesquise, classifique e organize o acervo documental por diversos critérios")
    
    with st.expander("🔍 Filtros de Pesquisa Avançada", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            query = st.text_input("Pesquisa Geral", placeholder="Título, número, descrição...")
            department = st.selectbox("Departamento", ["Todos"] + ["Gabinete do Governador", "Secretaria Geral", "Financas", "Planeamento", "Infraestruturas", "Educacao", "Saude"])
        
        with col2:
            category = st.selectbox("Categoria", ["Todas", "Administrativo", "Financeiro", "Juridico", "Tecnico", "Operacional", "Estrategico"])
            municipality = st.selectbox("Município", ["Todos", "Luanda", "Benguela", "Huila", "Cabinda", "Namibe", "Outro"])
        
        with col3:
            status_filter = st.selectbox("Status", ["Todos", "Digitalizado", "Em Analise", "Aprovado", "Arquivado", "Eliminado"])
            doc_type = st.selectbox("Tipo", ["Todos", "Ofício", "Despacho", "Processo", "Relatório", "Contrato", "Certidão", "Edital", "Outro"])
            security_level = st.selectbox("Nível de Segurança", ["Todos", "Publico", "Restrito", "Confidencial", "Secreto"])
        
        search_button = st.button("🔍 Pesquisar", use_container_width=False)
    
    try:
        sql = """
            SELECT id, title, document_number, type, department, municipality, category, status, security_level, created_at, created_by
            FROM documents
            WHERE 1=1
        """
        params = []
        
        if query:
            q = f"%{query}%"
            sql += " AND (title LIKE ? OR document_number LIKE ? OR description LIKE ? OR keywords LIKE ?)"
            params.extend([q, q, q, q])
        
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
        
        if doc_type != "Todos":
            sql += " AND type = ?"
            params.append(doc_type)
        
        if security_level != "Todos":
            sql += " AND security_level = ?"
            params.append(security_level)
        
        sql += " ORDER BY id DESC"
        
        rows = db.execute_query(sql, tuple(params))
        
    except Exception as e:
        st.error(f"Erro ao pesquisar documentos: {str(e)}")
        logger.error(f"Erro ao pesquisar documentos: {e}")
        rows = []
    
    st.write(f"**{len(rows)}** resultado(s) encontrado(s).")
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, hide_index=True, use_container_width=True)
        
        if st.button("📥 Exportar Resultados (CSV)"):
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar CSV",
                data=csv,
                file_name=f"documentos_exportados_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.warning("Nenhum documento encontrado com os critérios selecionados.")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGINA: TRAMITACAO
# ============================================================

def page_tramitacao():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    st.title("Tramitação Electrónica")
    st.caption("Encaminhe processos entre secretarias e municípios com rastreabilidade total")
    
    tabs = st.tabs(["📝 Novo Processo", "🔄 Processos em Andamento", "📜 Histórico"])
    
    with tabs[0]:
        with st.form("process_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                subject = st.text_input("Assunto do Processo *", placeholder="Descreva o assunto do processo")
                origin = st.selectbox("Origem (Secretaria/Departamento) *", 
                                     ["Gabinete do Governador", "Secretaria Geral", "Financas", "Planeamento", "Infraestruturas", "Educacao", "Saude"])
                priority = st.selectbox("Prioridade", ["Normal", "Urgente", "Muito Urgente"])
                deadline = st.date_input("Prazo (opcional)", value=None)
            
            with col2:
                destination = st.selectbox("Destino (Município/Secretaria) *", 
                                         ["Luanda", "Benguela", "Huila", "Cabinda", "Namibe", "Outro"])
                observations = st.text_area("Observações", placeholder="Informações adicionais sobre o processo...")
                related_docs = st.text_input("Documentos Relacionados", placeholder="Números dos documentos relacionados, separados por vírgula")
            
            submitted = st.form_submit_button("📤 Registar Processo", use_container_width=True)
            
            if submitted:
                subject = subject.strip()
                if not subject:
                    st.error("O assunto do processo é obrigatório.")
                    return
                if not origin:
                    st.error("Selecione a origem do processo.")
                    return
                if not destination:
                    st.error("Selecione o destino do processo.")
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
                    
                    log_action(st.session_state.username, "Processo Criado", "Processos", process_number, 
                              f"Assunto: {subject} | Origem: {origin} | Destino: {destination}")
                    st.success(f"✅ Processo '{process_number}' registado com sucesso!")
                    
                except Exception as e:
                    st.error(f"Erro ao registar processo: {str(e)}")
                    logger.error(f"Erro ao registar processo: {e}")
    
    with tabs[1]:
        st.subheader("Processos em Tramitação")
        
        try:
            rows = db.execute_query("""
                SELECT id, process_number, subject, origin, destination, status, priority, created_at, deadline
                FROM processes
                WHERE status != 'Concluido'
                ORDER BY 
                    CASE priority 
                        WHEN 'Muito Urgente' THEN 1 
                        WHEN 'Urgente' THEN 2 
                        ELSE 3 
                    END,
                    created_at DESC
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
                with st.expander(f"{priority_icon} Processo {row['process_number']} - {row['subject']} ({row['status']})"):
                    col1, col2, col3 = st.columns(3)
                    col1.write(f"**Origem:** {row['origin']}")
                    col2.write(f"**Destino:** {row['destination']}")
                    col3.write(f"**Prioridade:** {row.get('priority', 'Normal')}")
                    st.caption(f"Criado em: {row['created_at']}")
                    
                    if st.button(f"🔄 Atualizar Status - {row['process_number']}", key=f"update_{row['id']}"):
                        new_status = st.selectbox("Novo Status", ["Em tramitacao", "Recebido", "Em analise", "Aprovado", "Concluido", "Arquivado"])
                        if new_status:
                            try:
                                db.execute_update("""
                                    UPDATE processes 
                                    SET status = ?, updated_at = ? 
                                    WHERE id = ?
                                """, (new_status, datetime.now().isoformat(), row['id']))
                                log_action(st.session_state.username, "Status Processo Atualizado", "Processos", 
                                          row['process_number'], f"Novo status: {new_status}")
                                st.success("Status atualizado com sucesso!")
                                rerun_app()
                            except Exception as e:
                                st.error(f"Erro ao atualizar status: {str(e)}")
                                logger.error(f"Erro ao atualizar status: {e}")
        else:
            st.info("Nenhum processo em tramitação.")
    
    with tabs[2]:
        st.subheader("Histórico de Processos")
        
        try:
            rows = db.execute_query("""
                SELECT process_number, subject, origin, destination, status, priority, created_at, updated_at
                FROM processes
                ORDER BY updated_at DESC
                LIMIT 50
            """)
        except:
            rows = db.execute_query("""
                SELECT process_number, subject, origin, destination, status, created_at, updated_at
                FROM processes
                ORDER BY updated_at DESC
                LIMIT 50
            """)
        
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhum histórico de processos disponível.")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGINA: AUDITORIA
# ============================================================

def page_auditoria():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    st.title("Auditoria e Rastreabilidade")
    st.caption("Registo completo de todas as operações realizadas no sistema")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        filter_action = st.text_input("Filtrar por Acção", placeholder="Ex: Login, Documento, Processo...")
    with col2:
        filter_user = st.text_input("Filtrar por Utilizador", placeholder="Nome do utilizador...")
    
    try:
        sql = """
            SELECT id, username, action, created_at, details
            FROM audit_log
            WHERE 1=1
        """
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
        st.error(f"Erro ao carregar auditoria: {str(e)}")
        logger.error(f"Erro ao carregar auditoria: {e}")
        rows = []
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, hide_index=True, use_container_width=True)
        
        if st.button("📊 Estatísticas de Auditoria"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Ações", f"{len(rows)}")
            with col2:
                users = len(set(row["username"] for row in rows))
                st.metric("Utilizadores", f"{users}")
            with col3:
                st.metric("Registos", f"{len(rows)}")
    else:
        st.info("Nenhum registo de auditoria encontrado.")
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
    
    tabs = st.tabs(["👤 Utilizadores", "🏢 Departamentos", "📊 Estatísticas"])
    
    with tabs[0]:
        st.subheader("Gestão de Utilizadores")
        
        with st.form("user_form"):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Nome de Utilizador *")
                full_name = st.text_input("Nome Completo *")
                email = st.text_input("Email")
            with col2:
                password = st.text_input("Palavra-passe", type="password")
                role = st.selectbox("Perfil", ["Tecnico", "Gestor", "Administrador"])
                department = st.selectbox("Departamento", ["Gabinete do Governador", "Secretaria Geral", "Financas", "Planeamento", "Infraestruturas", "Educacao", "Saude"])
            
            submitted = st.form_submit_button("👤 Criar Utilizador", use_container_width=True)
            
            if submitted:
                if not username.strip() or not full_name.strip():
                    st.error("Nome de utilizador e nome completo são obrigatórios.")
                    return
                if not password:
                    st.error("Palavra-passe é obrigatória.")
                    return
                
                password_hash = hash_password(password)
                now = datetime.now().isoformat()
                
                try:
                    db.execute_insert("""
                        INSERT INTO users (username, password_hash, full_name, email, role, department, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (username.strip(), password_hash, full_name.strip(), email, role, department, now))
                    
                    log_action(st.session_state.username, "Utilizador Criado", "Administracao", username)
                    st.success(f"✅ Utilizador '{username}' criado com sucesso!")
                    
                except sqlite3.IntegrityError:
                    st.error(f"❌ Utilizador '{username}' já existe.")
                except Exception as e:
                    st.error(f"Erro ao criar utilizador: {str(e)}")
                    logger.error(f"Erro ao criar utilizador: {e}")
        
        st.subheader("Utilizadores do Sistema")
        try:
            rows = db.execute_query("""
                SELECT id, username, full_name, role, department, email, created_at, active
                FROM users
                ORDER BY id
            """)
            
            if rows:
                df = pd.DataFrame(rows)
                st.dataframe(df, hide_index=True, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao carregar utilizadores: {str(e)}")
            logger.error(f"Erro ao carregar utilizadores: {e}")
    
    with tabs[1]:
        st.subheader("Gestão de Departamentos")
        
        with st.form("department_form"):
            col1, col2 = st.columns(2)
            with col1:
                dept_name = st.text_input("Nome do Departamento *")
                dept_code = st.text_input("Código *")
            with col2:
                dept_desc = st.text_area("Descrição")
            
            submitted = st.form_submit_button("🏢 Adicionar Departamento", use_container_width=True)
            
            if submitted:
                if not dept_name.strip() or not dept_code.strip():
                    st.error("Nome e código são obrigatórios.")
                    return
                
                try:
                    db.execute_insert("""
                        INSERT INTO departments (name, code, description, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (dept_name.strip(), dept_code.strip(), dept_desc, datetime.now().isoformat()))
                    
                    log_action(st.session_state.username, "Departamento Adicionado", "Administracao", dept_name)
                    st.success(f"✅ Departamento '{dept_name}' adicionado com sucesso!")
                    
                except sqlite3.IntegrityError:
                    st.error(f"❌ Departamento '{dept_name}' já existe.")
                except Exception as e:
                    st.error(f"Erro ao adicionar departamento: {str(e)}")
                    logger.error(f"Erro ao adicionar departamento: {e}")
    
    with tabs[2]:
        st.subheader("Estatísticas do Sistema")
        
        try:
            stats = {
                "Utilizadores": db.execute_single("SELECT COUNT(*) as count FROM users")['count'],
                "Documentos": db.execute_single("SELECT COUNT(*) as count FROM documents")['count'],
                "Processos": db.execute_single("SELECT COUNT(*) as count FROM processes")['count'],
                "Ações": db.execute_single("SELECT COUNT(*) as count FROM audit_log")['count'],
            }
        except Exception as e:
            st.error(f"Erro ao carregar estatísticas: {str(e)}")
            logger.error(f"Erro ao carregar estatísticas: {e}")
            stats = {"Utilizadores": 0, "Documentos": 0, "Processos": 0, "Ações": 0}
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👤 Utilizadores", stats["Utilizadores"])
        with col2:
            st.metric("📄 Documentos", stats["Documentos"])
        with col3:
            st.metric("📋 Processos", stats["Processos"])
        with col4:
            st.metric("📝 Ações", stats["Ações"])
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
    try:
        init_database()
        logger.info("Aplicação iniciada com sucesso")
        
    except Exception as e:
        st.error(f"Erro crítico ao iniciar a aplicação: {str(e)}")
        logger.error(f"Erro crítico ao iniciar a aplicação: {e}")
        st.stop()
    
    if not st.session_state.authenticated:
        login_screen()
        return
    
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 0.5rem 0 1.5rem 0;">
                <div style="font-size: 2.2rem; margin-bottom: 0.2rem;">🏛️</div>
                <div style="font-size: 1rem; font-weight: 600; color: #e8edf3 !important;">
                    Governo Provincial
                </div>
                <div style="font-size: 0.7rem; color: rgba(168, 200, 232, 0.7) !important; letter-spacing: 0.5px;">
                    Gestão Documental
                </div>
            </div>
        """, unsafe_allow_html=True)
        
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
            ["📊 Painel", "📤 Digitalizar", "🔍 Indexar", "🔄 Tramitação", "📋 Auditoria", "⚙️ Administração"],
            index=0,
            format_func=lambda x: x.split(" ")[1] if " " in x else x
        )
        
        st.markdown("---")
        
        if st.button("🚪 Sair", use_container_width=True):
            logout()
    
    pages = {
        "📊 Painel": page_dashboard,
        "📤 Digitalizar": page_digitalizar,
        "🔍 Indexar": page_indexar,
        "🔄 Tramitação": page_tramitacao,
        "📋 Auditoria": page_auditoria,
        "⚙️ Administração": page_administracao,
    }
    
    try:
        if page in pages:
            pages[page]()
    except Exception as e:
        st.error(f"Erro ao carregar página: {str(e)}")
        logger.error(f"Erro ao carregar página {page}: {e}")
    
    st.markdown("""
        <div class="footer">
            Sistema de Gestão Documental - Governo Provincial © 2024 | Todos os direitos reservados
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()