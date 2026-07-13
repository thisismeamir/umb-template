from enum import Enum


class EntryMergeStrategy(Enum):
    DEEP = 'deep_merge'
    ADDITIVE = 'additive'
    SELECTIVE = 'selective'
    REPLACE = 'replace'
