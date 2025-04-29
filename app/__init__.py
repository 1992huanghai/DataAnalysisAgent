import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from app.utils.json_utils import JSONEncoder
# 加载环境变量
load_dotenv()

def create_app(test_config=None):
    """创建并配置Flask应用"""
    # 创建Flask应用
    app = Flask(__name__, instance_relative_config=True)
    app.json.encoder = JSONEncoder
    # 配置CORS - 允许所有来源
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 配置应用
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        DATABASE=os.path.join(app.instance_path, 'app.sqlite'),
    )

    if test_config is None:
        # 加载实例配置
        app.config.from_pyfile('config.py', silent=True)
    else:
        # 加载测试配置
        app.config.from_mapping(test_config)

    # 确保实例文件夹存在
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # 注册蓝图 - 确保前缀为 /api
    from app.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # 添加一个简单的根路由用于测试
    @app.route('/')
    def index():
        return {"status": "ok", "message": "API服务正常运行"}

    return app