import os
import json
import time
import pandas as pd
from openai import OpenAI

# 替换为你的DeepSeek API密钥
DEEPSEEK_API_KEY ="sk-53430f09089a436dba84954547afd5fe"

# 初始化DeepSeek API客户端
deepseek = OpenAI(api_key=DEEPSEEK_API_KEY,base_url="https://api.deepseek.com")

# 定义高中数学知识点列表
knowledge_points = [
    "函数概念与性质", "一次函数", "二次函数", "幂函数", "指数函数", "对数函数", "三角函数",
    "数列", "等差数列", "等比数列", "平面向量", "复数", "立体几何", "解析几何",
    "平面直角坐标系", "直线与圆", "圆锥曲线", "椭圆", "双曲线", "抛物线",
    "概率与统计", "排列组合", "二项式定理", "不等式", "三角恒等变换", "导数", "极限",
    "推理与证明", "计数原理", "数学建模", "参数方程", "极坐标"
]

# 定义难度级别
difficulty_levels = ["简单", "中等", "较难", "困难"]

def generate_math_problem(knowledge_point, difficulty):
    """使用DeepSeek API生成一道数学题"""
    prompt = f"""请生成一道高中数学题目，满足以下要求：
1. 知识点: {knowledge_point}
2. 难度级别: {difficulty}
3. 题目要有明确的答案和解析
4. 输出格式如下:
{{
    "题目": "具体题目描述",
    "知识点": "{knowledge_point}",
    "难度": "{difficulty}",
    "答案": "答案内容",
    "解析": "详细解析步骤"
}}
请确保输出是有效的JSON格式。
"""
    
    try:
        response = deepseek.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500
        )
        
        result = response.choices[0].message.content
        
        # 尝试解析JSON
        try:
            # 查找JSON字符串开始和结束的位置
            start_idx = result.find('{')
            end_idx = result.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = result[start_idx:end_idx]
                problem_data = json.loads(json_str)
                return problem_data
            else:
                return None
        except json.JSONDecodeError:
            return None
            
    except Exception as e:
        print(f"Error generating problem: {e}")
        return None

def main():
    # 创建保存问题的目录
    output_dir = os.path.join(os.path.dirname(__file__), "generated_problems")
    os.makedirs(output_dir, exist_ok=True)
    
    # 准备文件路径
    csv_path = os.path.join(output_dir, "high_school_math_problems.csv")
    json_path = os.path.join(output_dir, "high_school_math_problems.json")
    
    # 创建JSON文件并初始化为空列表
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write('[\n')  # 开始JSON数组
    
    # 创建CSV文件并写入表头
    csv_headers = ["题目", "知识点", "难度", "答案", "解析"]
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(','.join(csv_headers) + '\n')
    
    total_problems = 100  # 总共生成100道题目
    current_count = 0
    
    print(f"开始生成 {total_problems} 道高中数学题目...")
    
    # 选择前25个知识点，每个知识点生成4种难度的题目
    for i in range(min(25, len(knowledge_points))):
        knowledge_point = knowledge_points[i]
        for difficulty in difficulty_levels:
            problem = None
            attempts = 0
            
            # 尝试最多3次生成有效题目
            while problem is None and attempts < 3:
                problem = generate_math_problem(knowledge_point, difficulty)
                attempts += 1
                if problem is None:
                    time.sleep(1)  # 避免API限制
            
            if problem:
                current_count += 1
                
                # 向JSON文件追加内容
                with open(json_path, 'a', encoding='utf-8') as f:
                    json_str = json.dumps(problem, ensure_ascii=False, indent=2)
                    if current_count > 1:  # 第一个条目之后都需要加逗号
                        f.write(',\n')
                    f.write(json_str)
                
                # 向CSV文件追加内容
                with open(csv_path, 'a', encoding='utf-8') as f:
                    # 处理CSV中的特殊字符
                    row = [
                        f'"{str(problem.get("题目", "")).replace("\"", "\"\"")}"',
                        f'"{str(problem.get("知识点", "")).replace("\"", "\"\"")}"',
                        f'"{str(problem.get("难度", "")).replace("\"", "\"\"")}"',
                        f'"{str(problem.get("答案", "")).replace("\"", "\"\"")}"',
                        f'"{str(problem.get("解析", "")).replace("\"", "\"\"")}"'
                    ]
                    f.write(','.join(row) + '\n')
                
                # 显示进度
                print(f"已生成 {current_count}/{total_problems} 道题目 - {knowledge_point}({difficulty})")
            
            # 避免API限制
            time.sleep(0.5)
            
            # 如果已经达到目标题目数量，结束生成
            if current_count >= total_problems:
                break
        
        # 如果已经达到目标题目数量，结束生成
        if current_count >= total_problems:
            break
    
    # 完成JSON文件写入
    with open(json_path, 'a', encoding='utf-8') as f:
        f.write('\n]')  # 结束JSON数组
    
    print(f"成功生成 {current_count} 道数学题目")
    print(f"CSV 文件已保存到: {csv_path}")
    print(f"JSON 文件已保存到: {json_path}")

if __name__ == "__main__":
    main()