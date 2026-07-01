def summarize_memory(memory_items):
    summary = []
    for item in memory_items:
        clean_item = item.strip()
        if clean_item:
            summary.append(clean_item)
    return "\n".join(summary)


class DeltaPolicy:
    def context_lines(self):
        return 3

    def include_anchors(self):
        return True
