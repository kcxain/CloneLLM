import os
import platform
import signal
import sys
import torch

from transformers import (
    AutoConfig,
    AutoModel,
    AutoTokenizer,
    HfArgumentParser,
)
from arguments import ModelArguments, DataTrainingArguments

os_name = platform.system()
clear_command = 'cls' if os_name == 'Windows' else 'clear'
stop_stream = False


def build_prompt(history):
    prompt = "你好，我是数字世界的你，欢迎你与我对话！clear 清空对话历史，stop 终止程序"
    for query, response in history:
        prompt += f"\n本体 > {query}"
        prompt += f"\n\033[0;34;40m克隆体 > \033[0m{response}"
        prompt += f"\n"
    return prompt


def signal_handler(signal, frame):
    global stop_stream
    stop_stream = True


def main():
    global model, tokenizer

    parser = HfArgumentParser((ModelArguments))
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        # If we pass only one argument to the script and it's the path to a json file,
        # let's parse it to get our arguments.
        model_args = parser.parse_json_file(
            json_file=os.path.abspath(sys.argv[1]))[0]
    else:
        model_args = parser.parse_args_into_dataclasses()[0]

    tokenizer = AutoTokenizer.from_pretrained(model_args.model_name_or_path,
                                              trust_remote_code=True)
    config = AutoConfig.from_pretrained(model_args.model_name_or_path,
                                        trust_remote_code=True)

    config.pre_seq_len = model_args.pre_seq_len
    config.prefix_projection = model_args.prefix_projection

    if model_args.ptuning_checkpoint is not None:
        print(
            f"Loading prefix_encoder weight from {model_args.ptuning_checkpoint}"
        )
        model = AutoModel.from_pretrained(model_args.model_name_or_path,
                                          config=config,
                                          trust_remote_code=True)
        prefix_state_dict = torch.load(
            os.path.join(model_args.ptuning_checkpoint, "pytorch_model.bin"))
        new_prefix_state_dict = {}
        for k, v in prefix_state_dict.items():
            if k.startswith("transformer.prefix_encoder."):
                new_prefix_state_dict[
                    k[len("transformer.prefix_encoder."):]] = v
        model.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)
    else:
        model = AutoModel.from_pretrained(model_args.model_name_or_path,
                                          config=config,
                                          trust_remote_code=True)

    if model_args.quantization_bit is not None:
        print(f"Quantized to {model_args.quantization_bit} bit")
        model = model.quantize(model_args.quantization_bit)

    if model_args.pre_seq_len is not None:
        # P-tuning v2
        model = model.half().cuda()
        model.transformer.prefix_encoder.float().cuda()

    model = model.eval()
    history = []
    global stop_stream
    print("你好，我是数字世界的你，欢迎你与我对话！clear 清空对话历史，stop 终止程序")
    while True:
        query = input("\n本体 > ")
        if query.strip() == "stop":
            break
        if query.strip() == "clear":
            history = []
            os.system(clear_command)
            print("你好，我是数字世界的你，欢迎你与我对话！clear 清空对话历史，stop 终止程序")
            continue
        count = 0
        for response, history in model.stream_chat(tokenizer,
                                                   query,
                                                   history=history):
            if stop_stream:
                stop_stream = False
                break
            else:
                count += 1
                if count % 8 == 0:
                    os.system(clear_command)
                    print(build_prompt(history), flush=True)
                    signal.signal(signal.SIGINT, signal_handler)
        os.system(clear_command)
        print(build_prompt(history), flush=True)


if __name__ == "__main__":
    main()
