import json
import random
import nlpaug.flow as naf
import nlpaug.augmenter.word as naw

random.seed(10)

flow = naf.Sometimes(
    [
        naw.RandomWordAug("delete"),
        naw.RandomWordAug("swap"),
        naw.RandomWordAug("substitute"),
    ]
)

data_dir = "/home/yonglin/.cache/torch/mmf/data/datasets/"
train_annotations = "hateful_memes/defaults/annotations/train.jsonl"

original_data = []
new_data = []
with open(data_dir + train_annotations) as f:
    for line in f.readlines():
        original_data.append(json.loads(line))
        current = json.loads(line)
        new_text = flow.augment(current["text"])
        if new_text != current["text"]:
            current["text"] = new_text
            new_data.append(current)

new_data = random.choices(new_data, k=1700)

with open("./projects/ce7454/hateful_memes/train_random_textaug.jsonl", "w+") as f:
    for data in original_data:
        json.dump(data, f)
        f.write("\n")
    for data in new_data:
        json.dump(data, f)
        f.write("\n")
