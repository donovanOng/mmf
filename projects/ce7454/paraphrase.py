# pip install git+git://github.com/PrithivirajDamodaran/Parrot_Paraphraser.git

import json
import random
import warnings

import torch
from parrot import Parrot


warnings.filterwarnings("ignore")


def random_state(seed):
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


random.seed(10)
random_state(1234)

# Init models (make sure you init ONLY once if you integrate this to your code)
parrot = Parrot(model_tag="prithivida/parrot_paraphraser_on_T5")

data_dir = "/home/yonglin/.cache/torch/mmf/data/datasets/"
train_annotations = "hateful_memes/defaults/annotations/train.jsonl"

original_data = []
new_data = []
with open(data_dir + train_annotations) as f:
    for line in f.readlines():
        original_data.append(json.loads(line))
        current = json.loads(line)
        phrase = current["text"]
        para_phrases = parrot.augment(
            input_phrase=phrase, max_length=200, max_return_phrases=1, use_gpu=True
        )
        if para_phrases:
            para_phrase, change = para_phrases[0]
            if change > 0 and change < 50:
                current["text"] = para_phrase
                new_data.append(current)

new_data = random.choices(new_data, k=1700)

with open("./projects/ce7454/hateful_memes/train_paraphrase.jsonl", "w+") as f:
    for data in original_data:
        json.dump(data, f)
        f.write("\n")
    for data in new_data:
        json.dump(data, f)
        f.write("\n")
