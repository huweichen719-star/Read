import csv
import json
import re
import random

# 固定随机种子，保证结果可复现（可删除）
random.seed(42)

# 配置项（请根据你的需求修改）
INPUT_CSV = "input.csv"  # 输入CSV文件
OUTPUT_CSV = "output.csv"  # 输出CSV文件
JSON_FILE = "data.json"  # 替换规则JSON文件
TARGET_COLUMN = "content"  # 需要处理的目标列名

# 正则表达式：匹配 (*)[@*,*] 格式的实体
# 捕获组：group(1)=显示文本, group(2)=json键名
PATTERN = re.compile(r'\((.*?)\)\[@([^,]+?),[^]]*?\]')


def load_json_data(json_path):
    """加载JSON替换字典"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def process_text(text, replace_map):
    """处理文本，生成所有替换后的结果"""
    # 查找所有匹配的实体
    entities = PATTERN.findall(text)
    if not entities:
        return [text]  # 无实体，返回原文本

    # 去重并保留顺序（按第一个出现的实体为准）
    unique_entities = []
    seen_keys = set()
    for display, key in entities:
        if key not in seen_keys:
            seen_keys.add(key)
            unique_entities.append((display, key))

    # 获取第一个实体的完整数组（基准数组）
    first_display, first_key = unique_entities[0]
    first_array = replace_map.get(first_key, [first_display])

    # 处理后续实体：每个随机取3个元素
    other_combinations = []
    for display, key in unique_entities[1:]:
        arr = replace_map.get(key, [display])
        # 随机选3个（不足3个则全选）
        sample = random.sample(arr, min(3, len(arr)))
        other_combinations.append(sample)

    # 生成所有组合
    result_texts = []
    for first_val in first_array:
        # 构建当前替换映射
        current_replace = {first_key: first_val}
        # 后续实体依次取值
        temp_combs = other_combinations.copy()
        for i, (display, key) in enumerate(unique_entities[1:]):
            idx = i % len(temp_combs[i])  # 循环取
            current_replace[key] = temp_combs[i][idx]

        # 执行替换
        new_text = text
        for disp, k in unique_entities:
            new_text = re.sub(
                fr'\({re.escape(disp)}\)\@{re.escape(k)},[^]]*?\]',
                current_replace[k],
                new_text
            )
        # 修复格式：去掉 ()[@,] 结构
        new_text = PATTERN.sub(lambda m: current_replace[m.group(2)], new_text)
        result_texts.append(new_text)

    return result_texts


def main():
    # 加载替换数据
    replace_map = load_json_data(JSON_FILE)

    with open(INPUT_CSV, 'r', encoding='utf-8', newline='') as infile, \
            open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as outfile:

        reader = csv.DictReader(infile)
        # 保留原CSV所有列
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        # 遍历每一行
        for row in reader:
            original_content = row[TARGET_COLUMN]
            # 生成替换后的所有文本
            processed_texts = process_text(original_content, replace_map)

            # 写入每一行结果
            for text in processed_texts:
                new_row = row.copy()
                new_row[TARGET_COLUMN] = text
                writer.writerow(new_row)

    print(f"处理完成！结果已保存到：{OUTPUT_CSV}")


if __name__ == "__main__":
    main()