"""
天气数据采集 + MQTT 发布脚本

实战目标:
  1. requests  — 调公开 API 拉数据
  2. json      — 解析 API 返回的 JSON
  3. asyncio   — 并发处理多城市
  4. paho-mqtt — 将结果发布到 MQTT broker

用法: python weather_publisher.py
前置: Mosquitto broker 已启动 (mosquitto -v)
"""

import json
import time
import asyncio
import requests
import paho.mqtt.client as mqtt

# ========== 配置 ==========
BROKER = "localhost"
PORT = 1883
TOPIC_TEMP = "home/livingroom/sensor"         # 温度数据发到这里
TOPIC_WEATHER = "home/livingroom/weather"      # 完整天气信息发到这里

# 要查询的城市列表（用英文名，wttr.in 免费 API）
CITIES = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen"]


# ========== 同步版：单城市请求（理解 requests + json 用的）==========
def fetch_one_city_sync(city: str) -> dict | None:
    """
    同步请求单个城市天气（requests + json 基础练习）
    如果你对 requests 不熟，先看这个函数，再去看 async 版本
    """
    url = f"https://wttr.in/{city}?format=j1"  # j1 = JSON 格式
    try:
        # === requests 核心用法 ===
        resp = requests.get(url, timeout=10)

        # raise_for_status(): 如果 HTTP 状态码不是 200，直接抛异常
        resp.raise_for_status()

        # === json 核心用法 ===
        data = resp.json()  # 把 HTTP 响应体从 JSON 字符串解析为 Python dict

        # 从嵌套结构里提取当前天气
        current = data["current_condition"][0]
        result = {
            "city": city,
            "temperature": int(current["temp_C"]),
            "humidity": int(current["humidity"]),       # 湿度
            "weather_desc": current["weatherDesc"][0]["value"],  # 天气描述（晴/多云/雨...）
            "wind_speed": int(current["windspeedKmph"]),  # 风速 (km/h)
            "feels_like": int(current["FeelsLikeC"]),     # 体感温度
            "timestamp": time.time(),
        }
        return result

    except requests.exceptions.Timeout:
        print(f"  ⏱️  {city} 请求超时")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"  ❌ {city} HTTP 错误: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  ❌ {city} 网络错误: {e}")
        return None
    except (KeyError, ValueError, TypeError) as e:
        print(f"  ❌ {city} 数据解析失败: {e}")
        return None


# ========== 异步版：并发请求多城市（asyncio 核心练习）==========
async def fetch_one_city(city: str) -> dict | None:
    """
    异步请求单个城市天气。
    用 asyncio.to_thread() 把阻塞的 requests 调用扔到线程池，
    这样多个城市的请求可以"同时"发起，不用一个一个等。
    """
    # asyncio.to_thread() —— 把同步函数扔到线程池里跑，不阻塞事件循环
    return await asyncio.to_thread(fetch_one_city_sync, city)


async def fetch_all_cities() -> dict[str, dict | None]:
    """
    并发拉所有城市天气。
    
    关键概念：
      asyncio.as_completed() → 谁先返回就处理谁，不等慢的
      对比同步版：如果 4 个城市各 1 秒，同步要 4 秒，异步只要 ~1 秒
    """
    print(f"🌍 正在并发拉取 {len(CITIES)} 个城市的天气...\n")

    results = {}
    tasks = [fetch_one_city(city) for city in CITIES]

    for coro in asyncio.as_completed(tasks):
        result = await coro
        if result:
            city = result["city"]
            results[city] = result
            # 实时打印进度
            print(f"  ✅ {city:12s} | {result['temperature']}°C  "
                  f"(体感 {result['feels_like']}°C) | "
                  f"{result['weather_desc']} | "
                  f"湿度 {result['humidity']}%")

    return results


# ========== MQTT 发布 ==========
def publish_to_mqtt(results: dict[str, dict | None]):
    """
    把天气数据发布到 MQTT broker。
    对每个城市发两条消息：一条温度，一条完整天气。
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    print(f"\n📤 正在发布到 MQTT Broker ({BROKER}:{PORT})...\n")

    for city, data in results.items():
        if data is None:
            continue

        # 消息 1：仅温度（给传感器 topic，兼容你现有的 subscribe.py）
        temp_msg = json.dumps({
            "device": "weather_api",
            "city": city,
            "value": data["temperature"],
            "unit": "celsius",
            "timestamp": data["timestamp"],
        })
        client.publish(TOPIC_TEMP, temp_msg, qos=1)
        print(f"  📡 [{TOPIC_TEMP}]     ← {city}: {data['temperature']}°C")

        # 消息 2：完整天气信息
        weather_msg = json.dumps(data)
        client.publish(TOPIC_WEATHER, weather_msg, qos=1)
        print(f"  📡 [{TOPIC_WEATHER}] ← {city}: {data['weather_desc']}, "
              f"风速 {data['wind_speed']} km/h")

    time.sleep(1)  # 等消息发完
    client.loop_stop()
    client.disconnect()
    print("\n✅ 全部发布完成")


# ========== 主函数 ==========
async def main():
    """异步主函数 —— asyncio 程序的入口"""
    print("=" * 55)
    print("  🌤️  天气数据采集器 (requests + json + asyncio 实战)")
    print("=" * 55)

    # 1. 并发拉天气
    results = await fetch_all_cities()

    # 2. 发布到 MQTT
    if results:
        publish_to_mqtt(results)
    else:
        print("❌ 所有城市请求都失败了，请检查网络连接")

    # 3. 打印总结
    print("\n" + "=" * 55)
    print("  📊 总结")
    print("=" * 55)
    valid = [d for d in results.values() if d]
    if valid:
        hottest = max(valid, key=lambda x: x["temperature"])
        coldest = min(valid, key=lambda x: x["temperature"])
        avg_temp = sum(d["temperature"] for d in valid) // len(valid)
        print(f"  最热: {hottest['city']} ({hottest['temperature']}°C)")
        print(f"  最冷: {coldest['city']} ({coldest['temperature']}°C)")
        print(f"  平均: {avg_temp}°C")
    print(f"  成功: {len(valid)}/{len(CITIES)} 个城市")


# ========== 入口 ==========
if __name__ == "__main__":
    # asyncio.run() —— 运行异步主函数（这是 asyncio 的标准启动方式）
    asyncio.run(main())
