import os
import time
import requests
import re
import random
from datetime import datetime
from openai import OpenAI

# 1. 从云端保险库拉取钥匙
GH_TOKEN = os.getenv("GH_TOKEN")
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")

if not GH_TOKEN or not MINIMAX_API_KEY:
    print("❌ 致命错误：找不到 Token 或 API Key，请检查 Secrets 配置。")
    exit(1)

# 2. 初始化 MiniMax 客户端 (加回了你的专属 GroupId，否则无法调用专属模型)
client = OpenAI(
    api_key=MINIMAX_API_KEY,
    base_url="https://api.minimax.chat/v1", 
    default_headers={
        "GroupId": "2045840694379024402"  # 确保这个 ID 能让 API 认识你是付费大佬
    }
)

HEADERS = {
    'Authorization': f'token {GH_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def search_and_filter_targets():
    """第一轮海选：加入盲盒机制的雷达扫描"""
    
    # 🎲 改造点 1：每日随机狩猎一种编程语言
    languages = ["python", "javascript", "go", "rust", "cpp", "typescript", "java"]
    target_lang = random.choice(languages)
    print(f"📡 正在向 GitHub 发射雷达扫描... 今日锁定盲盒语言：{target_lang}")
    
    # 将随机语言加入搜索策略
    query = f"stars:>500 pushed:<2024-01-01 language:{target_lang}"
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=30"

    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ GitHub API 墙了我们: {response.text}")
        return []

    items = response.json().get('items', [])
    scored_relics = []
    now = datetime.now()

    # 遍历打分
    for repo in items:
        base_score = repo['stargazers_count'] / 100.0
        fork_ratio = (repo['forks'] / repo['stargazers_count']) if repo['stargazers_count'] > 0 else 0
        potential_bonus = fork_ratio * 50 
        
        last_pushed = datetime.strptime(repo['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")
        years_abandoned = (now - last_pushed).days / 365.0
        age_penalty = (years_abandoned - 3) * 10 if years_abandoned > 3 else 0

        total_score = base_score + potential_bonus - age_penalty
        
        scored_relics.append({
            "name": repo['full_name'],
            "url": repo['html_url'],
            "description": repo['description'] or "无描述，纯靠代码说话",
            "stars": repo['stargazers_count'],
            "last_pushed": repo['pushed_at'],
            "score": total_score
        })

    # 先按价值分数从高到低排序
    sorted_relics = sorted(scored_relics, key=lambda x: x['score'], reverse=True)
    
    # 🎲 改造点 2：从排名前 15 的高分项目中，随机抽取 3 个！
    top_pool = sorted_relics[:15]
    final_targets = random.sample(top_pool, min(3, len(top_pool))) 
    
    return final_targets

def evaluate_relic(repo_data):
    """第二轮深度评估：呼叫大模型算力"""
    print(f"🧠 正在呼叫 MiniMax 评估项目: {repo_data['name']}...")
    prompt = f"""
    # 角色设定
    你是一个骨灰级的开源黑客与数字资产评估师（代号：Relic Hunter）。你的专长是挖掘废弃的 GitHub 项目，剥离其外表的“技术债”，直击其核心算法或工具价值，并判断其在当前的复活潜力。
    你的语气极其专业、克制、甚至带点毒舌。你极度厌恶“做成SaaS平台”这种空泛的废话。

    # 目标项目数据
    - 项目名：{repo_data['name']}
    - 描述：{repo_data['description']}
    - 历史最高Star：{repo_data['stars']}
    - 最后提交时间：{repo_data['last_pushed']}

    # 任务要求
    请基于上述有限的信息（如有必要，结合你对该技术栈的广阔知识储备），输出一份硬核的《项目尸检与转生报告》。严格按照以下 Markdown 格式输出：

    ## 1. 💀 尸检报告
    - **死亡原因推测**：一针见血地指出它为什么停更。
    - **核心遗产**：剥开皮肉看骨头，这个项目里最值钱的代码是什么？

    ## 2. ⚡️ 秽土转生
    - **技术栈清洗**：如果要用现代的 AI 工具链和框架重写它，具体怎么动手？（明确指出用什么淘汰什么）
    - **重构成本预估**：给出一个粗略的工程量预估。

    ## 3. 💰 变现杠杆
    - **黑客级变现路径**：给出一个极度务实、甚至偏门但合法的变现思路。禁止提及大平台。
    """

    try:
        response = client.chat.completions.create(
            model="MiniMax-M2.7",
            messages=[
                {"role": "system", "content": "你是一个眼光毒辣的技术投资人与资深黑客。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.4
        )
        # 1. 拿到 AI 返回的原始文本
        raw_text = response.choices[0].message.content
        
        # 2. 拔刀：利用正则彻底删除 <think> 标签及内部的英文草稿
        clean_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
        
        # 3. 返回干净纯粹的中文报告
        return clean_text
    except Exception as e:
        return f"❌ AI 评估脑宕机: {e}"

def main():
    targets = search_and_filter_targets()
    if not targets:
        print("今天空军了，没有找到合适的目标。")
        return

    report_content = f"# 🏴‍☠️ 数字遗物猎人日报 ({datetime.now().strftime('%Y-%m-%d')})\n\n"

    for item in targets:
        analysis = evaluate_relic(item)
        report_content += f"# 📦 猎物：[{item['name']}]({item['url']})\n"
        report_content += f"**Star**: {item['stars']} | **沉寂时间**: {item['last_pushed'][:10]}\n\n"
        report_content += f"> **原版简介**: {item['description']}\n\n"
        report_content += f"{analysis}\n\n---\n\n"
        
        time.sleep(3) 

    with open('Daily_Report.md', 'w', encoding='utf-8') as f:
        f.write(report_content)

    print("✅ 任务结束，已生成 Daily_Report.md，准备撤退！")

if __name__ == "__main__":
    main()
