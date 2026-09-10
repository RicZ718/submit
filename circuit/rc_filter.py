# -*- coding: utf-8 -*-
"""
电路①  RC 低通滤波器 (RC low-pass filter)

元件参数 (self-defined):  R = 1 kΩ,  C = 100 nF
理论计算:
    tau = R*C = 1e3 * 100e-9 = 100 us = 0.1 ms
    fc  = 1 / (2*pi*tau) = 1.5915 kHz

仿真内容:
    - 画原理图 (schemdraw) -> figures/rc_schematic.png
    - 波特图 AC 分析 (10Hz~100kHz) -> figures/rc_bode.png
    - 方波瞬态 (PULSE) 输入/输出 -> figures/rc_transient.png
    - 阶跃响应测 tau (63.2% 点)
    - 打印 手算 vs 仿真 对比表
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm

import PySpice.Logging.Logging as L
L.setup_logging(logging_level='ERROR')
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

# ---------------- 元件参数 ----------------
R_val = 1 @ u_kΩ
C_val = 100 @ u_nF
R_ohms = 1e3
C_farad = 100e-9

# 理论值
tau_theory = R_ohms * C_farad            # 100e-6 s = 100 us
fc_theory = 1.0 / (2 * np.pi * tau_theory)  # 1591.5 Hz
print('【RC 低通滤波器】')
print('  R = 1 kOhm, C = 100 nF')
print('  手算 tau = R*C = %.2f us' % (tau_theory * 1e6))
print('  手算 fc  = 1/(2*pi*tau) = %.2f Hz' % fc_theory)

# ---------------- 画原理图 ----------------
d = schemdraw.Drawing(show=False)
d.config(unit=2, fontsize=11)
# 顶部水平支路
d += elm.SourceSin().label('Vi', loc='left').up().at((0, 0))
d += (elm.Resistor().label('R 1k', loc='top').right().at((0, 2)))
# R 右端与 C 顶端节点
d += (elm.Capacitor().label('C\n100nF', loc='bottom').down().at((2, 2)))
d += elm.Line().down().length(1.5)
d += elm.Ground()
# 底部地线
d += elm.Line().at((0, 0)).down().length(2)
d += elm.Ground()
# 输出端 (R-C 节点处)
d += elm.Dot().at((2, 2))
d += (elm.Line().right().length(1.2).at((2, 2)))
d += elm.Label().at((3.4, 2)).label('v_o')
d.save('figures/rc_schematic.png')
print('  已保存原理图: figures/rc_schematic.png')

# ---------------- 建电路 ----------------
circuit = Circuit('RC_lowpass')
# 用带 AC 激励的源做波特图 (AC 幅值默认为 1)
circuit.SinusoidalVoltageSource('in', 'vin', circuit.gnd,
                                amplitude=1, frequency=1 @ u_kHz, offset=0)
circuit.R(1, 'vin', 'out', R_val)
circuit.C(1, 'out', circuit.gnd, C_val)

# ---------------- AC 分析 (波特图) ----------------
simulator = circuit.simulator(temperature=25, nominal_temperature=25)
ac = simulator.ac(start_frequency=10 @ u_Hz, stop_frequency=100 @ u_kHz,
                  number_of_points=200, variation='dec')

freq = np.asarray(ac.frequency)
h = np.asarray(ac['out'])          # complex gain H
mag = np.abs(h)                    # |H|
phase = np.degrees(np.angle(h))    # deg
gain_db = 20 * np.log10(mag)

# 找 -3dB 点 (|H| 降到 0.707) -> 仿真 fc
H_target = 1 / np.sqrt(2)
idx = int(np.argmin(np.abs(mag - H_target)))
fc_sim = float(freq[idx])
print('  仿真测 fc (|H|=0.707 处) = %.2f Hz' % fc_sim)

# ---------------- 绘制波特图 ----------------
fig, ax1 = plt.subplots(figsize=(8, 5))
ax1.semilogx(freq, gain_db, 'b-', lw=1.8)
ax1.set_xlabel('Frequency (Hz)')
ax1.set_ylabel('Magnitude (dB)', color='b')
ax1.tick_params(axis='y', labelcolor='b')
ax1.grid(True, which='both', ls=':')
ax1.axhline(-3, color='r', ls='--', lw=1.2)
ax1.axvline(fc_sim, color='g', ls='--', lw=1.2)
ax1.text(fc_sim * 1.2, -3, '  fc_sim=%.0f Hz' % fc_sim, color='g')
ax2 = ax1.twinx()
ax2.semilogx(freq, phase, 'b--', lw=1.5)
ax2.set_ylabel('Phase (deg)', color='b')
ax2.tick_params(axis='y', labelcolor='b')
ax2.axhline(-45, color='m', ls=':', lw=1.2)
ax1.set_title('RC Low-pass Bode Plot')
fig.tight_layout()
fig.savefig('figures/rc_bode.png', dpi=130)
plt.close(fig)
print('  已保存波特图: figures/rc_bode.png')

# ---------------- 方波瞬态 ----------------
f_sq = 2 @ u_kHz
period_s = 1.0 / float(f_sq)          # 500 us
half_s = period_s / 2                 # 250 us
circuit2 = Circuit('RC_lowpass_sq')
# PULSE source: 0 -> 5 V
circuit2.PulseVoltageSource('in', 'vin', circuit2.gnd,
                            initial_value=0 @ u_V, pulsed_value=5 @ u_V,
                            delay_time=0 @ u_s, rise_time=1 @ u_us,
                            fall_time=1 @ u_us, pulse_width=half_s @ u_s,
                            period=period_s @ u_s)
circuit2.R(1, 'vin', 'out', R_val)
circuit2.C(1, 'out', circuit2.gnd, C_val)
sim2 = circuit2.simulator(temperature=25, nominal_temperature=25)
tran = sim2.transient(step_time=5 @ u_us, end_time=4 * period_s @ u_s)

t = np.array(tran.time) * 1e3          # ms
vin = np.array(tran['vin'])
vout = np.array(tran['out'])

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(t, vin, 'b-', lw=1.2, label='Vin (square)')
ax.plot(t, vout, 'r-', lw=1.8, label='Vout')
ax.set_xlabel('Time (ms)')
ax.set_ylabel('Voltage (V)')
ax.set_title('RC Low-pass Transient (square wave, f=2 kHz)')
ax.grid(True, ls=':')
ax.legend()
fig.tight_layout()
fig.savefig('figures/rc_transient.png', dpi=130)
plt.close(fig)
print('  已保存方波瞬态图: figures/rc_transient.png')

# ---------------- 阶跃响应测 tau ----------------
# 用足够长的脉冲让电容接近充满, 测 63.2% 点
circuit3 = Circuit('RC_step')
circuit3.PulseVoltageSource('in', 'vin', circuit3.gnd,
                            initial_value=0 @ u_V, pulsed_value=5 @ u_V,
                            delay_time=0 @ u_s, rise_time=1 @ u_ns,
                            fall_time=1 @ u_ns, pulse_width=2 @ u_ms,
                            period=10 @ u_ms)
circuit3.R(1, 'vin', 'out', R_val)
circuit3.C(1, 'out', circuit3.gnd, C_val)
sim3 = circuit3.simulator(temperature=25, nominal_temperature=25)
step = sim3.transient(step_time=2 @ u_us, end_time=1.5 @ u_ms)
ts = np.array(step.time) * 1e6        # us
vs = np.array(step['out'])

Vfinal = 5.0
Vcrit = 0.632 * Vfinal                 # 63.2% of final
# 上升沿从 0 起, 找第一个越过 0.632*Vfinal 的时间
cross_idx = int(np.argmax(vs > Vcrit))
tau_sim = float(ts[cross_idx])
print('  仿真测 tau (63.2%% 点) = %.2f us' % tau_sim)

# ---------------- 对比表 ----------------
print('\n================ 手算 vs 仿真 对比 ================')
print('  tau (理论) = %.2f us | tau (仿真) = %.2f us | 偏差 %.2f%%'
      % (tau_theory * 1e6, tau_sim, abs(tau_sim - tau_theory * 1e6) / (tau_theory * 1e6) * 100))
print('  fc (理论) = %.2f Hz | fc (仿真) = %.2f Hz | 偏差 %.2f%%'
      % (fc_theory, fc_sim, abs(fc_sim - fc_theory) / fc_theory * 100))

# ---------------- 结果写入 UTF-8 txt ----------------
with open('figures/rc_results.txt', 'w', encoding='utf-8') as fh:
    fh.write('RC 低通滤波器 结果\n')
    fh.write('R=1kOhm  C=100nF\n')
    fh.write('tau_theory_us=%.2f\n' % (tau_theory * 1e6))
    fh.write('tau_sim_us=%.2f\n' % tau_sim)
    fh.write('fc_theory_hz=%.2f\n' % fc_theory)
    fh.write('fc_sim_hz=%.2f\n' % fc_sim)
print('  已写入结果文件: figures/rc_results.txt')
