export CUDA_VISIBLE_DEVICES=1

cp ./projects/ce7454/hateful_memes/train_tatp.jsonl \
    /home/$USER/.cache/torch/mmf/data/datasets/hateful_memes/defaults/annotations/

mmf_run \
    config=projects/ce7454/configs/tatp.yaml \
    model=concat_bert \
    dataset=hateful_memes