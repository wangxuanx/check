import xlrd
import xlwt
from argparse import ArgumentParser

# 跳过的非真实人员名单（可按需增删）
SKIP_NAMES = {'106', '8888', '333', '管理', '管理宋'}


def parse_args():
    parser = ArgumentParser(description='考勤打卡数据标准化汇总工具')
    parser.add_argument('input', help='考勤的原文件（打卡流水 .xls）')
    parser.add_argument('file', help='需要写入的标准化文件（模板 .xls）')
    parser.add_argument('days', help='考勤的天数')
    parser.add_argument('--out-file', default='./结果.xls', help='处理之后的数据输出（默认 ./结果.xls）')

    args = parser.parse_args()
    return args


def write_excal(excel_out, write_sheet, name, time, day, log=print):
    """向输出工作表中写入某个人某一天的考勤时间。

    excel_out:   模板工作簿（xlrd），用于按姓名定位行号
    write_sheet: 输出工作表（xlwt）
    name:        员工姓名
    time:        已清洗的打卡时间列表
    day:         第几天（0 基），写入列号为 day+1，对齐模板表头 1~31
    log:         日志回调
    """
    wr_time = ''
    if time is not None:
        wr_time = ' '.join(time)

    sheet_out = excel_out.sheet_by_index(0)
    cols_out: list = sheet_out.col_values(1)  # 模板第 2 列：姓名

    if name in SKIP_NAMES:
        return

    p_list = None
    if len(name) == 2:
        # 兼容模板里两个字的姓名被写成 "张  三" 这种带空格的变体
        candidates = [name[0] + '  ' + name[1], name]
        for c in candidates:
            try:
                p_list = cols_out.index(c)
                break
            except ValueError:
                continue
    else:
        try:
            p_list = cols_out.index(name)
        except ValueError:
            p_list = None

    if p_list is None:
        log(f'警告：模板中找不到姓名「{name}」，已跳过')
        return

    log(f'写入{day + 1}号，考勤时间为：{wr_time}')
    write_sheet.write(p_list, 0, name)
    write_sheet.write(p_list, day + 1, wr_time)


def clear_time(check_time):
    """标准化打卡时间。

    - check_time 应为已排序的时间字符串列表（形如 '07:26'）。
    - 若条数 <= 4（正常上下班 + 午休 4 次），原样返回。
    - 若条数 > 4，按"小时"去重：同一小时内只保留最早的一次打卡，
      用来合并同小时内的重复刷脸记录。
    """
    l = len(check_time)

    if l <= 4:
        return check_time

    by_hour = {}
    for t in check_time:
        if not t or len(t) < 2:
            continue
        h = t[:2]
        # 同一小时只保留时间最小（最早）的一条
        if h not in by_hour or t < by_hour[h]:
            by_hour[h] = t

    return sorted(by_hour.values())


def process(input_path, file_path, days, out_file, log=print):
    """核心处理流程，供 CLI 与 GUI 共用。返回 True 表示成功。"""
    excel_in = xlrd.open_workbook_xls(input_path)
    excel_out = xlrd.open_workbook_xls(file_path)  # 模板，用于按姓名定位行

    sheet_in = excel_in.sheet_by_index(0)

    write_out = xlwt.Workbook()
    write_sheet = write_out.add_sheet('考勤', cell_overwrite_ok=True)

    cols_in: list = sheet_in.col_values(0)  # 第一列：姓名
    name_list = list(set(cols_in))
    log(f'总签到人数: {name_list}')

    days = int(days)
    n = int(sheet_in.nrows / days)  # 打卡总人数
    log(f'共 {days} 天，{n} 人，开始处理……')

    for i in range(0, n):
        user_name = sheet_in.row_values(i * days)[0]
        for j in range(0, days):
            row_idx = i * days + j
            if row_idx >= sheet_in.nrows:
                break
            user_time = sheet_in.row_values(row_idx)[2]
            if not user_time:
                user_time = ''
            user_time = sorted(set(user_time.split(' ')))

            check_time = clear_time(user_time)
            write_excal(excel_out, write_sheet, user_name, check_time, j, log=log)

        log(f'{user_name} 考勤信息写入成功!')

    write_out.save(out_file)
    log(f'全部完成，已保存到：{out_file}')
    return True


def main(args):
    return process(args.input, args.file, args.days, args.out_file)


if __name__ == '__main__':
    main(parse_args())
