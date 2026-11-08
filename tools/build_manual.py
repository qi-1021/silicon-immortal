"""从玩家Markdown生成无网络依赖的图文手册，检查所有本地资源。"""
from pathlib import Path
import html
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from silicon_professor.version import GAME_VERSION

PAGES=[('README','开始阅读'),('install','安装与启动'),('first-core','第一颗核心'),
       ('soc','第一颗SoC'),('challenges','12项设计委托'),('accelerators','GPU / NPU / ISP'),
       ('sharing','文件与分享'),('faq','常见问题'),('glossary','术语与边界')]


def validate():
    count=0
    for slug,_ in PAGES:
        source=ROOT/'docs/guide'/(slug+'.md')
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',source.read_text('utf-8')):
            if target.startswith(('https://','http://','mailto:','#')):continue
            file=(source.parent/target.split('#')[0]).resolve()
            if not file.is_file():raise ValueError(f'{source.name}缺失图片或链接：{target}')
            count+=1
    return count


def main():
    import markdown
    resources=validate();output=ROOT/'docs/player-guide';output.mkdir(parents=True,exist_ok=True)
    nav=''.join(f'<a href="#{slug}"><span>{i+1:02}</span>{title}</a>' for i,(slug,title) in enumerate(PAGES))
    articles=[]
    for slug,_ in PAGES:
        text=(ROOT/'docs/guide'/(slug+'.md')).read_text('utf-8')
        for other,_ in PAGES:text=text.replace(']('+other+'.md)','](#'+other+')')
        rendered=markdown.markdown(text,extensions=['tables','fenced_code','sane_lists'])
        articles.append(f'<article id="{slug}">{rendered}</article>')
    css=(ROOT/'docs/guide/manual.css').read_text()
    page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>硅仙人 · 玩家手册</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%23191f21'/%3E%3Cpath d='M46 18H18v14h28v14H18' fill='none' stroke='%23ddb887' stroke-width='5'/%3E%3C/svg%3E">
<style>'''+css+'''</style></head><body><aside><div class="mark">SI<span>硅仙人</span></div>
<div class="label">PLAYER FIELD GUIDE / '''+html.escape(GAME_VERSION)+'''</div><nav>'''+nav+'''</nav>
<div class="offline">离线图文手册<br>设计 · 验证 · 分享<br>powered by isqi</div></aside><main>
<header><span>FROM CORE TO SILICON</span><small>'''+html.escape(GAME_VERSION)+'''</small></header>
'''+''.join(articles)+'''<footer>本作是教学游戏。功能模型、资源调度与PPA估算分别说明。<br>powered by isqi</footer></main>
<button id="top" aria-label="返回顶部">↑</button><script>
document.getElementById('top').onclick=()=>window.scrollTo({top:0,behavior:'smooth'});
const links=[...document.querySelectorAll('nav a')];
const observer=new IntersectionObserver(entries=>{for(const e of entries)if(e.isIntersecting)for(const a of links)a.classList.toggle('active',a.hash==='#'+e.target.id);},{rootMargin:'-5% 0px -80% 0px'});
document.querySelectorAll('article').forEach(e=>observer.observe(e));
document.querySelectorAll('pre').forEach(pre=>{const b=document.createElement('button');b.textContent='复制';b.onclick=async()=>{try{await navigator.clipboard.writeText(pre.querySelector('code').textContent);b.textContent='已复制';setTimeout(()=>b.textContent='复制',1800);}catch{b.textContent='请选中文本复制';}};pre.append(b);});
</script></body></html>'''
    (output/'index.html').write_text(page,'utf-8')
    print(f'离线手册：{len(PAGES)}章，{resources}处本地图片/链接通过，{output}/index.html')

if __name__=='__main__':main()
