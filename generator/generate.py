"""Main DSA repo generator — reads Excel, writes topic folders and MD files."""
import os
import sys
import openpyxl

sys.path.insert(0, os.path.dirname(__file__))
from utils import ROOT, clean_topic, clean_title, write, make_question_md

from data_heap import DATA as D_HEAP
from data_math import DATA as D_MATH
from data_graph import DATA as D_GRAPH
from data_bst import DATA as D_BST
from data_trees import DATA as D_TREES
from data_greedy import DATA as D_GREEDY
from data_arrays1d2d import DATA as D_ARR12
from data_segtree import DATA as D_SEG
from data_arraysmat import DATA as D_ARRM
from data_search import DATA as D_SEARCH
from data_twoptr import DATA as D_TWO
from data_linkedlist import DATA as D_LL
from data_numthy import DATA as D_NUM
from data_trie import DATA as D_TRIE
from data_dp import DATA as D_DP
from data_bit import DATA as D_BIT
from data_hashing import DATA as D_HASH
from data_queues import DATA as D_QUE
from data_stack import DATA as D_STACK
from data_recursion import DATA as D_REC
from data_backtrack import DATA as D_BACK
from data_sort import DATA as D_SORT
from topic_concepts import CONCEPTS

# Merge all topic data
ALL = {}
for d in [D_HEAP, D_MATH, D_GRAPH, D_BST, D_TREES, D_GREEDY, D_ARR12, D_SEG, D_ARRM, D_SEARCH,
          D_TWO, D_LL, D_NUM, D_TRIE, D_DP, D_BIT, D_HASH, D_QUE, D_STACK, D_REC, D_BACK, D_SORT]:
    ALL.update(d)

# Map duplicated / slightly-renamed titles in the Excel to actual keys in ALL
RESOLVER = {
    # Excel title → DATA key
    ("🔍 Two Pointers", "Trapping Rain Water"): "Trapping Rain Water (TP)",
    ("🔄 Sorting / Divide & Conquer", "Kth Largest Element in an Array"): "Kth Largest Element in an Array (DC)",
    ("🧠 Dynamic Programming (DP)", "Numbers At Most N Given Digit Set"): "Numbers At Most N Given Digit Set (dup)",
    # Em/en-dash normalized aliases
    "Construct Binary Tree from Inorder & Postorder": "Construct Binary Tree from Inorder and Postorder",
    "Range Sum Query 2D \u2013 Immutable": "Range Sum Query 2D Immutable",
    "Range Sum Query \u2013 Immutable": "Range Sum Query Immutable",
    "Range Sum Query \u2013 Mutable": "Range Sum Query Mutable",
    "Two Sum II \u2013 Input Array Is Sorted": "Two Sum II Input Array Is Sorted",
}

# Special per-(topic,title) with occurrence index, since some repeat in the same topic
DUPLICATES_BY_ID = {
    44: "Number of Operations to Make Network Connected (dup)",  # second entry in Graph topic
    93: "Flipping Sign Problem (Lazy Propagation Segment Tree)",  # second flipping in Segment Tree
    155: "Count Substrings That Differ by One Character",  # second trie entry (same content)
    182: "Unique Binary Search Trees",  # duplicate DP entry; same content
}


def resolve_key(row_id, topic, title):
    if row_id in DUPLICATES_BY_ID:
        return DUPLICATES_BY_ID[row_id]
    if (topic, title) in RESOLVER:
        return RESOLVER[(topic, title)]
    if title in RESOLVER:
        return RESOLVER[title]
    if title in ALL:
        return title
    return None


def main():
    wb = openpyxl.load_workbook(os.path.join(os.path.dirname(ROOT), "DSA_Questions.xlsx"))
    ws = wb["Sheet1"]

    topics_seen = {}
    missing = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[1] is None:
            continue
        row_id = int(row[0])
        topic_raw = row[1]
        title = row[2]
        link = row[3] or ""
        topic_folder = clean_topic(topic_raw)
        topic_clean_display = topic_folder.replace("_", " ")
        topics_seen[topic_folder] = topic_raw

        key = resolve_key(row_id, topic_raw, title)
        if key is None or key not in ALL:
            missing.append((row_id, topic_raw, title))
            continue

        q = ALL[key]
        file_name = clean_title(title) + ".md"
        dest = os.path.join(ROOT, "Topics", topic_folder, file_name)
        md = make_question_md(title, link, topic_clean_display, q)
        write(dest, md)

    # Write Concepts.md per topic
    for folder in topics_seen:
        content = CONCEPTS.get(folder, f"# {folder.replace('_', ' ')} — Concepts\n\nGeneral theory and templates for this topic.\n")
        write(os.path.join(ROOT, "Topics", folder, "Concepts.md"), content)

    if missing:
        print("MISSING:")
        for m in missing: print("  ", m)
    else:
        print("All questions matched.")
    print(f"Topics written: {len(topics_seen)}")


if __name__ == "__main__":
    main()
