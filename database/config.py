# config.py

# 数据库连接信息
SQLALCHEMY_DATABASE_URI = (
    'mysql+pymysql://root:Skyler548114!@sh-cdb-ieebubfu.sql.tencentcdb.com:22002/ai_platform?charset=utf8mb4'
)


# 是否追踪对象修改（设为 False 可以节省资源）
SQLALCHEMY_TRACK_MODIFICATIONS = False

SQLALCHEMY_ENGINE_OPTIONS = {
    "connect_args": {
        "charset": "utf8mb4"
    }
}
# 可选：设置 SQLAlchemy 输出原始 SQL 语句（用于调试）
# SQLALCHEMY_ECHO = True

# 可选：设置 Flask 的调试模式（在主程序中用更合适）
# DEBUG = True
