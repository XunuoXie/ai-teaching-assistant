
import os
import sys
import subprocess
import shutil
import uuid
import time
import logging
from flask import current_app

logger = logging.getLogger(__name__)

FONT_CONFIG = '''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import warnings
import os
import gc
import atexit
warnings.filterwarnings('ignore')

chinese_fonts = [
    '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
    '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 
    '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
    '/usr/share/fonts/truetype/arphic/uming.ttc',
    '/usr/share/fonts/truetype/arphic/ukai.ttc',
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/STHeiti Light.ttc',
    '/System/Library/Fonts/Hiragino Sans GB.ttc'
]

available_fonts = []
for font_path in chinese_fonts:
    if os.path.exists(font_path):
        try:
            fm.fontManager.addfont(font_path)
            available_fonts.append(font_path)
        except Exception:
            pass

all_font_names = [f.name for f in fm.fontManager.ttflist]
chinese_font_candidates = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Noto Sans SC', 'Droid Sans Fallback', 
                          'AR PL UMing CN', 'AR PL UKai CN', 'PingFang SC', 'Heiti SC', 
                          'Hiragino Sans GB', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS']

font_found = None
for candidate in chinese_font_candidates:
    if candidate in all_font_names:
        font_found = candidate
        break

if font_found:
    matplotlib.rcParams['font.sans-serif'] = [font_found, 'DejaVu Sans']
    matplotlib.rcParams['font.family'] = 'sans-serif'
    plt.rcParams.update({
        'font.sans-serif': [font_found, 'DejaVu Sans'],
        'font.family': 'sans-serif',
        'axes.unicode_minus': False
    })
else:
    matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
    matplotlib.rcParams['font.family'] = 'sans-serif'
    plt.rcParams.update({
        'font.sans-serif': ['DejaVu Sans'],
        'font.family': 'sans-serif', 
        'axes.unicode_minus': False
    })

_original_show = plt.show
_image_counter = 0
_saved_figs = set()  # 已保存的figure id集合

def _has_animation():
    """检查当前是否有动画对象"""
    for obj in gc.get_objects():
        try:
            if 'FuncAnimation' in str(type(obj)):
                return True
        except:
            pass
    return False

def _patched_show(*args, **kwargs):
    global _image_counter
    try:
        fig = plt.gcf()
        if fig.get_axes():
            # 如果有动画，则跳过PNG保存（动画会在退出时保存为GIF）
            if not _has_animation():
                _image_counter += 1
                filename = f'output_{_image_counter}.png'
                fig.savefig(filename, dpi=100, bbox_inches='tight')
                _saved_figs.add(id(fig))
    except Exception:
        pass

plt.show = _patched_show

_animation_counter = 0

def _auto_save_animation_gif():
    """自动检测并保存 FuncAnimation 对象为 GIF"""
    global _animation_counter
    saved_count = 0
    for obj in gc.get_objects():
        try:
            if 'FuncAnimation' in str(type(obj)) and hasattr(obj, 'save'):
                _animation_counter += 1
                gif_filename = f'animation_{_animation_counter}.gif'
                obj.save(gif_filename, writer='pillow', fps=10, dpi=100)
                print(f"[动画已保存] {gif_filename}")
                saved_count += 1
        except Exception as e:
            pass
    
    if saved_count > 0:
        print(f"[共保存 {saved_count} 个动画]")

def _auto_save_figures():
    """脚本退出时自动保存未通过 plt.show() 保存的图片"""
    global _image_counter
    try:
        if _has_animation():
            return  # 有动画时跳过，由动画处理器处理
        # 遍历所有未关闭的figure
        for fig_num in plt.get_fignums():
            fig = plt.figure(fig_num)
            if fig.get_axes() and id(fig) not in _saved_figs:
                _image_counter += 1
                filename = f'output_{_image_counter}.png'
                fig.savefig(filename, dpi=100, bbox_inches='tight')
                _saved_figs.add(id(fig))
    except Exception:
        pass

atexit.register(_auto_save_figures)
atexit.register(_auto_save_animation_gif)
'''


def execute_python_code(code: str, timeout_sec: int = None) -> tuple:
    if timeout_sec is None:
        timeout_sec = current_app.config.get('CODE_EXECUTION_TIMEOUT', 600)
    
    session_id = str(uuid.uuid4())[:8]
    sandbox_base = current_app.config.get('SANDBOX_BASE', 'sandbox_temp')
    output_dir = current_app.config.get('OUTPUT_DIR', 'static/outputs')
    
    work_dir = os.path.join(sandbox_base, session_id)
    os.makedirs(work_dir, exist_ok=True)
    script_path = os.path.join(work_dir, 'script.py')
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(FONT_CONFIG + '\n' + code)
    
    env = os.environ.copy()
    mpl_config_dir = os.path.join(work_dir, '.matplotlib')
    os.makedirs(mpl_config_dir, exist_ok=True)
    env['MPLCONFIGDIR'] = mpl_config_dir
    if 'USERPROFILE' in os.environ:
        env['USERPROFILE'] = os.environ['USERPROFILE']
    if 'HOME' in os.environ:
        env['HOME'] = os.environ['HOME']
    env['PATH'] = os.environ.get('PATH', '')
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env=env
        )
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired:
        stdout = ""
        stderr = f"⏰ 代码执行超时（{timeout_sec}秒）"
    except Exception as e:
        stdout = ""
        stderr = f"执行错误: {str(e)}"
    
    images = []
    for fname in os.listdir(work_dir):
        if fname.lower().endswith(('.png', '.gif', '.jpg', '.jpeg')):
            src = os.path.join(work_dir, fname)
            new_name = f"{int(time.time())}_{uuid.uuid4().hex[:6]}_{fname}"
            dst = os.path.join(output_dir, new_name)
            shutil.move(src, dst)
            images.append(new_name)
    
    try:
        shutil.rmtree(work_dir)
    except Exception as e:
        logger.warning(f"无法删除沙箱目录 {work_dir}: {e}")
    
    return stdout, stderr, images
