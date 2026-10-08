# -*- coding: utf-8 -*-
"""低频小信号等效模型（Low-frequency small-signal model）
共源放大电路：直流电源 VDD 置零（交流接地），Cb1 保留，
场效应管用 g-m 模型（压控电流源 gm*vgs 与输出电阻 rds 并联）。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow, Circle

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

LW, LW2 = 2.0, 1.7
FS, FSN = 15, 17

fig, ax = plt.subplots(figsize=(13.2, 8.9))
fig.subplots_adjust(left=0.012, right=0.988, top=0.895, bottom=0.125)
ax.set_xlim(6.20, 22.35)
ax.set_ylim(0.20, 10.55)
ax.set_aspect("equal")
ax.axis("off")

wire = dict(color="black", lw=LW, solid_capstyle="round", zorder=2)
dev = dict(color="black", lw=LW2, solid_capstyle="round", zorder=3)


def line(x1, y1, x2, y2, **kw):
    ax.plot([x1, x2], [y1, y2], **{**wire, **kw})


def dot(x, y, r=0.075):
    ax.add_patch(Circle((x, y), r, color="black", zorder=6))


def res_v(cx, y1, y2, cw=0.72, ch=1.55):
    cy = (y1 + y2) / 2.0
    ax.add_patch(Rectangle((cx - cw / 2, cy - ch / 2), cw, ch,
                           facecolor="white", edgecolor="black", lw=LW2,
                           zorder=4))
    line(cx, y1, cx, cy + ch / 2, lw=LW)
    line(cx, y2, cx, cy - ch / 2, lw=LW)


def res_h(cy, x1, x2, cw=1.55, ch=0.72):
    cx = (x1 + x2) / 2.0
    ax.add_patch(Rectangle((cx - cw / 2, cy - ch / 2), cw, ch,
                           facecolor="white", edgecolor="black", lw=LW2,
                           zorder=4))
    line(x1, cy, cx - cw / 2, cy, lw=LW)
    line(x2, cy, cx + cw / 2, cy, lw=LW)


def ground(x, y):
    for i, w in enumerate((0.92, 0.60, 0.28)):
        line(x - w, y - i * 0.24, x + w, y - i * 0.24, lw=LW2, zorder=4)


def terminal(x, y):
    ax.plot([x], [y], marker="o", ms=9, mfc="white", mec="black",
            mew=LW2, zorder=5, clip_on=False)


def vsource(cx, cy, r=0.42):
    """电压源圆圈（箭头向上：+ 端在上）"""
    ax.add_patch(Circle((cx, cy), r, facecolor="white", edgecolor="black",
                        lw=LW2, zorder=4))
    line(cx, cy - r, cx, cy + r, lw=LW2, zorder=5)
    ax.add_patch(FancyArrow(cx, cy - 0.17, 0, 0.26, width=0.02,
                            head_width=0.15, head_length=0.15,
                            color="black", zorder=6,
                            length_includes_head=True))


# ======================================================== 坐标
Y_RAIL = 9.15          # 交流地（V_DD 置零）
Y_GND = 1.20           # 参考地
Y_DRAIN = 8.00         # 漏极公共线
Y_GATE = 5.60
Y_SRC = 3.60
X_IN = 9.50            # 输入端口
X_RAIL_L = 10.60       # 交流地左端（Rg1 处）
X_GATE = 14.80         # 栅极节点
X_RG2 = 16.20          # Rg2 支路
X_GM = 17.50           # gm*vgs 支路
X_GM2 = 17.80          # 漏极节点
X_RDS = 18.90          # rds 支路
X_RD = 19.60           # Rd 支路
X_VO = 21.20           # 输出端口

# ======================================================== 交流地与参考地
line(X_RAIL_L, Y_RAIL, X_RD, Y_RAIL)
ground(X_RAIL_L - 0.80, Y_RAIL - 0.20)
line(X_GM, Y_GND, X_RD, Y_GND)
ground(X_GM, Y_GND - 0.14)
ax.text(11.30, 9.92, "交流地（直流电源 $V_{DD}$ 置零）", fontsize=FS + 1,
        ha="left", va="center")

# ======================================================== 输入回路
line(11.80, Y_GATE, X_GATE, Y_GATE)              # 耦合电容 -> 栅极节点
line(11.52, Y_GATE - 0.60, 11.52, Y_GATE + 0.60, lw=LW2 + 0.8, zorder=4)
line(11.80, Y_GATE - 0.60, 11.80, Y_GATE + 0.60, lw=LW2 + 0.8, zorder=4)
line(X_IN, Y_GATE, 11.52, Y_GATE)
ax.text(11.14, Y_GATE + 1.02, r"$C_{b1}$", fontsize=FSN, ha="center", va="bottom")
terminal(X_IN, Y_GATE)
line(X_IN, Y_GATE, X_IN, 4.30)
line(X_IN, 4.30, 7.60, 4.30)
line(7.60, 4.30, 7.60, Y_GND)
line(7.60, Y_GND, X_GM, Y_GND)
ax.text(7.60, 4.22, r"$v_i$", fontsize=FSN, ha="center", va="top")
ax.text(X_IN - 0.62, Y_GATE + 0.32, r"$+$", fontsize=FSN, ha="center",
        va="center")
ax.text(X_IN - 0.62, Y_GATE - 0.34, r"$-$", fontsize=FSN, ha="center",
        va="center")

# ======================================================== 栅极偏置电阻
res_h(Y_RAIL, X_RAIL_L, 12.60)                   # Rg1：上端交流接地
line(12.60, Y_RAIL, 12.60, 7.00)                 # Rg1 支路
res_v(12.60, 7.00, 5.60)                         # Rg1：下端接栅极
line(X_GATE, Y_GATE, X_RG2, Y_GATE)              # 栅极节点 -> Rg2
line(X_RG2, Y_GATE, X_RG2, 4.30)
res_v(X_RG2, 4.30, 2.60)
line(X_RG2, 2.60, X_RG2, Y_GND)
dot(X_GATE, Y_GATE)
ax.text(11.95, 6.65, r"$R_{g1}$" "\n60 kΩ", fontsize=FSN,
        ha="right", va="center", linespacing=1.4)
ax.text(17.12, 3.45, r"$R_{g2}$" "\n40 kΩ", fontsize=FSN, ha="left",
        va="center", linespacing=1.4)
ax.text(X_GATE - 0.28, Y_GATE + 0.36, r"$g$", fontsize=FSN, ha="right",
        va="center")

# ======================================================== vgs 电压源
vsource(X_GATE, 4.60, 0.42)
line(X_GATE, Y_GATE, X_GATE, 5.02)
line(X_GATE, 4.18, X_GATE, Y_SRC)
dot(X_GATE, Y_SRC)
line(X_GATE, Y_SRC, X_GATE, Y_GND)
ax.text(14.10, 5.15, r"$+$", fontsize=FSN, ha="right", va="center")
ax.text(14.10, 4.05, r"$-$", fontsize=FSN, ha="right", va="center")
ax.text(14.06, 4.60, r"$v_{gs}$", fontsize=FSN, ha="right", va="center")
ax.text(X_GATE + 0.26, 3.22, r"$s$", fontsize=FSN, ha="left", va="center")

# ======================================================== 漏极公共线
line(X_GATE, Y_DRAIN, X_VO, Y_DRAIN)
dot(X_GM2, Y_DRAIN)
dot(X_RD, Y_DRAIN)
ax.text(X_GATE + 0.24, Y_DRAIN - 0.36, r"$d$", fontsize=FSN, ha="left",
        va="center")
terminal(X_VO, Y_DRAIN)
ax.text(X_VO, Y_DRAIN + 0.34, r"$v_o$", fontsize=FSN, ha="center", va="bottom")

# ======================================================== Rd
line(X_RD, Y_RAIL, X_RD, 8.95)
line(X_RD, 8.55, X_RD, Y_DRAIN)
ax.add_patch(Rectangle((X_RD - 0.36, 8.55), 0.72, 0.40, facecolor="white",
                       edgecolor="black", lw=LW2, zorder=4))
ax.text(19.08, 8.40, r"$R_d$" " 60 kΩ", fontsize=FSN - 2, ha="right",
        va="center")

# ======================================================== 受控电流源 gm*vgs
line(X_GM, Y_RAIL, X_GM, Y_DRAIN)                # 交流地 -> 漏极
line(X_GM, Y_DRAIN, X_GM, 7.00)
ax.add_patch(Circle((X_GM, 6.25), 0.75, facecolor="white",
                    edgecolor="black", lw=LW2, zorder=4))
line(X_GM, 6.25 - 0.75, X_GM, 6.25 + 0.75, lw=LW2, zorder=5)
ax.add_patch(FancyArrow(X_GM, 6.58, 0, -0.66, width=0.035, head_width=0.26,
                        head_length=0.26, color="black", zorder=6,
                        length_includes_head=True))
line(X_GM, 5.50, X_GM, Y_GND)
ax.text(16.42, 6.25, r"$g_m v_{gs}$", fontsize=FSN, ha="right", va="center")

# ======================================================== 输出电阻 rds
line(X_RDS, Y_DRAIN, X_RDS, 7.80)
res_v(X_RDS, 7.80, 6.25)
line(X_RDS, 6.25, X_RDS, Y_GND)
ax.text(17.72, 7.06, r"$r_{ds}$", fontsize=FSN, ha="left", va="center")

# ======================================================== 图题与说明
fig.suptitle("低频小信号等效模型（Low-frequency small-signal model）",
             fontsize=21, fontweight="bold", y=0.968)
fig.text(0.5, 0.048,
         r"$V_{DD}$ 置零（交流接地），$C_{b1}$ 保留；"
         r"场效应管用 $g_m$–$r_{ds}$ 模型（$g_m v_{gs}$ 与 $r_{ds}$ 并联）；"
         r"低频时忽略 $C_{gs}$、$C_{gd}$；"
         r"$R_i=R_{g1}\parallel R_{g2}$，$R_o=R_d\parallel r_{ds}$",
         fontsize=FS - 1, ha="center", va="center")

fig.savefig(r"D:\Learning\submit\ss_model.png", dpi=200, facecolor="white")
fig.savefig(r"D:\Learning\submit\ss_model.svg", facecolor="white")
print("saved")
