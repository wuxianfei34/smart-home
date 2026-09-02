# 智能家居自然语言控制系统（Smart Home AIoT）

> 通过自然语言控制智能家居设备，集成 RAG 设备手册问答。
> 技术栈：LangChain + MQTT + FastAPI + Chroma

## 项目进度

- [ ] 第 1-2 周：Python  + MQTT 通信
- [ ] 第 3-4 周：LLM + LangChain 入门
- [ ] 第 5-6 周：迷你 Demo（Agent → MQTT 控灯）
- [ ] 第 7-8 周：RAG + FastAPI 接口
- [ ] 第 9-11 周：多设备协同 + Streamlit 前端
- [ ] 第 12-13 周：  GitHub 整理

## 快速启动

```bash
# 1. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动 MQTT Broker（需要先安装 Mosquitto）
mosquitto -v

# 4. 运行设备模拟器
python src/mqtt/fake_device.py

# 5. 测试 MQTT 通信
# 终端 A：
python src/mqtt/subscribe.py
# 终端 B：
python src/mqtt/publish.py
```
