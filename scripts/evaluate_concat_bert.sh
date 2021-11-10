export CUDA_VISIBLE_DEVICES=2

mmf_run \
    config=projects/hateful_memes/configs/concat_bert/defaults.yaml \
    model=concat_bert \
    dataset=hateful_memes \
    run_type=test \
    checkpoint.resume_zoo=concat_bert.hateful_memes \
    checkpoint.resume_pretrained=False