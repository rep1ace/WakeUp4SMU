import json
import datetime
import uuid
import requests
import models
import timetable
import logging
import random
from models import AggregatedCourse




def write_schedule(courses_list:dict, date, last_week, aggregated_courses: list[AggregatedCourse]):
    with open("export.wakeup_schedule", "w", encoding="utf-8") as f:
        # 固定开头
        f.write(
            '{"courseLen":50,"id":1,"name":"SMU","sameBreakLen":false,"sameLen":true,"theBreakLen":10}\n')
        f.write(
            timetable.TimeTable(int(input("请选择课表时间类别：\n1. 本部课表 2. 顺德课表\n请输入对应数字(1 or 2)\n")))+"\n")
        # 学期信息
        f.write(
            '{"background":"","courseTextColor":-1,"id":1,"itemAlpha":60,"itemHeight":64,"itemTextSize":12,"maxWeek":' + str(
                last_week) + ',"nodes":11,"showOtherWeekCourse":false,"showSat":true,"showSun":true,"showTime":false,"startDate":"' + date + '","strokeColor":-2130706433,"sundayFirst":false,"tableName":"SMU-'+date+'","textColor":-16777216,"timeTable":1,"type":0,"widgetCourseTextColor":-1,"widgetItemAlpha":60,"widgetItemHeight":64,"widgetItemTextSize":12,"widgetStrokeColor":-2130706433,"widgetTextColor":-16777216}\n')
        # 课程信息
        logging.info("课程总数: " + str(len(courses_list)))
        colors = ["#FF6B6B", "#FF9F43", "#FFC048", "#FFD93D", "#6BCB77", "#38A169", "#4ECDC4", "#1ABC9C", "#3498DB",
                  "#2C82C9", "#6A5ACD", "#9B59B6", "#D980FA", "#E84393", "#FF7675", "#FFB8B8", "#A29BFE", "#00B894",
                  "#0984E3", "#2D3436"]
        random.shuffle(colors)

        course_json = []
        cid = 0
        for j in courses_list.keys():
            course_json.append(
                {"color": colors[cid], "courseName": j, "credit": 0.0, "id": courses_list[j], "note": "",
                 "tableId": 1})
            cid += 1
        f.write(json.dumps(course_json) + "\n")

        # 课程时间信息
        course_time = []
        for e in aggregated_courses:
            course_time.append({
                "day": e.xq,
                "endTime": "",
                "endWeek": e.zc[-1],
                "startWeek": e.zc[0],
                "id": courses_list[e.kcmc],
                "level": 0,
                "ownTime": False,
                "room": e.jxcdmc,
                "startNode": e.ps,
                "startTime": "",
                "step": e.pe-e.ps+1,
                "tableId": 1,
                "teacher": e.teaxms,
                "type": 0
            })
        f.write(json.dumps(course_time) + "\n")

def upload_schedule():
    r = requests.post("https://i.wakeup.fun/share_schedule", data={
        "schedule": open("export.wakeup_schedule", "r", encoding="utf-8").read()
    }, headers={
        "version": "180",
        "User-Agent": "okhttp/3.14.9"
    })
    return r


def export_to_ics(events: models.Iterable[models.SingleEvent], start_date: datetime.date) -> str:
    """
    Export SingleEvent list to ICS format with Beijing Timezone (Asia/Shanghai).
    :param events: List of SingleEvent
    :param start_date: The start date of the first week (Week 1)
    :return: ICS string
    """
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//SMU-CALENDAR//CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-TIMEZONE:Asia/Shanghai",  # 兼容部分日历软件的全局时区扩展属性
        # --- 声明北京时间时区块 ---
        "BEGIN:VTIMEZONE",
        "TZID:Asia/Shanghai",
        "X-LIC-LOCATION:Asia/Shanghai",
        "BEGIN:STANDARD",
        "TZOFFSETFROM:+0800",
        "TZOFFSETTO:+0800",
        "TZNAME:CST",
        "DTSTART:19700101T000000",
        "END:STANDARD",
        "END:VTIMEZONE",
        # ------------------------
    ]

    for event in events:
        # Calculate date
        days_offset = (event.zc - 1) * 7 + (event.xq - 1)
        event_date = start_date + datetime.timedelta(days=days_offset)
        
        # Parse time
        start_time_str = event.qssj.replace(":", "") + "00" # HHMMSS
        end_time_str = event.jssj.replace(":", "") + "00"
        
        dtstart = f"{event_date.strftime('%Y%m%d')}T{start_time_str}"
        dtend = f"{event_date.strftime('%Y%m%d')}T{end_time_str}"
        
        description = f"教师: {event.teaxms}\\n场地: {event.jxcdmc}\\n环节: {event.jxhjmc}\\n周次: {event.zc}\\n节次: {event.ps}-{event.pe}"
        
        # ICS 标准中 DTSTAMP 应当使用 UTC 时间，末尾带 'Z' 表示 UTC
        dtstamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        
        ics_lines.append("BEGIN:VEVENT")
        ics_lines.append(f"UID:{uuid.uuid4()}@smu")
        ics_lines.append(f"DTSTAMP:{dtstamp}")
        
        # 在开始和结束时间显式加上时区 ID (TZID)
        ics_lines.append(f"DTSTART;TZID=Asia/Shanghai:{dtstart}")
        ics_lines.append(f"DTEND;TZID=Asia/Shanghai:{dtend}")
        
        ics_lines.append(f"SUMMARY:{event.kcmc}")
        ics_lines.append(f"LOCATION:{event.jxcdmc}")
        ics_lines.append(f"DESCRIPTION:{description}")
        ics_lines.append("END:VEVENT")

    ics_lines.append("END:VCALENDAR")
    return "\n".join(ics_lines)
