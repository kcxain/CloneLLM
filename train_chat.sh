#!/bin/bash
PRE_SEQ_LEN=128
LR=2e-3
CHAT_TRAIN_DATA=data/qq.json
CHECKPOINT_NAME=chatglm_qq

python3 main.py \
    --do_train \
    --train_file $CHAT_TRAIN_DATA \
    --prompt_column prompt \
    --response_column response \
    --history_column history \
    --overwrite_cache \
    --model_name_or_path THUDM/chatglm-6b \
    --output_dir $CHECKPOINT_NAME \
    --overwrite_output_dir \
    --max_source_length 256 \
    --max_target_length 256 \
    --per_device_train_batch_size 8 \
    --per_device_eval_batch_size 1 \
    --gradient_accumulation_steps 2 \
    --predict_with_generate \
    --max_steps 10000 \
    --logging_steps 10 \
    --save_steps 1000 \
    --learning_rate $LR \
    --pre_seq_len $PRE_SEQ_LEN \
    # --quantization_bit 4