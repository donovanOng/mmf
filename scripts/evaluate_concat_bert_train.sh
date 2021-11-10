export CUDA_VISIBLE_DEVICES=2

mmf_run \
    config=projects/hateful_memes/configs/concat_bert/defaults.yaml \
    model=concat_bert \
    dataset=hateful_memes \
    run_type=test \
    checkpoint.resume_file=./save/concat_bert_final.pth \
    checkpoint.resume_pretrained=False