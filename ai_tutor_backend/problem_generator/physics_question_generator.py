import os
import json
import time
from openai import OpenAI

# 替换为你的DeepSeek API密钥
DEEPSEEK_API_KEY ="sk-53430f09089a436dba84954547afd5fe"

# 初始化DeepSeek API客户端
deepseek = OpenAI(api_key=DEEPSEEK_API_KEY,base_url="https://api.deepseek.com")

# 定义高中物理知识点列表
physics_knowledge_points = [
    "力与运动", "牛顿定律", "动量守恒", "能量守恒", "机械能", "功和功率", "圆周运动", "万有引力", "静电场", "电场力", "电势能", "电流", "欧姆定律", "电功率", "磁场", "电磁感应", "交流电", "光的反射与折射", "光的干涉与衍射", "热力学", "气体状态方程", "波动", "原子物理", "近代物理", "相对论", "半导体", "核反应"
]

# 定义难度级别
difficulty_levels = ["简单", "中等", "较难", "困难"]

def generate_physics_problem(knowledge_point, difficulty):
    """使用DeepSeek API生成一道物理练习题"""
    prompt = f"""请生成一道高中物理题目，满足以下要求：
1. 知识点: {knowledge_point}
2. 难度级别: {difficulty}
3. 题目要有明确的答案和解析
4. 输出格式如下:
{{
    \"题目\": \"具体题目描述\",
    \"知识点\": \"{knowledge_point}\",
    \"难度\": \"{difficulty}\",
    \"答案\": \"答案内容\",
    \"解析\": \"详细解析步骤\"
}}
请确保输出是有效的JSON格式。
"""
    try:
        response = deepseek.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0,
            max_tokens=1500
        )
        result = response.choices[0].message.content
        # 尝试解析JSON
        try:
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
    output_dir = os.path.join(os.path.dirname(__file__), "generated_problems")
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "high_school_physics_problems.csv")
    json_path = os.path.join(output_dir, "high_school_physics_problems.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write('[\n')
    csv_headers = ["题目", "知识点", "难度", "答案", "解析"]
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(','.join(csv_headers) + '\n')
    total_problems = 100
    current_count = 0
    print(f"开始生成 {total_problems} 道高中物理题目...")
    for i in range(min(25, len(physics_knowledge_points))):
        knowledge_point = physics_knowledge_points[i]
        for difficulty in difficulty_levels:
            problem = None
            attempts = 0
            while problem is None and attempts < 3:
                problem = generate_physics_problem(knowledge_point, difficulty)
                attempts += 1
                if problem is None:
                    time.sleep(1)
            if problem:
                current_count += 1
                with open(json_path, 'a', encoding='utf-8') as f:
                    json_str = json.dumps(problem, ensure_ascii=False, indent=2)
                    if current_count > 1:
                        f.write(',\n')
                    f.write(json_str)
                with open(csv_path, 'a', encoding='utf-8') as f:
                    row = [
                        f'"{str(problem.get("题目", "")).replace("\"", "\"\"")}"',
                        f'"{str(problem.get("知识点", "")).replace("\"", "\"\"")}"',
                        f'"{str(problem.get("难度", "")).replace("\"", "\"\"")}"',
                        f'"{str(problem.get("答案", "")).replace("\"", "\"\"")}"',
                        f'"{str(problem.get("解析", "")).replace("\"", "\"\"")}"'
                    ]
                    f.write(','.join(row) + '\n')
                print(f"已生成 {current_count}/{total_problems} 道题目 - {knowledge_point}({difficulty})")
            time.sleep(0.5)
            if current_count >= total_problems:
                break
        if current_count >= total_problems:
            break
    with open(json_path, 'a', encoding='utf-8') as f:
        f.write('\n]')
    print(f"成功生成 {current_count} 道物理题目")
    print(f"CSV 文件已保存到: {csv_path}")
    print(f"JSON 文件已保存到: {json_path}")

if __name__ == "__main__":
    main()