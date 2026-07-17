"""
PumpGuard 仿真数据引擎 — 主入口

用法：
  python engine.py                    # 使用 config.yaml 默认配置
  python engine.py --output ./data    # 指定输出目录
  python engine.py --mqtt             # 仿真 + MQTT 实时推送

与架构说明书第六章 / 开发步骤 Phase 1 完全对齐。
"""

import json
import os
import sys
import time
import yaml
import click
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from models.pump_physics import PumpPhysicsModel, make_pump_specs, PumpSpecs
from models.degradation import DegradationModel, DegradationParams
from models.fault_injection import FaultInjector, FaultConfig
from sensors.vibration import VibrationSensor
from sensors.current import CurrentSensor
from sensors.thermal import ThermalSensor


class SimulationEngine:
    """泵群仿真引擎主类"""

    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        sim_cfg = self.config["simulation"]
        self.num_pumps = sim_cfg["num_pumps"]
        self.duration_days = sim_cfg["duration_days"]
        self.sample_interval = sim_cfg["sample_interval_sec"]
        self.rng = np.random.default_rng(sim_cfg["seed"])

        # 泵实例
        self.pumps: list[dict] = []       # {"specs": PumpSpecs, "physics": PumpPhysicsModel, ...}
        self._init_pumps()

        # 传感器
        self.vib_sensor = VibrationSensor(rng=self.rng)
        self.cur_sensor = CurrentSensor(rng=self.rng)
        self.thm_sensor = ThermalSensor(rng=self.rng)

        # MQTT（可选）
        self.mqtt_client = None
        if self.config.get("mqtt"):
            self._init_mqtt()

    def _init_pumps(self):
        """初始化泵群：分配型号 + 退化参数 + 故障注入"""
        pump_types = self.config["pump_types"]
        fault_scenarios = self.config["fault_scenarios"]
        total_configured = sum(t["count"] for t in pump_types)
        assert total_configured == self.num_pumps, \
            f"泵型号配置总数 ({total_configured}) != num_pumps ({self.num_pumps})"

        pump_idx = 0
        for pt_cfg in pump_types:
            for i in range(pt_cfg["count"]):
                pump_id = f"PUMP-{pump_idx:04d}"
                specs = make_pump_specs(pump_id, pt_cfg)
                physics = PumpPhysicsModel(specs)
                deg_params = DegradationParams.random_for_pump(pt_cfg["name"], self.rng)
                degradation = DegradationModel(deg_params, self.rng)
                injector = FaultInjector(specs, self.rng)

                # 随机注入故障
                for fs in fault_scenarios:
                    if self.rng.random() < fs["probability"]:
                        onset = self.rng.integers(fs["onset_day_min"], fs["onset_day_max"])
                        sev = self.rng.uniform(*fs["severity_range"])
                        injector.add_fault(FaultConfig(
                            fault_type=fs["type"],
                            onset_day=float(onset),
                            severity=sev,
                            progression_rate=self.rng.uniform(0.3, 0.8),
                        ))

                self.pumps.append({
                    "specs": specs,
                    "physics": physics,
                    "degradation": degradation,
                    "injector": injector,
                    "location": self._random_location(),
                    "start_date": datetime(2023, 1, 1) + timedelta(days=int(self.rng.integers(0, 365))),
                })
                pump_idx += 1

        print(f"[Engine] 已初始化 {len(self.pumps)} 台虚拟泵 "
              f"({sum(1 for p in self.pumps if p['injector'].faults)} 台注入故障)")

    def _random_location(self) -> dict:
        """随机生成泵的地理位置（模拟全球分布）"""
        return {
            "lat": round(self.rng.uniform(-35, 55), 4),
            "lon": round(self.rng.uniform(-120, 150), 4),
            "country": self.rng.choice(["中国", "印度", "巴西", "印尼", "尼日利亚",
                                         "埃及", "越南", "泰国", "墨西哥", "南非"]),
        }

    def _init_mqtt(self):
        """初始化 MQTT 连接"""
        try:
            import paho.mqtt.client as mqtt
            mqtt_cfg = self.config["mqtt"]
            self.mqtt_client = mqtt.Client(client_id="pumpguard-sim-engine")
            self.mqtt_client.connect(mqtt_cfg["host"], mqtt_cfg["port"])
            self.mqtt_client.loop_start()
            self.mqtt_topic_prefix = mqtt_cfg.get("topic_prefix", "pump")
            print(f"[Engine] MQTT 已连接 {mqtt_cfg['host']}:{mqtt_cfg['port']}")
        except ImportError:
            print("[Engine] paho-mqtt 未安装，跳过 MQTT 连接")
        except Exception as e:
            print(f"[Engine] MQTT 连接失败: {e}")

    def simulate_one_sample(self, pump: dict, day: float) -> dict:
        """对一台泵仿真一个采样点"""
        specs = pump["specs"]
        physics = pump["physics"]
        degradation = pump["degradation"]
        injector = pump["injector"]

        # 工况模拟（负载率 60-100%，随机波动）
        load_ratio = 0.7 + 0.3 * np.sin(day * np.pi / 180) + self.rng.uniform(-0.1, 0.1)
        load_ratio = max(0.3, min(1.1, load_ratio))
        flow = specs.rated_flow * load_ratio
        speed = specs.rated_speed * load_ratio

        # --- 物理模型计算理论值 ---
        theo_vib = physics.get_theoretical_vibration(flow, speed)
        theo_eff = physics.get_efficiency(flow)
        theo_temp = physics.get_theoretical_temperature_rise(flow, ambient_temp=25.0)
        theo_cur = physics.get_theoretical_current(flow, speed)
        theo_head = physics.get_head(flow)

        # --- 退化增量 ---
        deg_vib = degradation.get_vibration_offset(day)
        deg_eff = degradation.get_efficiency_decay(day)
        deg_temp = degradation.get_temperature_offset(day)

        # --- 故障注入 ---
        fault_vib_sig = injector.get_vibration_fault_signature(day, {})
        fault_temp = injector.get_temperature_fault_offset(day)
        fault_press = injector.get_pressure_fault_offset(day)
        fault_thd = injector.get_current_thd_offset(day)

        # --- 传感器仿真 ---
        vib = self.vib_sensor.simulate(theo_vib, deg_vib, fault_vib_sig, speed)
        cur = self.cur_sensor.simulate(theo_cur, fault_thd, fault_vib_sig, speed, specs.num_poles)
        thm = self.thm_sensor.simulate(theo_temp, deg_temp, fault_temp, ambient_temp=25.0)

        # --- HI 计算 ---
        eff_decay = deg_eff  # 效率绝对衰减量
        vib_deviation = vib.rms_overall - theo_vib
        temp_offset = thm.bearing_temp - 25.0 - theo_temp
        hi = degradation.get_health_index(
            vibration_deviation=max(0, vib_deviation),
            efficiency_decay=max(0, eff_decay),
            temperature_offset=max(0, temp_offset),
            running_days=day,
        )

        # --- 出口压力 ---
        pressure_out = theo_head * 0.0981 - fault_press  # m 扬程 → bar (approx)

        return {
            "timestamp": (pump["start_date"] + timedelta(days=day)).isoformat(),
            "device_id": specs.pump_id,
            "device_type": "smart",  # 仿真默认视为 smart 类型
            "pump_type": specs.pump_type,
            "health_index": round(hi, 1),
            "vibration": {
                "rms_x": vib.rms_x,
                "rms_y": vib.rms_y,
                "rms_z": vib.rms_z,
                "rms_overall": vib.rms_overall,
                "crest_factor": vib.crest_factor,
                "peak_frequencies": vib.peak_frequencies,
            },
            "current": {
                "rms": cur.rms,
                "thd": cur.thd,
                "frequency": cur.frequency,
                "sideband_amplitudes": cur.sideband_amplitudes,
            },
            "thermal": {
                "bearing_temp": thm.bearing_temp,
                "winding_temp": thm.winding_temp,
                "ambient_temp": thm.ambient_temp,
            },
            "pressure": {
                "outlet_bar": round(pressure_out, 2),
            },
            "flow_rate": round(flow, 1),
            "rotation_speed": round(speed, 1),
            "location": pump["location"],
        }

    def run(self, output_dir: Optional[str] = None, use_mqtt: bool = False,
            progress_callback=None):
        """运行仿真"""
        if output_dir is None:
            output_dir = self.config.get("output", {}).get("directory", "./output")
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, "simulation_data.jsonl")
        total_samples = 0

        # 采样时间点
        samples_per_day = 86400 // self.sample_interval
        total_timesteps = self.duration_days * samples_per_day

        print(f"[Engine] 开始仿真: {self.duration_days} 天 × {samples_per_day} 样本/天 = {total_timesteps} 时间步")

        with open(output_file, "w", encoding="utf-8") as f:
            for day in np.linspace(0, self.duration_days, total_timesteps):
                day = round(day, 4)
                for pump in self.pumps:
                    sample = self.simulate_one_sample(pump, day)
                    f.write(json.dumps(sample, ensure_ascii=False) + "\n")
                    total_samples += 1

                    # MQTT 推送
                    if use_mqtt and self.mqtt_client:
                        topic = f"{self.mqtt_topic_prefix}/{pump['specs'].pump_id}/sensor"
                        self.mqtt_client.publish(topic, json.dumps(sample, ensure_ascii=False))

                # 进度
                if progress_callback:
                    progress_callback(day, self.duration_days)

        print(f"[Engine] 仿真完成: {total_samples} 条数据 → {output_file}")

        # 生成统计摘要
        self._write_summary(output_dir, total_samples)

    def _write_summary(self, output_dir: str, total_samples: int):
        """生成仿真数据统计摘要"""
        fault_pumps = [p for p in self.pumps if p["injector"].faults]
        summary = {
            "total_pumps": len(self.pumps),
            "fault_pumps": len(fault_pumps),
            "total_samples": total_samples,
            "duration_days": self.duration_days,
            "sample_interval_sec": self.sample_interval,
            "fault_details": [
                {
                    "pump_id": p["specs"].pump_id,
                    "pump_type": p["specs"].pump_type,
                    "faults": [
                        {"type": f.fault_type, "onset_day": f.onset_day, "severity": round(f.severity, 2)}
                        for f in p["injector"].faults
                    ]
                }
                for p in fault_pumps[:20]  # 只输出前 20 台
            ]
        }
        summary_path = os.path.join(output_dir, "simulation_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"[Engine] 摘要已保存 → {summary_path}")


@click.command()
@click.option("--config", default="config.yaml", help="配置文件路径")
@click.option("--output", default=None, help="输出目录")
@click.option("--mqtt/--no-mqtt", default=False, help="启用 MQTT 实时推送")
def main(config: str, output: str, mqtt: bool):
    """PumpGuard 仿真数据引擎"""
    engine = SimulationEngine(config_path=config)
    engine.run(output_dir=output, use_mqtt=mqtt)


if __name__ == "__main__":
    main()
