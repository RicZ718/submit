# -*- coding: utf-8 -*-
"""直流通路（DC Path）——分压式共源放大电路
隔直电容 Cb1 直流开路；输入 vi / 输出 vo 端口不参与直流分析。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

LW, LW2 = 2.0, 1.7
FS, FSN = 15, 17

fig, ax = plt.subplots(figsize=(10.4, 9.6))
fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.13)
ax.set_xlim(3.85, 14.05)
ax.set_ylim(0.15, 9.05)
ax.set_aspect("equal")
ax.axis("off")

wire = dict(color="black", lw=LW, solid_capstyle="round", zorder=2)
dev = dict(color="black", lw=LW2, solid_capstyle="round", zorder=3)


def line(x1, y1, x2, y2, **kw):
    ax.plot([x1, x2], [y1, y2], **{**wire, **kw})


def dot(x, y, r=0.078):
    ax.add_patch(plt.Circle((x, y), r, color="black", zorder=6))


def res_v(cx, y1, y2, hw=0.30):
    ax.add_patch(Rectangle((cx - hw, min(y1, y2)), 2 * hw, abs(y2 - y1),
                           facecolor="white", edgecolor="black", lw=LW2,
                           zorder=4))


def ground(x, y):
    for i, w in enumerate((0.90, 0.58, 0.27)):
        line(x - w, y - i * 0.24, x + w, y - i * 0.24, lw=LW2, zorder=4)


def terminal(x, y):
    ax.plot([x], [y], marker="o", ms=9, mfc="white", mec="black",
            mew=LW2, zorder=5, clip_on=False)


# ======================================================== 坐标
Y_RAIL = 8.90
Y_GATE = 4.15          # 栅极引线
Y_GND = 0.80
X_DIV = 5.40           # 分压支路
X_D = 12.20            # 漏/源公共引出线
X_PL = 11.30           # 栅极极板
X_CH = 11.58           # 沟道竖线
X_ST = 12.00           # 沟道短横线右端
Y_DC, Y_GC, Y_SC = 4.55, 4.15, 3.75    # 漏/栅/源接触点

# ======================================================== VDD 电源轨
line(X_DIV, Y_RAIL, 12.85, Y_RAIL)
terminal(12.85, Y_RAIL)
ax.text(12.85, Y_RAIL + 0.28, r"$V_{\mathrm{DD}}$" "\n(5 V)", fontsize=FSN,
        ha="center", va="bottom", linespacing=1.35)

# ======================================================== Rg1 (60 kΩ)
line(X_DIV, Y_RAIL, X_DIV, 8.00)
res_v(X_DIV, 8.00, 6.30)
line(X_DIV, 6.30, X_DIV, Y_GATE)
ax.text(4.92, 7.45, "60 kΩ", fontsize=FSN, ha="right", va="center")
ax.text(4.92, 6.80, r"$R_{\mathrm{g1}}$", fontsize=FSN, ha="right", va="center")

# ======================================================== Rg2 (40 kΩ)
line(X_DIV, Y_GATE, X_DIV, 3.05)
res_v(X_DIV, 3.05, 1.25)
line(X_DIV, 1.25, X_DIV, Y_GND)
line(X_DIV, Y_GND, X_D, Y_GND)
ax.text(4.92, 2.45, "40 kΩ", fontsize=FSN, ha="right", va="center")
ax.text(4.92, 1.75, r"$R_{\mathrm{g2}}$", fontsize=FSN, ha="right", va="center")

dot(X_DIV, Y_GATE)
ax.text(5.72, Y_GATE + 0.40, r"$V_{\mathrm{G}}$", fontsize=FSN,
        ha="left", va="bottom")

# ======================================================== Rd
line(X_D, Y_RAIL, X_D, 7.90)
res_v(X_D, 7.90, 6.00)
line(X_D, 6.00, X_D, 5.40)
ax.text(12.68, 6.95, r"$R_{\mathrm{d}}$", fontsize=FSN, ha="left", va="center")

# 漏极节点 / 直流输出电位
dot(X_D, 5.40)
line(X_D, 5.40, 13.50, 5.40)
line(13.50, 5.40, 13.50, 5.75)
terminal(13.50, 5.75)
ax.text(13.50, 6.12, r"$V_{\mathrm{D}}$", fontsize=FSN, ha="center", va="bottom")

# 漏极电流 I_D
ax.add_patch(FancyArrow(X_D, 5.90, 0, -0.42, width=0.033, head_width=0.19,
                        head_length=0.23, color="black", zorder=5,
                        length_includes_head=True))
ax.text(12.62, 5.72, r"$I_{\mathrm{D}}$", fontsize=FSN, ha="left", va="center")

# ======================================================== MOSFET
ax.add_patch(Rectangle((X_PL - 0.075, 3.55), 0.15, 1.20, facecolor="black",
                       edgecolor="none", zorder=4))          # 栅极极板
line(X_PL, Y_GC, X_CH, Y_GC, **dev)                          # 栅极（极板→沟道）
for y in (Y_DC, Y_GC, Y_SC):                                 # 沟道竖线分三段
    ax.add_patch(Rectangle((X_CH, y - 0.06), 0.10, 0.12,
                           facecolor="black", edgecolor="none", zorder=4))
for y in (Y_DC, Y_SC):                                       # 漏/源短横线
    line(X_CH + 0.05, y, X_ST, y, **dev)
line(X_D, 5.40, X_D, Y_DC, **dev)                            # 漏极引线
line(X_D, Y_DC, X_ST, Y_DC, **dev)
line(X_DIV, Y_GATE, X_PL - 0.075, Y_GATE)                    # 栅极外部引线
line(X_ST, Y_SC, X_D, Y_SC, **dev)                           # 衬底与源相连
ax.add_patch(FancyArrow(X_ST - 0.12, Y_SC, -0.26, 0, width=0.03,
                        head_width=0.18, head_length=0.19, color="black",
                        zorder=5, length_includes_head=True))
dot(X_D, Y_SC)
line(X_D, Y_SC, X_D, Y_GND, **dev)                           # 源极引线

ax.text(X_PL - 0.58, Y_GC + 0.34, r"g", fontsize=FSN, ha="right", va="center")
ax.text(X_D + 0.20, Y_DC + 0.26, r"d", fontsize=FSN, ha="left", va="center")
ax.text(X_D + 0.20, Y_SC - 0.30, r"s", fontsize=FSN, ha="left", va="center")
ax.text(X_PL - 0.40, 3.34, r"T", fontsize=FSN, ha="center", va="top")

# ======================================================== 地
dot(X_D, Y_GND)
ground(X_D, Y_GND - 0.14)

# ======================================================== 偏置计算
ax.text(6.60, 2.55,
        r"$V_G=\dfrac{R_{g2}}{R_{g1}+R_{g2}}V_{DD}"
        r"=\dfrac{40}{100}\times5=2\ \mathrm{V}$",
        fontsize=FS + 2, ha="left", va="center")

# ======================================================== 图题与说明
fig.suptitle("直流通路（DC Path）", fontsize=22, fontweight="bold", y=0.975)
fig.text(0.5, 0.075,
         r"$C_{b1}$ 隔直：直流开路，输入回路断开；"
         r"输入 $v_i$、输出 $v_o$ 端口不参与直流分析；栅极电流 $I_G=0$",
         fontsize=FS, ha="center", va="center")

fig.savefig(r"D:\Learning\submit\dc_path.png", dpi=200, facecolor="white")
fig.savefig(r"D:\Learning\submit\dc_path.svg", facecolor="white")
print("saved")
