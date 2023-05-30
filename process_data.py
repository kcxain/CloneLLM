import argparse
import re
import json


def write_json(l, file):
    with open(file, 'w', encoding='utf8') as f:
        for j in l:
            json.dump(j, f, ensure_ascii=False)
            f.write('\n')


def check_id(s, qq_id):
    return (s in qq_id) or (qq_id in s)


# 将数据输出为标准数据集的格式
def gen_prompt(chat_list, qq_id, source_file, history_nums=5):
    data_list = []
    for item in chat_list:
        for i, turn in enumerate(item['history']):
            if check_id(turn['username'], qq_id):
                cur_history = []
                cur_d = {}
                prompt = item['history'][i - 1]['message'] if i > 0 else "你好"
                prompt = prompt.replace("[表情]", "").replace("[图片]", "").strip()
                response = item['history'][i]['message']
                response = response.replace("[表情]", "").replace("[图片]", "").strip()
                if response == "" or prompt == "":
                    continue
                cur_d["prompt"] = prompt
                cur_d["response"] = response
                history = []
                j = i - 3
                while j >= 0:
                    cur_history = []
                    pre = item['history'][j]['message']
                    pre = pre.replace("[表情]", "").replace("[图片]", "").strip()
                    cur_history.append(pre)
                    cur = item['history'][j + 1]['message']
                    cur = cur.replace("[表情]", "").replace("[图片]", "").strip()
                    if cur == "" or pre == "":
                        j -= 2
                        continue
                    cur_history.append(cur)
                    history.append(cur_history)
                    if len(history) > history_nums:
                        break
                    j -= 2
                cur_d["history"] = history
                data_list.append(cur_d)
    write_json(data_list, source_file + '.json')


# 预处理QQ聊天记录
def preprocess(lines):
    result = []
    i = 2
    while i < len(lines):
        # ================================================================
        i += 1  # 消息分组:0xFFFF
        group = re.sub(r"^消息分组:(.*)", r"\1", lines[i])
        i += 1  # ================================================================
        i += 1  # 消息对象:Lomirus
        username = re.sub(r"^消息对象:(.*)", r"\1", lines[i])
        i += 1  # ================================================================
        i += 1  #
        i += 1  # 2020-02-02 11:45:15 USERNAME
        chatHistory = []
        while i < len(lines):
            username1 = ""
            time = ""
            message = []
            # 2020-02-02 11:45:15 USERNAME
            if re.match(r"^20\d\d-\d\d-\d\d \d{1,2}:\d\d:\d\d .*", lines[i]):
                time = re.sub(r"^(20\d\d-\d\d-\d\d \d{1,2}:\d\d:\d\d) .*", r"\1", lines[i])
                username1 = re.sub(r"^20\d\d-\d\d-\d\d \d{1,2}:\d\d:\d\d (.*)", r"\1", lines[i])
            i += 1  # MESSAGE
            while i < len(lines):
                if (lines[i] == "" and i + 1 < len(lines) and
                        (re.match(r"^20\d\d-\d\d-\d\d \d{1,2}:\d\d:\d\d ", lines[i + 1]) or
                         lines[i + 1] == "================================================================")):
                    i += 1
                    break
                else:
                    message.append(lines[i])
                    i += 1
            chatHistory.append({
                "username": username1,
                "time": time,
                "message": "\n".join(message)
            })
            if i < len(lines) and lines[i] == "================================================================":
                break
        result.append({
            'group': group,
            'username': username,
            'history': chatHistory
        })
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", help="specify the input file")
    parser.add_argument("-qq_id", help="specify your QQ ID")
    parser.add_argument("-max_history", default=5, help="the max num of history for P-Tuning")
    args = parser.parse_args()

    if not args.f:
        print('Invalid argument value: -f\nYou need to specify the input file by "-f" argument.')
        exit()
    if not args.qq_id:
        print('Invalid argument value: -check_id\nYou need to specify specify your QQ ID')
        exit()

    with open(args.f, "r", encoding="utf-8") as file:
        lines = file.read().splitlines()

    result = preprocess(lines)

    gen_prompt(result, args.qq_id, args.f, args.max_history)


if __name__ == '__main__':
    main()
