"""版本为排错元数据，读取能力由格式与字段决定。"""
GAME_VERSION='0.1.0-alpha.3'
MODEL_VERSION='analytic-v0.6+challenges-v1'


def producer():
    return dict(name='Silicon Immortal',version=GAME_VERSION,release_channel='alpha',model=MODEL_VERSION)


def diagnostic(record):
    if not isinstance(record,dict):return '来源版本未知'
    source=record.get('producer',{})
    if not isinstance(source,dict):source={}
    return f"文件游戏版本 {source.get('version','旧文件未记录')} / 格式版本 {record.get('version','未知')}；当前 {GAME_VERSION}"


def compatibility_notes(record,expected):
    notes=[]
    source=record.get('producer',{})
    if not isinstance(source,dict) or not source.get('version'):notes.append('旧文件没有游戏版本；按实际字段读取。')
    elif source['version']!=GAME_VERSION:notes.append('来源游戏版本不同，按可理解字段读取；'+diagnostic(record))
    if record.get('version')!=expected:notes.append('格式版本不同；尝试读取可理解的结构，未把版本号作为拒绝理由。')
    return notes
