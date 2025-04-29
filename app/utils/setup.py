import os
from app.utils.file_utils import get_project_root, ensure_dir_exists

def setup_data_directories():
    """设置数据目录"""
    root_dir = get_project_root()
    
    # 创建必要的数据目录
    dirs = [
        os.path.join(root_dir, 'data', 'uploads'),
        os.path.join(root_dir, 'data', 'outputs'),
        os.path.join(root_dir, 'data', 'conversations'),
    ]
    
    for dir_path in dirs:
        ensure_dir_exists(dir_path)
    
    # 确保元数据文件存在
    metadata_path = os.path.join(root_dir, 'data', 'dataset_metadata.json')
    if not os.path.exists(metadata_path):
        with open(metadata_path, 'w') as f:
            f.write('{"datasets": []}')
    
    print("数据目录设置完成")