# check

考勤软件源码（Python 版），提供最基础的功能：

- 员工签到（checkin）
- 员工签退（checkout）
- 按日期查看考勤报表（report）

## 使用示例

```bash
python attendance.py checkin E001 --time 09:00
python attendance.py checkout E001 --time 18:00
python attendance.py report
```

默认会把数据保存到 `attendance.json`，可用 `--db` 指定其他文件。
