"""GB6 score composition and source records; no SP-to-GB6 conversion."""
import math
from copy import deepcopy
from ..data.rescue_measurements import MOBILE_CHIPS


def measured_geekbench6(cid):
    chip=MOBILE_CHIPS.get(cid)
    if not chip:return []
    return [dict(deepcopy(o),device=chip['device'],os=chip['os'],basis='measured_review_snapshot')
            for o in chip['observations'] if o['test']=='Geekbench CPU' and o.get('version','').startswith('6.')]


def compose_geekbench6(integer_scores,floating_scores):
    """Combine already-normalized workload scores, not cycles or IPC.

    Primate Labs May 2024 internals: geometric means for subsections,
    weighted arithmetic composite (integer 65%, floating-point 35%).
    """
    def mean(values):
        if not isinstance(values,(list,tuple)) or not values or len(values)>100:raise ValueError('GB6需要完整且有界的分项成绩。')
        if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in values):raise ValueError('分项成绩必须为有限正数。')
        return math.exp(sum(math.log(v) for v in values)/len(values))
    return .65*mean(integer_scores)+.35*mean(floating_scores)


def projected_geekbench6(integer_scores=None,floating_scores=None):
    if integer_scores is None or floating_scores is None:
        return dict(available=False,score=None,basis='insufficient_workload_calibration',
                    reason='没有GB6各工作负载的有效归一化成绩；整数IPC、核数和SP模型分不能直接换算。')
    return dict(available=True,score=compose_geekbench6(integer_scores,floating_scores),
                basis='workload_projection',official=False,
                scope='仅汇总调用方提供的分项预测；未运行官方GB6，不认证工作负载模型准确性。')
