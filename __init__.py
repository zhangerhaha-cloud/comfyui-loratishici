"""
ComfyUI LoRA提示词工具插件
该插件可以从同名JSON文件中提取LoRA的提示词，也可以将提示词保存成同名JSON文件，类似WebUI的功能
"""
import os
import json
import comfy.sd
import folder_paths

# 获取所有LoRA目录
try:
    LORA_DIRS = folder_paths.get_folder_paths("loras")
    # 如果有多个LoRA目录，取第一个作为默认目录
    LORA_DIR = LORA_DIRS[0] if LORA_DIRS else ""
    print(f"[LoRA提示词工具] 已获取LoRA目录列表: {LORA_DIRS}")
except Exception as e:
    print(f"[LoRA提示词工具] 获取LoRA目录失败: {e}")
    LORA_DIRS = []
    LORA_DIR = ""

# 获取可用的保存目录列表 - 仅包含LoRA目录
def get_available_directories():
    # 创建LoRA目录的副本，避免修改原始列表
    directories = LORA_DIRS.copy()
    
    # 按字母顺序排序
    directories.sort()
    
    return directories

# 将路径转换为显示名称
def path_to_display_name(path):
    # 获取最后两级目录作为显示名称
    parts = path.split(os.sep)
    if len(parts) >= 2:
        return f"{parts[-2]}\{parts[-1]}"
    elif len(parts) >= 1:
        return parts[-1]
    return path

class LoraPromptExtractor:
    """LoRA提示词提取节点"""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "include_positive": ("BOOLEAN", {"default": True}),
                "include_negative": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "lora_name": ("STRING", {"forceInput": True}), # 连接到LoRA加载器节点的lora_name输出
                "test_mode": ("BOOLEAN", {"default": False}), # 测试模式，使用手动输入的文件名
                "test_lora_filename": ("STRING", {"default": "example_lora_prompts"}) # 测试用的LoRA文件名
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "FLOAT",)
    RETURN_NAMES = ("positive_prompt", "negative_prompt", "preferred_weight",)
    FUNCTION = "extract_prompts"
    CATEGORY = "提示词工具"

    def extract_prompts(self, include_positive, include_negative, lora_name=None, test_mode=False, test_lora_filename=""):
        """从LoRA同名JSON文件中提取提示词和权重"""
        # 详细日志输出，帮助调试
        print(f"[LoRA提示词提取器] 接收到的lora_name: {lora_name}")
        print(f"[LoRA提示词提取器] 类型: {type(lora_name)}")
        print(f"[LoRA提示词提取器] 测试模式: {test_mode}")
        print(f"[LoRA提示词提取器] 测试文件名: {test_lora_filename}")
        print(f"[LoRA提示词提取器] LoRA目录: {LORA_DIR}")
        
        # 确定要使用的文件名
        if test_mode and test_lora_filename:
            # 在测试模式下，使用手动输入的文件名
            print(f"[LoRA提示词提取器] 使用测试模式，文件名: {test_lora_filename}")
            lora_base_name = test_lora_filename
        else:
            # 如果没有从LoRA加载器获取lora_name，返回空提示词和默认权重
            if not lora_name or not isinstance(lora_name, str):
                print(f"[LoRA提示词提取器] 警告: 无效的lora_name")
                return ("", "", 0.6)
            
            # 获取LoRA文件名（不含扩展名）
            lora_base_name = os.path.splitext(lora_name)[0]
              
        print(f"[LoRA提示词提取器] 基础文件名: {lora_base_name}")
        
        # 查找同名JSON文件 - 遍历所有LoRA目录
        json_path = None
        found_json = False
        
        # 首先尝试在所有LoRA目录中查找
        if LORA_DIRS:
            print(f"[LoRA提示词提取器] 在所有LoRA目录中查找JSON文件: {lora_base_name}.json")
            for lora_dir in LORA_DIRS:
                candidate_path = os.path.join(lora_dir, f"{lora_base_name}.json")
                print(f"[LoRA提示词提取器] 检查路径: {candidate_path}")
                if os.path.exists(candidate_path):
                    json_path = candidate_path
                    found_json = True
                    print(f"[LoRA提示词提取器] 在{lora_dir}中找到JSON文件")
                    break
        
        positive_prompt = ""
        negative_prompt = ""
        preferred_weight = 0.6  # 默认权重，预先初始化以避免UnboundLocalError
        
        # 检查JSON文件是否存在
        if found_json and json_path:
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[LoRA提示词提取器] 成功读取JSON文件内容")
                    
                    # 提取正向提示词
                    if include_positive:
                        if "activation text" in data:
                            positive_prompt = data["activation text"]
                            print(f"[LoRA提示词提取器] 从'activation text'提取正向提示词: {positive_prompt}")
                        elif "positive" in data:
                            positive_prompt = data["positive"]
                            print(f"[LoRA提示词提取器] 从'positive'提取正向提示词: {positive_prompt}")
                        elif "prompt" in data:
                            positive_prompt = data["prompt"]
                            print(f"[LoRA提示词提取器] 从'prompt'提取正向提示词: {positive_prompt}")
                        else:
                            print(f"[LoRA提示词提取器] JSON文件中未找到正向提示词字段")
                    
                    # 提取反向提示词
                    if include_negative:
                        if "negative text" in data:
                            negative_prompt = data["negative text"]
                            print(f"[LoRA提示词提取器] 从'negative text'提取反向提示词: {negative_prompt}")
                        elif "negative" in data:
                            negative_prompt = data["negative"]
                            print(f"[LoRA提示词提取器] 从'negative'提取反向提示词: {negative_prompt}")
                        else:
                            print(f"[LoRA提示词提取器] JSON文件中未找到反向提示词字段")
                    
                    # 提取权重值
                    if "preferred weight" in data and isinstance(data["preferred weight"], (int, float)):
                        preferred_weight = data["preferred weight"]
                        print(f"[LoRA提示词提取器] 提取权重值: {preferred_weight}")
                    else:
                        print(f"[LoRA提示词提取器] JSON文件中未找到有效的权重值，使用默认值: 0.6")
            except json.JSONDecodeError as e:
                print(f"[LoRA提示词提取器] 错误: JSON文件格式不正确 - {e}")
            except Exception as e:
                print(f"[LoRA提示词提取器] 错误: 读取JSON文件时发生错误 - {e}")
        else:
            print(f"[LoRA提示词提取器] 警告: 在所有LoRA目录中均未找到JSON文件: {lora_base_name}.json")
            print(f"[LoRA提示词提取器] 已检查的LoRA目录列表: {LORA_DIRS}")
            
            # 如果是测试模式，尝试使用插件目录中的示例文件
            if test_mode:
                plugin_example_path = os.path.join(os.path.dirname(__file__), f"{test_lora_filename}.json")
                if os.path.exists(plugin_example_path):
                    print(f"[LoRA提示词提取器] 测试模式: 尝试使用插件目录中的示例文件 - {plugin_example_path}")
                    try:
                        with open(plugin_example_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                            if include_positive and "activation text" in data:
                                positive_prompt = data["activation text"]
                                print(f"[LoRA提示词提取器] 测试模式: 提取正向提示词: {positive_prompt}")
                            if include_negative and "negative text" in data:
                                negative_prompt = data["negative text"]
                                print(f"[LoRA提示词提取器] 测试模式: 提取反向提示词: {negative_prompt}")
                    except Exception as e:
                        print(f"[LoRA提示词提取器] 测试模式: 读取示例文件时发生错误 - {e}")
            else:
                # 非测试模式下，提供创建JSON文件的建议
                print(f"[LoRA提示词提取器] 建议: 请在任意LoRA目录中创建名为 '{lora_base_name}.json' 的文件")
                print(f"[LoRA提示词提取器] 您可以使用'LoRA提示词保存器'节点来创建此文件")
            
        # 输出最终返回的提示词内容
        print(f"[LoRA提示词提取器] 最终返回 - 正向提示词: '{positive_prompt}', 反向提示词: '{negative_prompt}', 权重: {preferred_weight}")
        
        return (positive_prompt, negative_prompt, preferred_weight)

class LoraPromptSaver:
    """LoRA提示词保存节点"""
    @classmethod
    def INPUT_TYPES(cls):
        # 获取可用的保存目录
        directories = get_available_directories()
        # 转换为显示名称和实际路径的映射
        dir_options = {path_to_display_name(path): path for path in directories}
        
        return {
            "required": {
                "positive_prompt": ("STRING", {"default": "", "multiline": True, "placeholder": "输入正向提示词"}),
                "negative_prompt": ("STRING", {"default": "", "multiline": True, "placeholder": "输入反向提示词"}),
                "save_directory": (list(dir_options.keys()), {"default": path_to_display_name(LORA_DIR)}),
                "overwrite_existing": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "lora_name": ("STRING", {"forceInput": True}), # 连接到LoRA加载器节点的lora_name输出
                "preferred_weight": ("FLOAT", {"default": 0.6, "min": 0, "max": 2, "step": 0.1}), # 可选权重输入
                "include_sd_version": ("BOOLEAN", {"default": False}), # 是否包含SD版本
                "sd_version": (["", "1.5", "SDXL", "FLUX", "QWEN", "Other"], {"default": ""}), # SD版本类型
                "show_messages": ("BOOLEAN", {"default": True}), # 是否显示成功/失败消息
            }
        }

    RETURN_TYPES = ("BOOLEAN", "STRING",)
    RETURN_NAMES = ("success", "message",)
    FUNCTION = "save_prompts"
    CATEGORY = "提示词工具"

    def save_prompts(self, positive_prompt, negative_prompt, save_directory, overwrite_existing, lora_name=None, preferred_weight=None, include_sd_version=False, sd_version="", show_messages=True):
        """将提示词和权重保存到同名JSON文件"""
        # 检查是否从LoRA加载器获取了lora_name
        if not lora_name or not isinstance(lora_name, str) or lora_name.strip() == "":
            print(f"[LoRA提示词保存器] 错误：请连接LoRA加载器节点以获取LoRA名称")
            return (False, "错误：请连接LoRA加载器节点以获取LoRA名称")
            
        # 去除可能的扩展名
        lora_filename = os.path.splitext(lora_name)[0]
        
        # 检查文件名是否为空
        if not lora_filename or lora_filename.strip() == "":
            print(f"[LoRA提示词保存器] 错误：文件名不能为空")
            return (False, "错误：文件名不能为空")
        
        # 查找原始LoRA文件所在的目录
        original_lora_dir = None
        lora_full_name = lora_name
        # 检查所有LoRA目录中是否存在对应的LoRA文件
        for dir_path in LORA_DIRS:
            for ext in ['.safetensors', '.pt']:
                candidate_lora_path = os.path.join(dir_path, f"{lora_filename}{ext}")
                if os.path.exists(candidate_lora_path):
                    original_lora_dir = dir_path
                    lora_full_name = f"{lora_filename}{ext}"
                    print(f"[LoRA提示词保存器] 找到原始LoRA文件: {candidate_lora_path}")
                    break
            if original_lora_dir:
                break
        
        # 获取实际的保存路径
        directories = get_available_directories()
        dir_mapping = {path_to_display_name(path): path for path in directories}
        
        # 如果用户选择了特定目录，使用该目录
        if save_directory in dir_mapping:
            save_path = dir_mapping[save_directory]
        else:
            # 如果找不到对应的路径，优先使用原始LoRA目录，如果不存在则使用第一个LoRA目录
            save_path = original_lora_dir if original_lora_dir else (LORA_DIR if LORA_DIR else "")
            
        # 如果保存路径仍然为空，报错
        if not save_path:
            print(f"[LoRA提示词保存器] 错误：无法确定保存路径")
            return (False, "错误：无法确定保存路径")
        
        # 构建JSON文件路径
        json_path = os.path.join(save_path, f"{lora_filename.strip()}.json")
        
        # 记录尝试保存的路径
        print(f"[LoRA提示词保存器] 尝试保存提示词到：{json_path}")
        
        # 检查文件是否已存在
        if os.path.exists(json_path) and not overwrite_existing:
            print(f"[LoRA提示词保存器] 错误：文件已存在。启用覆盖选项以替换现有文件。")
            return (False, f"错误：文件已存在。启用覆盖选项以替换现有文件。")
        
        try:
            # 确保目录存在，如果不存在则创建
            directory = os.path.dirname(json_path)
            if directory and not os.path.exists(directory):
                print(f"[LoRA提示词保存器] 目录不存在，尝试创建：{directory}")
                os.makedirs(directory, exist_ok=True)
                print(f"[LoRA提示词保存器] 目录创建成功")
            
            # 创建要保存的数据，使用用户指定的格式
            # 使用传入的权重值，如果没有提供则使用默认值0.6
            weight_value = preferred_weight if preferred_weight is not None and isinstance(preferred_weight, (int, float)) else 0.6
            
            # 根据用户选择决定是否包含SD版本
            sd_version_value = sd_version if include_sd_version and sd_version else ""
            
            data = {
                "description": "",
                "sd version": sd_version_value,
                "activation text": positive_prompt.strip() if positive_prompt.strip() else "",
                "preferred weight": weight_value,
                "negative text": negative_prompt.strip() if negative_prompt.strip() else "",
                "notes": ""
            }
            
            # 保存JSON文件
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 记录保存成功
            print(f"[LoRA提示词保存器] 保存成功")
            
            if show_messages:
                return (True, f"成功：提示词已保存到 {json_path}")
            else:
                return (True, "")
        except Exception as e:
            # 记录保存失败及错误信息
            error_msg = str(e)
            print(f"[LoRA提示词保存器] 错误：保存失败 - {error_msg}")
            
            if show_messages:
                return (False, f"错误：保存失败 - {error_msg}")
            else:
                return (False, "")

# 注册节点
NODE_CLASS_MAPPINGS = {
    "LoraPromptExtractor": LoraPromptExtractor,
    "LoraPromptSaver": LoraPromptSaver
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoraPromptExtractor": "LoRA提示词提取器",
    "LoraPromptSaver": "LoRA提示词保存器"
}

# 导出节点映射
exported_nodes = {
    "NODE_CLASS_MAPPINGS": NODE_CLASS_MAPPINGS,
    "NODE_DISPLAY_NAME_MAPPINGS": NODE_DISPLAY_NAME_MAPPINGS
}