PRE_SEQ_LEN=128

python3 cli_demo.py \
    --model_name_or_path THUDM/chatglm-6b \
    --pre_seq_len $PRE_SEQ_LEN \
    --ptuning_checkpoint chatglm_qq/checkpoint-2000