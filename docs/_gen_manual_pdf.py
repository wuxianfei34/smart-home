# -*- coding: utf-8 -*-
"""生成《智能家居系统使用说明书》PDF，作为 RAG 知识库素材"""
from fpdf import FPDF

FONT_PATH = "C:/Windows/Fonts/simhei.ttf"

pdf = FPDF()
pdf.add_font("hei", "", FONT_PATH)
pdf.add_font("hei", "B", FONT_PATH)  # 表头需要粗体样式，用同一字体充当
pdf.set_auto_page_break(auto=True, margin=18)
pdf.add_page()


def title(text):
    pdf.set_font("hei", size=22)
    pdf.cell(0, 12, text, align="C", new_x="LMARGIN", new_y="NEXT")


def subtitle(text):
    pdf.set_font("hei", size=11)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 8, text, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)


def h1(text):
    pdf.ln(3)
    pdf.set_font("hei", size=14)
    pdf.cell(0, 9, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def h2(text):
    pdf.set_font("hei", size=12)
    pdf.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def body(text):
    pdf.set_font("hei", size=11)
    pdf.multi_cell(0, 7, text)
    pdf.ln(1)


def bullet(text):
    pdf.set_font("hei", size=11)
    pdf.multi_cell(0, 7, "· " + text)
    pdf.ln(1)


# ============ 封面 ============
title("智能家居系统使用说明书")
subtitle("版本 V1.0 · 发布日期：2026 年 1 月")
pdf.ln(2)

# ============ 一、产品概述 ============
h1("一、产品概述")
body("本智能家居系统包含三类设备：智能空调、智能照明灯、温湿度传感器。"
     "所有设备可通过手机 APP 或语音助手进行控制，支持定时、场景联动等功能。")
bullet("智能空调：型号 AI-Cool X1，负责室内温度调节")
bullet("智能照明灯：型号 AI-Light L2，负责室内照明")
bullet("温湿度传感器：型号 AI-Sensor T1，负责环境数据采集")

# ============ 二、智能空调 ============
h1("二、智能空调（AI-Cool X1）")
h2("2.1 产品参数")
bullet("制冷功率：3500W")
bullet("适用面积：15～25 平方米")
bullet("能效等级：一级能效")
bullet("温度调节范围：16℃～30℃")

h2("2.2 基本操作")
bullet("开关机：短按电源键，或对语音助手说「打开空调」「关闭空调」")
bullet("温度调节：通过遥控器上下键，或说「把空调调到 26 度」")
bullet("运行模式：制冷、制热、除湿、送风四种模式")
bullet("风速调节：自动、低速、中速、高速四档")

h2("2.3 定时功能")
body("可通过 APP 设置定时开关机。例如设置「每天 22:00 关机、次日 7:00 开机」，空调会自动执行。")

h2("2.4 清洁与保养")
body("建议每月清洗一次过滤网。滤网位于室内机前盖内，取出后用清水冲洗、晾干后装回。"
     "长期不清洗会导致制冷效果下降，并可能触发 E3 故障码。")

# ============ 三、故障码表 ============
h1("三、空调故障码对照表")

faults = [
    ("E1", "室内温度传感器故障", "联系售后服务更换传感器"),
    ("E2", "室外温度传感器故障", "检查室外机传感器接线"),
    ("E3", "滤网堵塞或过脏", "取出滤网清洗干净并晾干，重新装回后断电重启"),
    ("E4", "制冷剂不足", "联系售后补充制冷剂（加氟）"),
    ("E5", "电源电压异常", "检查插座电压，避免大功率电器共用"),
    ("E6", "排水系统故障", "检查排水管是否堵塞或弯折"),
    ("E7", "压缩机过热保护", "关闭空调 30 分钟待冷却后重启"),
    ("E8", "内外机通讯故障", "断开电源 5 分钟后重新上电"),
]

with pdf.table(col_widths=(18, 48, 120), text_align="LEFT") as table:
    header = table.row()
    for c in ("故障码", "含义", "处理方法"):
        header.cell(c)
    for code, meaning, fix in faults:
        row = table.row()
        row.cell(code)
        row.cell(meaning)
        row.cell(fix)

pdf.ln(3)
body("温馨提示：出现 E3 时，先关闭空调电源，取下过滤网用清水冲洗并彻底晾干，装回后重启即可，无需报修。")

# ============ 四、智能照明灯 ============
h1("四、智能照明灯（AI-Light L2）")
h2("4.1 基本操作")
bullet("开关：对语音助手说「打开客厅灯」「关闭卧室灯」，或通过 APP 控制")
bullet("亮度调节：亮度范围 1%～100%")
bullet("色温调节：支持暖黄光（2700K）、自然白光（4000K）、冷白光（6500K）三档")

h2("4.2 场景模式")
bullet("阅读模式：亮度 80%，冷白光，适合看书")
bullet("睡眠模式：亮度 10%，暖黄光，助眠")
bullet("会客模式：亮度 100%，自然白光")

h2("4.3 常见问题")
bullet("灯连不上 WiFi：长按开关按键 5 秒直到灯快闪，进入配网模式后重新连接")
bullet("灯光闪烁：多为电压不稳定或灯泡接近寿命末期，建议更换灯泡")
bullet("语音控制无响应：检查设备是否在线、网络是否正常")

# ============ 五、温湿度传感器 ============
h1("五、温湿度传感器（AI-Sensor T1）")
h2("5.1 产品参数")
bullet("温度测量范围：-10℃～50℃")
bullet("湿度测量范围：20%～95% RH")
bullet("测量精度：温度 ±0.5℃，湿度 ±5% RH")
bullet("供电方式：内置电池，续航约 12 个月")

h2("5.2 主要用途")
body("传感器采集环境温湿度后，可联动空调自动调节。例如设置「温度高于 28℃ 自动开空调、"
     "湿度高于 70% 自动开除湿」，实现环境自动保持舒适。")

# ============ 六、FAQ ============
h1("六、常见问题 FAQ")
body("Q1：设备连不上 WiFi 怎么办？答：请确认路由器 2.4G 频段已开启，且设备与手机在同一网络下，"
     "然后长按设备按键进入配网模式重试。")
body("Q2：语音助手没有反应？答：先检查设备是否在线、网络是否畅通，确认语音指令是否包含设备名称。")
body("Q3：如何恢复出厂设置？答：长按设备复位键 10 秒，直到指示灯快闪三次，设备即恢复出厂设置。")
body("Q4：可以多台设备同时控制吗？答：可以，所有设备均可通过 APP 或语音助手单独或批量控制。")

# ============ 七、安全须知 ============
h1("七、安全须知")
bullet("空调应安装在通风良好处，出风口勿遮挡")
bullet("照明灯勿用湿手触碰，更换灯泡前请先断电")
bullet("温湿度传感器请远离水源和高温环境，避免损坏")
bullet("出现任何异常焦味、冒烟，请立即断电并联系售后")

pdf.output("D:/QQ/project/smart-home/docs/设备说明书.pdf")
print("✅ 已生成：D:/QQ/project/smart-home/docs/设备说明书.pdf")
