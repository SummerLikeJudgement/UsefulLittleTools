import pandas as pd
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def extract_teacher_info(excel_file, start_row, end_row, output_file):
    """
    从Excel文件中提取老师信息并输出到txt文件

    Parameters:
    excel_file: Excel文件路径
    start_row: 起始行（从1开始计数，包含该行）
    end_row: 结束行（从1开始计数，包含该行）
    output_file: 输出txt文件路径
    """
    # 读取Excel文件
    df = pd.read_excel(excel_file, sheet_name=0)  # 读取第一个sheet

    # 转换为从0开始的索引
    start_idx = start_row - 1
    end_idx = end_row - 1

    # 提取指定行（注意：pandas的iloc是左闭右闭区间，所以end_idx+1）
    selected_rows = df.iloc[start_idx:end_idx + 1]

    result_list = []

    for idx, row in selected_rows.iterrows():
        # 跳过空行（如果老师姓名为空或者邮箱为空）
        if pd.isna(row.get('老师')) or pd.isna(row.get('邮箱')):
            continue

        # 提取完整老师姓名
        teacher_name = str(row.get('老师', '')) if pd.notna(row.get('老师')) else ''

        # 提取邮箱
        email = str(row.get('邮箱', '')) if pd.notna(row.get('邮箱')) else ''

        # 提取研究方向
        research_interest = str(row.get('方向', '')) if pd.notna(row.get('方向')) else ''

        # 构建字典
        teacher_info = {
            'email': email,
            'teacher_name': teacher_name,  # 改为完整姓名
            'degree_type': '硕士研究生',  # 默认值
            'research_interest': research_interest,
            'representative_works': '',  # 默认为空
            'paper_appreciation': ''  # 默认为空
        }

        result_list.append(teacher_info)

    # 写入txt文件
    with open(output_file, 'w', encoding='utf-8') as f:
        # 使用json.dump写入，indent=4使格式更美观
        json.dump(result_list, f, ensure_ascii=False, indent=4)

    print(f"成功提取 {len(result_list)} 位老师的信息")
    print(f"结果已保存到: {output_file}")

    return result_list


if __name__ == "__main__":
    # 从环境变量读取配置
    excel_file = os.getenv('EXCEL_FILE')
    start_row = int(os.getenv('START_ROW', '1'))
    end_row = int(os.getenv('END_ROW', '1'))
    output_file = os.getenv('OUTPUT_FILE', 'teacher_info.txt')

    # 验证必要的配置
    if not excel_file:
        print("❌ 错误：请在.env文件中配置EXCEL_FILE")
        exit(1)

    if not os.path.exists(excel_file):
        print(f"❌ 错误：Excel文件不存在: {excel_file}")
        exit(1)

    print(f"正在从Excel文件提取老师信息...")
    print(f"文件路径: {excel_file}")
    print(f"提取范围: 第{start_row}行到第{end_row}行")
    print("-" * 50)

    # 提取老师信息
    result = extract_teacher_info(excel_file, start_row, end_row, output_file)

    # 打印提取的结果
    print("\n提取的信息如下：")
    for teacher in result:
        print(f"姓名: {teacher['teacher_name']}, 邮箱: {teacher['email']}, 方向: {teacher['research_interest']}")