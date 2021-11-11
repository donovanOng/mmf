export CUDA_VISIBLE_DEVICES=3

cp ./projects/ce7454/hateful_memes/train_ta.jsonl \
    /home/$USER/.cache/torch/mmf/data/datasets/hateful_memes/defaults/annotations/

mmf_run \
    config=projects/ce7454/configs/ta.yaml \
    model=concat_bert \
    dataset=hateful_memes