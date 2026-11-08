"""确定性组相联缓存访问模拟；LRU/FIFO，write-back/write-allocate。"""
from dataclasses import dataclass


class Cache:
    def __init__(self, capacity_bytes=32768, line_bytes=64, ways=4, policy="lru"):
        if policy not in ("lru", "fifo"):
            raise ValueError("替换策略必须为 lru 或 fifo。")
        if line_bytes <= 0 or capacity_bytes <= 0 or ways <= 0 or capacity_bytes % (line_bytes * ways):
            raise ValueError("容量必须是 cache line × ways 的整数倍。")
        self.line_bytes, self.ways, self.policy = line_bytes, ways, policy
        self.set_count = capacity_bytes // (line_bytes * ways)
        self.sets = [[] for _ in range(self.set_count)]
        self.seen = set()
        # 相同容量的 fully-associative LRU shadow，用于 3C 分类。
        self.shadow, self.lines = [], capacity_bytes // line_bytes
        self.hits = self.misses = self.writebacks = 0
        self.miss_types = dict(compulsory=0, capacity=0, conflict=0)

    def access(self, address, write=False):
        if not isinstance(address, int) or address < 0:
            raise ValueError("地址必须为非负整数。")
        block = address // self.line_bytes
        index, tag = block % self.set_count, block // self.set_count
        entries = self.sets[index]
        found = next((e for e in entries if e[0] == tag), None)
        hit = found is not None
        kind, evicted = None, None
        if hit:
            self.hits += 1
            found[1] = found[1] or write
            if self.policy == "lru":
                entries.remove(found)
                entries.append(found)
        else:
            self.misses += 1
            kind = "compulsory" if block not in self.seen else "capacity" if block not in self.shadow else "conflict"
            self.miss_types[kind] += 1
            if len(entries) >= self.ways:
                evicted = entries.pop(0)
                if evicted[1]: self.writebacks += 1
            entries.append([tag, bool(write)])
        self.seen.add(block)
        if block in self.shadow: self.shadow.remove(block)
        self.shadow.append(block)
        if len(self.shadow) > self.lines: self.shadow.pop(0)
        return dict(address=address, set=index, tag=tag, hit=hit, miss_type=kind,
                    writeback=bool(evicted and evicted[1]))

    def stats(self):
        total = self.hits + self.misses
        return dict(accesses=total, hits=self.hits, misses=self.misses,
                    hit_rate=self.hits / max(1, total), writebacks=self.writebacks,
                    miss_types=dict(self.miss_types), sets=self.set_count)


def run_cache_trace(addresses, *, capacity_bytes=32768, line_bytes=64, ways=4,
                    policy="lru", hit_latency=2, miss_latency=40):
    if not 1 <= hit_latency <= miss_latency:
        raise ValueError("延迟应为正数，miss 总延迟不得小于 hit。")
    if len(addresses) > 10000:
        raise ValueError("地址轨迹最多 10000 次访问。")
    cache = Cache(capacity_bytes, line_bytes, ways, policy)
    rows = [cache.access(int(a)) for a in addresses]
    stats = cache.stats()
    stats["serial_cycles"] = stats["hits"] * hit_latency + stats["misses"] * miss_latency
    stats["amat"] = stats["serial_cycles"] / max(1, stats["accesses"])
    return dict(rows=rows, **stats)
