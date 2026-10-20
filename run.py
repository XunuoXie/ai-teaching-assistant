import os
from pathlib import Path
from dotenv import load_dotenv

# 加载项目根目录的 .env 文件
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

from app import create_app

app = create_app()

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))

    print("🚀 AI 作业管理系统启动中...")
    print(f"📱 访问地址: http://{host}:{port}")
    print("👤 演示账户:")
    print("   - 管理员: admin / admin123")
    print("   - 教师: teacher / teacher123")
    print("   - 学生: student1 / student123")
    print("-" * 50)

    app.run(debug=True, host=host, port=port, use_reloader=False)
