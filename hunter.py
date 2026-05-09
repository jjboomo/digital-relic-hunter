import os
import time
import requests
import re
import random
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime
from openai import OpenAI

# 1. 密钥拉取
GH_TOKEN = os.getenv("GH_TOKEN")
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

# 2. 初始化客户端
client = OpenAI(
    api_key=MINIMAX_API_KEY,
    base_url="https://api.minimax.chat/v1",
    default_headers={"GroupId": "2045840694379024402"}
)

HEADERS = {'Authorization': f'token {GH_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}

def send_email_report(content):
    """📩 核心功能：将报告发送至邮箱"""
    if not EMAIL_USER or not EMAIL_PASS:
        print("⚠️ 未配置邮箱环境变量，跳过邮件发送。")
        return

    # 设置邮件服务器（以QQ邮箱为例，如果是163则换成 smtp.163.com）
    mail_host = "smtp.qq.com"
    
    # 构造邮件对象
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = f"Relic Hunter Agent <{EMAIL_USER}>"
    message['To'] = EMAIL_RECEIVER
    message['Subject'] = Header(f"🏴‍☠️ 今日数字遗物挖掘报告 ({datetime.now().strftime('%Y-%m-%d')})", 'utf-8')

    try:
        smtp_obj = smtplib.SMTP_SSL(mail_host, 465)
        smtp_obj.login(EMAIL_USER, EMAIL_PASS)
        smtp_obj.sendmail(EMAIL_USER, [EMAIL_RECEIVER], message.as_string())
        print("📧 邮件发送成功！请查收。")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

def search_and_filter_targets():
    """雷达扫描逻辑（包含盲盒机制）"""
    languages = ["python", "javascript", "go", "rust", "cpp", "typescript", "java"]
    target_lang = random.choice(languages)
    print(f"📡 今日锁定盲盒语言：{target_lang}")
    
    query = f"stars:>500 pushed:<2024-01-01 language:{target_lang}"
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=30"
    
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200: return []
    
    items = response.json().get('items', [])
    scored_relics = []
    for repo in items:
        # ... (打分逻辑保持不变)
        last_pushed = datetime.strptime(repo['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")
        years_abandoned = (datetime.now() - last_pushed).days / 365.0
        score = (repo['stargazers_count'] / 100.0) + ((repo['forks'] / repo['stargazers_count']) * 50 if repo['stargazers_count'] > 0 else 0) - ((years_abandoned - 3) * 10 if years_abandoned > 3 else 0)
        
        scored_relics.append({
            "name": repo['full_name'], "url": repo['html_url'],
            "stars": repo['stargazers_count'], "last_pushed": repo['pushed_at'],
            "description": repo['description'] or "无描述", "score": score
        })

    top_pool = sorted(scored_relics, key=lambda x: x['score'], reverse=True)[:15]
    return random.sample(top_pool, min(3, len(top_pool)))

def evaluate_relic(repo_data):
    """大模型深度评估"""
    prompt = f"分析项目：{repo_data['name']}，描述：{repo_data['description']}。请给出尸检报告、秽土转生方案和变现路径。"
    try:
        response = client.chat.completions.create(
            model="MiniMax-M2.7",
            messages=[{"role": "system", "content": "你是一个毒舌黑客投资人。"}, {"role": "user", "content": prompt}],
            max_tokens=4000, temperature=0.4
        )
        raw_text = response.choices[0].message.content
        return re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
    except: return "评估失败"

def main():
    targets = search_and_filter_targets()
    if not targets: return

    report_content = f"🏴‍☠️ 数字遗物猎人日报 ({datetime.now().strftime('%Y-%m-%d')})\n\n"
    for item in targets:
        analysis = evaluate_relic(item)
        report_content += f"📦 猎物：{item['name']}\n链接：{item['url']}\n{analysis}\n\n---\n\n"
        time.sleep(3)

    # 1. 写入仓库存档
    with open('Daily_Report.md', 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    # 2. ⚡️ 发送到邮件
    send_email_report(report_content)
    print("✅ 任务圆满完成。")

if __name__ == "__main__":
    main()
