from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import uuid
import pandas as pd
from typing import Dict, List, Any, Optional
import json

from app.agents.user_intent_agent import UserIntentAgent
from app.agents.data_analysis_agent import DataAnalysisAgent
from app.agents.data_visualization_agent import DataVisualizationAgent
# 在适当的位置添加导入语句
from app.agents.data_analysis_conclusion_agent import DataAnalysisConclusionAgent

from app.utils.data_loader import DataLoader
from app.services.session_service import SessionService  # 导入会话服务

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件目录，用于存储可视化结果
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
VIZ_DIR = os.path.join(STATIC_DIR, "visualizations")
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data")

# 确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VIZ_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 初始化会话服务
session_service = SessionService(DATA_DIR)

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = Form(...)):
    """上传数据文件"""
    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # 保存文件
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # 加载数据
    try:
        data_loader = DataLoader(file_path)
        df = data_loader.load_data()
        
        # 存储数据集信息
        dataset_id = str(uuid.uuid4())
        original_name = file.filename
        dataset_info = {
            "name": original_name,
            "path": file_path,
            "type": "uploaded",
            "preview": df.head(5).to_dict(orient="records")
        }
        
        # 使用会话服务添加数据集
        session_service.add_dataset(session_id, dataset_id, dataset_info)
        
        return {
            "success": True,
            "dataset_id": dataset_id,
            "name": original_name,
            "preview": df.head(5).to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法加载数据: {str(e)}")

@app.post("/api/analyze")
async def analyze_data(request: Dict[str, Any]):
    """处理用户分析请求"""
    session_id = request.get("session_id")
    user_prompt = request.get("prompt")
    selected_datasets = request.get("selected_datasets", [])
    
    if not session_id or not user_prompt:
        raise HTTPException(status_code=400, detail="缺少必要参数")
    
    # 获取选中的数据集
    inputs = []
    datasets = session_service.get_datasets(session_id)
    
    for dataset_id in selected_datasets:
        if dataset_id in datasets:
            dataset = datasets[dataset_id]
            if dataset["type"] == "uploaded" or dataset["type"] == "generated":
                # 加载数据
                if "path" in dataset:
                    data_loader = DataLoader(dataset["path"])
                    df = data_loader.load_data()
                    inputs.append(df)
                elif "data_file" in dataset:
                    # 从CSV文件加载数据
                    try:
                        df = pd.read_csv(dataset["data_file"], encoding='utf-8')
                        inputs.append(df)
                    except Exception as e:
                        print(f"从CSV加载数据集 {dataset_id} 失败: {str(e)}")
                elif "data" in dataset:
                    # 如果是之前分析生成的DataFrame
                    df = pd.DataFrame(dataset["data"])
                    inputs.append(df)
    
    if not inputs:
        raise HTTPException(status_code=400, detail="未选择有效的数据集")
    
    # 1. 使用UserIntentAgent确定用户意图
    user_intent_agent = UserIntentAgent()
    intent_result = user_intent_agent.execute(inputs, user_prompt)
    
    # 添加意图识别结果日志输出
    print(f"用户意图识别结果: agent_type={intent_result.get('agent_type', 'unknown')}, confidence={intent_result.get('confidence', 0)}")
    if 'explanation' in intent_result:
        print(f"解释: {intent_result['explanation']}")
    
    # 记录到历史
    message_id = str(uuid.uuid4())
    user_message = {
        "id": message_id,
        "role": "user",
        "content": user_prompt
    }
    session_service.add_history(session_id, user_message)
    
    # 2. 根据意图调用相应的Agent
    agent_type = intent_result.get("agent_type")
    
    # 在处理分析请求的部分
    if agent_type == "data_analysis":
        # 数据分析
        data_analysis_agent = DataAnalysisAgent()
        analysis_results = data_analysis_agent.execute(inputs, user_prompt)
        
        # 使用保存的生成代码
        generated_code = data_analysis_agent.generated_code
        
        # 保存分析结果
        result_datasets = {}
        for key, df_data in analysis_results.items():
            dataset_id = str(uuid.uuid4())
            # 将列表数据转换回DataFrame以获取预览
            df = pd.DataFrame(df_data)
            dataset_info = {
                "name": key,
                "type": "generated",
                "data": df_data,
                "preview": df.head(5).to_dict(orient="records")
            }
            session_service.add_dataset(session_id, dataset_id, dataset_info)
            result_datasets[dataset_id] = dataset_info
        
        # 添加系统回复到历史
        assistant_message = {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": "已完成数据分析",
            "result_type": "analysis",
            "datasets": result_datasets,
            "generated_code": generated_code  # 添加生成的代码
        }
        session_service.add_history(session_id, assistant_message)
        
        return {
            "success": True,
            "result_type": "analysis",
            "datasets": result_datasets,
            "generated_code": generated_code  # 添加生成的代码到返回结果
        }
    
    elif agent_type == "data_visualization":
        # 数据可视化
        data_viz_agent = DataVisualizationAgent()
        viz_path = data_viz_agent.execute(inputs, user_prompt)
        
        # 生成可访问的URL
        viz_filename = os.path.basename(viz_path)
        viz_url = f"/static/visualizations/{viz_filename}"
        print(f"生成的可视化URL: {viz_url}")
        
        # 添加系统回复到历史
        assistant_message = {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": "已生成可视化结果",
            "result_type": "visualization",
            "viz_url": viz_url
        }
        session_service.add_history(session_id, assistant_message)
        
        return {
            "success": True,
            "result_type": "visualization",
            "viz_url": viz_url
        }
    
    elif agent_type == "data_analysis_plan":
        # 数据分析方案生成
        from app.agents.data_analysis_plan_agent import DataAnalysisPlanAgent
        plan_agent = DataAnalysisPlanAgent()
        plan_result = plan_agent.execute(inputs, user_prompt)
        
        # 添加系统回复到历史
        assistant_message = {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": plan_result["plan"],
            "result_type": "analysis_plan"
        }
        session_service.add_history(session_id, assistant_message)
        
        return {
            "success": True,
            "result_type": "analysis_plan",
            "plan": plan_result["plan"]
        }
    
    # 在现有的agent_type判断逻辑中添加新的代理类型处理    
    # 在处理agent_type的条件分支中添加新的分支
    elif agent_type == "data_analysis_conclusion":
        # 数据分析结论生成
        conclusion_agent = DataAnalysisConclusionAgent()
        conclusion_result = conclusion_agent.execute(inputs, user_prompt)
        
        # 添加系统回复到历史
        assistant_message = {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": conclusion_result["conclusion"],
            "result_type": "analysis_conclusion"
        }
        session_service.add_history(session_id, assistant_message)
        
        return {
            "success": True,
            "result_type": "analysis_conclusion",
            "conclusion": conclusion_result["conclusion"]
        }
    
    else:
        # 未识别的意图
        error_message = "无法理解您的请求，请尝试重新描述"
        assistant_message = {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": error_message,
            "result_type": "error"
        }
        session_service.add_history(session_id, assistant_message)
        
        return {
            "success": False,
            "result_type": "error",
            "message": error_message
        }

@app.get("/api/datasets/{session_id}")
async def get_datasets(session_id: str):
    """获取会话中的数据集列表"""
    datasets = session_service.get_datasets(session_id)
    return {"datasets": datasets}

@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """获取会话历史"""
    history = session_service.get_history(session_id)
    return {"history": history}

@app.post("/api/session")
async def create_session(request: Dict[str, Any] = None):
    """创建新会话"""
    name = "新会话"
    if request and "name" in request:
        name = request["name"]
    
    session_meta = session_service.create_session(name)
    return {"session_id": session_meta["id"], "name": session_meta["name"]}

@app.get("/api/sessions")
async def list_sessions():
    """获取所有会话列表"""
    sessions = session_service.list_sessions()
    return {"sessions": sessions}

@app.put("/api/session/{session_id}")
async def rename_session(session_id: str, request: Dict[str, Any]):
    """重命名会话"""
    if "name" not in request:
        raise HTTPException(status_code=400, detail="缺少会话名称")
    
    success = session_service.rename_session(session_id, request["name"])
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {"success": True}

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    success = session_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {"success": True}

@app.get("/api/dataset/{session_id}/{dataset_id}")
async def get_dataset(session_id: str, dataset_id: str, full: bool = False):
    """获取单个数据集详情
    
    Args:
        session_id: 会话ID
        dataset_id: 数据集ID
        full: 是否返回完整数据
    """
    datasets = session_service.get_datasets(session_id)
    
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="数据集不存在")
    
    dataset_meta = datasets[dataset_id]
    
    # 如果不需要完整数据，只返回元数据
    if not full:
        return {"dataset": dataset_meta}
    
    # 获取完整数据
    data = session_service.get_dataset_data(session_id, dataset_id)
    if data is None:
        raise HTTPException(status_code=404, detail="数据集数据不存在")
    
    # 返回完整数据
    full_dataset = dict(dataset_meta)
    full_dataset["data"] = data
    
    return {"dataset": full_dataset}

@app.get("/api/dataset/{session_id}/{dataset_id}/download")
async def download_dataset(session_id: str, dataset_id: str, background_tasks: BackgroundTasks):
    """下载数据集为CSV文件
    
    Args:
        session_id: 会话ID
        dataset_id: 数据集ID
        background_tasks: 后台任务
    """
    datasets = session_service.get_datasets(session_id)
    
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="数据集不存在")
    
    dataset_meta = datasets[dataset_id]
    
    # 如果数据已经存储为CSV
    if "data_file" in dataset_meta and os.path.exists(dataset_meta["data_file"]):
        return FileResponse(
            path=dataset_meta["data_file"],
            filename=f"{dataset_meta['name']}.csv",
            media_type="text/csv"
        )
    
    # 否则获取数据并生成CSV
    data = session_service.get_dataset_data(session_id, dataset_id)
    if data is None:
        raise HTTPException(status_code=404, detail="数据集数据不存在")
    
    # 创建临时CSV文件
    temp_file = os.path.join(UPLOAD_DIR, f"temp_{dataset_id}.csv")
    df = pd.DataFrame(data)
    df.to_csv(temp_file, index=False, encoding='utf-8')
    
    # 使用后台任务删除临时文件
    background_tasks.add_task(os.remove, temp_file)
    
    return FileResponse(
        path=temp_file,
        filename=f"{dataset_meta['name']}.csv",
        media_type="text/csv"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)