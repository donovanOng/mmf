import json
from collections import Counter

data_dir = "/home/yonglin/.cache/torch/mmf/data/datasets/"
train_annotations = "hateful_memes/defaults/annotations/train.jsonl"

words = []
with open(data_dir + train_annotations) as f:
    for line in f.readlines():
        print(line)
        captions = json.loads(line)['text'].split(" ")
        if "black" in captions:
            print(captions)
        words.extend(captions)

word_counts = Counter(words)

with open("./projects/ce7454/word_counts.tsv", "w+") as out:
    for word, count in word_counts.most_common():
        out.write(f"{word}\t{count}\n")
