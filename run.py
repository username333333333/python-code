from app import create_app
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    # 获取环境变量中的配置
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    
    # 优化Flask配置，提高性能
    app.config.update({
        'JSON_SORT_KEYS': False,  # 禁用JSON响应排序，提高性能
        'JSONIFY_PRETTYPRINT_REGULAR': debug,  # 只有在调试模式下才美化JSON输出
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 限制请求大小为16MB
    })
    
    # 在生产环境中建议使用Gunicorn或Waitress等WSGI服务器
    # 这里添加生产环境提示
    if not debug:
        print("=== 生产环境部署建议 ===")
        print("在生产环境中，建议使用WSGI服务器（如Gunicorn或Waitress）运行应用：")
        print("例如：waitress-serve --host={host} --port={port} 'run:app'")
        print("========================")
    
    # 启动应用
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True,  # 启用多线程处理请求
        processes=1  # 在Windows上，processes参数不生效，使用多线程
    )