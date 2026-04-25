# 明日方舟：斗蛐蛐 计分板

由于《明日方舟》争锋频道：青草城不支持官服和B服联机，所以做了这么一个计分板。

具体使用推荐一人开屏幕共享，进入自娱自乐模式，然后持续观望。玩家则在网页计分板上选择。管理员在后台根据对局填写结果。

## 功能

- 10轮对局，每轮选择 LEFT / RIGHT / 观望
- 实时 WebSocket 同步，所有玩家状态一致，支持断线重连
- 20秒倒计时（可通过 `TIMER_DURATION` 环境变量配置），超时未选择自动观望
- 最后7秒隐藏其他玩家选择，倒计时变红跳动提醒
- ALL IN 机制：第6轮起可自愿 ALL IN，积分不足时强制 ALL IN
- 管理员控制面板：公布答案、回滚、催促
- Apple Design 风格，支持深色/浅色模式
- 移动端适配

## 规则

| 项目 | 说明 |
|------|------|
| 初始积分 | 10000 |
| 对局轮数 | 10轮 |
| 猜对 | +本轮积分 |
| 猜错 | -本轮积分 |
| 观望 | 不扣不增 |
| ALL IN 胜利 | 投入积分翻倍（净赚 = 当前全部积分） |
| ALL IN 失败 | 淘汰 |
| 第6轮起 | 可自愿 ALL IN（不论积分多少） |
| 积分不足 | 强制 ALL IN |
| 全员淘汰 | 游戏自动结束 |

## 项目结构

```
arknight-game/
├── main.py              # Python 后端 (FastAPI + WebSocket)
├── requirements.txt     # Python 依赖
├── frontend/            # Vue 3 前端源码
│   ├── src/
│   │   ├── App.vue              # 根组件
│   │   ├── main.js              # 入口
│   │   ├── styles/              # 全局样式（按功能拆分）
│   │   │   ├── variables.css    # CSS 变量 + 暗色主题
│   │   │   ├── base.css         # reset、布局、顶栏
│   │   │   ├── ui.css           # 按钮、卡片、徽章
│   │   │   ├── game.css         # 回合信息、排行榜、结果
│   │   │   └── animations.css   # @keyframes
│   │   ├── composables/
│   │   │   └── useWebSocket.js  # WebSocket 状态管理
│   │   └── components/
│   │       ├── JoinScreen.vue   # 加入页面
│   │       ├── AdminPanel.vue   # 管理员面板
│   │       ├── PlayerSection.vue # 玩家区域
│   │       └── TitlesScreen.vue # 结算页面
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
└── dist/                # 构建产物（需手动构建，不包含在仓库中）
```

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/Emma-Stardust/arknight-game.git
cd arknight-game
```

### 2. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 3. 构建前端

```bash
cd frontend
npm install
npm run build    # 构建到 ../dist/
cd ..
```

### 4. 启动服务

```bash
python main.py
```

默认监听 `0.0.0.0:8080`，浏览器打开 `http://localhost:8080` 即可。

如需修改端口：

```bash
python main.py --port 9000
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ADMIN_PASSWORD` | `Stardust` | 管理员密码 |
| `TIMER_DURATION` | `20` | 每轮倒计时（秒） |

## 使用方法

### 玩家

1. 打开网页，输入玩家 ID 和昵称
2. 如果有管理员密码，填入后自动解锁管理权限
3. 等待管理员开始游戏
4. 每轮选择 LEFT 或 RIGHT，也可以观望
5. 选择后点「确定！」锁定，锁定后无法更改
6. 倒计时20秒，超时未选择自动观望

### 管理员

1. 加入时填入管理员密码，或加入后点右上角齿轮解锁
2. 点击「开始新游戏！」
3. 等待玩家投票 → 选择正确答案 → 结算
4. 可以催促未确认的玩家（催一下 / 狠狠催）
5. 所有玩家确认后公布答案，也可以提前公布（未选择者按观望处理）
6. 答案选错可以「回滚！」回到投票阶段

### 内网穿透（可选）

如果需要让外网玩家访问，可以用 ngrok、frp 等工具将 8080 端口暴露出去。

## 技术栈

- **后端**：Python + FastAPI + WebSocket
- **前端**：Vue 3 + Vite（Composition API + SFC）
- **通信**：WebSocket 实时双向同步，版本号强一致性，断线自动重连
- **构建**：Vite 打包到 `dist/`，后端自动服务静态文件

## License

MIT
