def summarize_memory(memory_items):
    summary = []
    for item in memory_items:
        summary.append(item.strip())
    return "\n".join(summary)


class DeltaPolicy:
    def context_lines(self):
        return 2
