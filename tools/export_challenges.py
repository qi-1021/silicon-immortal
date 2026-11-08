"""导出12个可复查参考方案；不修改玩家存档。"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from silicon_professor.data.challenges import CHALLENGES
from silicon_professor.engine.challenges import challenge_design
from silicon_professor.engine.simulate import simulate
from silicon_professor.export import export_to,read_design

def main():
    output=ROOT/'docs/examples/challenges';output.mkdir(parents=True,exist_ok=True)
    for sid in CHALLENGES:
        d=challenge_design(sid,solution=True);r=simulate(d)
        if not r['signoff']['ready']:raise RuntimeError(sid+'参考方案未验收。')
        file=export_to(output/(sid+'.sil'),d,r);loaded,_=read_design(file)
        if not simulate(loaded)['challenge']['ready']:raise RuntimeError(sid+'交换后验收失效。')
    print('12个挑战参考.sil全部导入验收通过。')

if __name__=='__main__':main()
