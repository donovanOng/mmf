export CUDA_VISIBLE_DEVICES=3

mmf_run \
    config=projects/hateful_memes/configs/concat_bert/defaults.yaml \
    model=concat_bert \
    dataset=hateful_memes