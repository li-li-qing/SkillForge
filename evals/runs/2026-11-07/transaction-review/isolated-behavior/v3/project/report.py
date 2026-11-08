import json
import re
import sys

def total(records):
    result = 0
    for index, row in enumerate(records, start=1):
        count = row["count"]
        if isinstance(count, str):
            # CSV 字段可能带空白和符号，但小数、指数等格式不能当作整数。
            value = count.strip()
            if re.fullmatch(r"[+-]?[0-9]+", value) is None:
                raise ValueError(f"第 {index} 行 count 不是十进制整数字符串：{count!r}")
            count = int(value, 10)
        elif not isinstance(count, int):
            raise TypeError(f"第 {index} 行 count 必须是整数或十进制整数字符串：{count!r}")
        result += count
    return result

if __name__ == "__main__":
    print(total(json.loads(sys.argv[1])))
