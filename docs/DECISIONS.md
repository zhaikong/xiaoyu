# 小遇实施决策

2026-11-09，用户确认：

- 产品名称为“小遇”，英文名暂用 Xiaoyu。
- 按 PRD 先跑通流程；有 Vidu API Key，运行时在 App 输入。
- cyber-xiaoya-live 仅作参考，不复用源码或素材。
- 官方形象指 Vidu 平台提供的官方形象，需要在 App 中选择；同时支持用户自建形象。

## 技术文档对照

收到的技术文档与旧项目 docs/TECHNICAL_ARCHITECTURE.md V1.2 内容一致。主技术栈与 PRD 一致。当前仓库副本已更正根目录工程、人设原文优先、M0 提前实现取消/结束核对与本地链接。

官方形象目录使用用户提供的 `https://service.vidu.cn/live/v1/keeper/avatar/roles`，通过 avatar_types=system 选择官方角色。2026-11-09 已验证匿名读取成功，当前返回 15 个角色，不使用用户浏览器 Cookie。此接口属于官网接口，独立封装以应对变更；官网角色 ID 不作为公开 API avatar ID，选中后下载图片并创建用户账号的 API 资产，尚待真实 Key 验证。

M0 必验：Agora 账号通道、无用户摄像头媒体链路、WS 协议 Ping/Pong 是否满足 15 秒活性要求、转写结构、准备期挂断、强杀回收与账单。收费会话只能由用户点击开始创建。

## 2026-11-09：改用 Agora 与 SPM

用户要求在火山不能直接使用 SPM 时采用声网。火山 Flutter 3.60.9 发布包只有 podspec，没有 Package.swift；Agora Flutter 6.6.4 发布包同时提供 SPM manifest，原生 SDK 固定 4.6.4，iris_method_channel 2.2.7 也支持 SPM。

已将会话创建改为 rtc.provider=agora，使用 joinChannelWithUserAccount 原样传递 Vidu 的字符串 user_id，麦克风上行开启、本地摄像头关闭。已移除火山 Flutter/原生依赖、专用 Maven 源、Jetifier 与 iOS Pods 集成，保留 pubspec.lock 和 SPM Package.resolved。

官方证据：
- Agora 发布包：pub.dev/packages/agora_rtc_engine/versions/6.6.4
- Flutter SPM manifest：github.com/AgoraIO-Extensions/Agora-Flutter-SDK/blob/main/ios/agora_rtc_engine/Package.swift
- 原生 SPM manifest：github.com/AgoraIO/AgoraRtcEngine_iOS/blob/main/Package.swift
- Vidu RTC 参数与凭证映射：platform.vidu.cn/vidu-stream/doc/s2-avatar/realtime/parameters

账号是否开通 Agora 以及真实音视频/计费仍以 App 内验证为准；503 时不自动重试创建或切到其他通道。

真机发现 permission_handler_apple 的 SPM manifest 将 PERMISSION_MICROPHONE 解析为 0，导致直接返回 denied 而不弹授权。首次媒体验证临时通过 AVFoundation MethodChannel 完成；随后删除该桥接，双端统一使用 permission_handler，曾通过项目内 Apple 插件副本规避配置发现问题。

## 2026-11-10：恢复 pub 官方权限依赖

重新核对 permission_handler 官方 SPM 文档：单一环境应用通过 Info.plist 声明权限即可，Xcode 直接启动的构建可显式配置 PERMISSION_HANDLER_INFO_PLIST，配置或环境变化后须刷新 SPM 缓存。无需复制 Apple 插件。已删除 third_party 副本与 dependency_overrides，恢复 pub 官方依赖；Dart 的 request 调用无需修改。不自动设置全局 launchctl 变量，不修改 pub 缓存，不引入 CocoaPods。操作说明见 [iOS 权限配置](IOS_PERMISSIONS.md)。

## 2026-11-10：本地 Harness 与界面边界

- 开发依赖 analyzer/args/crypto/yaml 分别提供 Dart AST、参数解析、摘要和配置解析；integration_test 使用 Flutter SDK 官方组件。无新增运行时依赖、RTC 切换、权限桥接或本地插件。官方来源：https://pub.dev/packages/analyzer 、https://dart.dev/tools 、https://docs.flutter.dev/testing/integration-tests 。复用现有包，未引入新的测试执行框架。
- LiveApi 移至 domain/call_ports；页面通过 Riverpod presentation 控制器操作仓储、凭证和通话。可注入 HTTP、Socket、RTC 只用于离线验证；生产默认实现不变。
- 有效行覆盖率排除 AST 确认的 `extends Table` 声明式 schema 行：Drift 生成器编译这些声明，运行时使用生成的列；仍统计同文件 AppDatabase 的迁移和运行逻辑。真实 SQLite 创建、约束、重开与持久化由行为测试验证，不调用 schema DSL getter 刷覆盖率。原生权限桥接依赖设备验证，不能以宿主单测冒充。
- 黄金图使用固定离线夹具，系统字体由宿主加载；不使用设计稿示例头像、历史、对话作为用户数据。首轮黄金图只防回退，视觉符合度仍待审查。

- 静态分析增加 unawaited_futures 与 avoid_void_async，导航异步返回显式处理；不增加 ignore。首次黄金基线为双平台 16 张，后续仅专用更新命令可更新。配置及依赖变更必须同时更新本决策文件；机器仅检查记录存在，真实性仍由评审核对。
- iOS 无线设备测试使用 Flutter 官方 `integration_test_driver` + `flutter drive --publish-port --no-uninstall-first`。当前 SDK 的 `flutter test` 不接受 publish-port，且默认可能卸载测试应用，故 Android 测试显式 no-uninstall；无需修改 SDK 或插件。官方参考：https://docs.flutter.dev/testing/integration-tests 、Flutter SDK packages/flutter_tools/lib/src/test/integration_test_device.dart。

- RTC 原生释放抛错后仍执行平台结束/账单核对，但当前协调器阻止再次创建通话，避免释放状态未知时建立另一个原生引擎；需重新启动进程恢复。已补行为断言。

## 2026-11-10：将 Skill 提示改为可检查的动态加载流程

原实现仅检查四个固定 Skill 文件存在，无法发现任务只读 xiaoyu-harness。改为从用户安装的 `.agents/skills/*/SKILL.md` 发现真实元数据，按任务种类、改动路径及显式主题/名称选择，skills --load 读取并输出原文，check 核对任务与文件摘要。全部现有专项技能可通过主题或名称选择；新安装技能自动进入目录，默认路由配置需显式维护。不新增包、不复制或替换用户的专项技能。相比仅在文档中列名，此方案可阻断缺失/过期的文件加载；相比自动执行 AI runner，保持现有本地 Harness 边界。CLI 文件读取不能证明模型遵循，skillApplication 不标记通过，自述不能充当 MCP 证据。新增必测 skills_test.dart 验证这些失败情形，不放宽原有检查。

## 2026-11-10：官方 Liquid Glass Widgets 统一 UI

用户明确指定所有可见控件使用 liquid_glass_widgets。固定官方 1.17.1 与 cupertino_icons（包内密码和导航图标字体所需），不引入其他玻璃库、不复制包源码。官方来源：https://pub.dev/packages/liquid_glass_widgets/versions/1.17.1 、发布包 README、ios/liquid_glass_widgets/Package.swift；Flutter >=3.41、Dart >=3.5、iOS15，与当前工具链及 SPM 相容。启动预热官方 shader，保留 MaterialApp.router 并仅提供透明 Material 基础设施。HTML 为外观基准，额外已有角色功能移至高级设置。实色内容也使用该库的 solid 表面；Premium 用于悬浮控件，测试固定 Standard，不能冒充设备 Premium 效果。相比继续自写 BackdropFilter，此次采用官方公开渲染层和组件；不新建原生桥接。iOS Agora 使用 SDK 已有 FlutterTexture（官方包 src/render/video_view_controller.dart）；Android 保留 TextureView 并使用玻璃库公开 platformViewBackdrop 路径，实际动态画面合成仍须设备验证。

## 2026-11-10 — 本轮仅验收手机竖屏

根据用户“去除大屏和旋转屏的兼容，先把 iOS 和 Android 做好”的最新指示，本轮适配矩阵收敛为 320×568、360×800、402×874 的手机竖屏。保留中文/英文、Android/iOS、1×/2×字体以及键盘操作可达性。移除 430×932 和横屏专项矩阵，不新增方向锁，不将未覆盖的大屏或横屏称为通过。此调整由用户授权，未降低业务覆盖率门槛。

高级设置弹层在页面退出动画期间可能继续重建，因此控制器在打开前捕获；弹层布局使用其自身的 BuildContext，避免读取已停用的编辑页祖先。FlutterError 不再被业务提示吞掉，测试和 MCP 能发现真正的 UI 编程错误。

## 2026-11-11：局部玻璃迁移到 liquid_glass_easy

用户明确授权使用 easy 官方公开 API 重构，不保留旧封装兼容，缺少组件使用 Flutter 自带组件。此决定取代此前全部使用 liquid_glass_widgets 的要求。固定官方 liquid_glass_easy 5.2.0；它只有 Flutter/meta 依赖，没有原生插件，不增加 Pods/SPM 项目或自定义桥接。cupertino_icons 继续用于系统风格图标。

已通过 Dart MCP 核对发布包公开导出、README、按钮、开关、AppBar、TabBar、Dialog 和 Sheet 的实现。来源：https://pub.dev/packages/liquid_glass_easy/versions/5.2.0 、https://pub.dev/packages/liquid_glass_easy/example 、https://github.com/AhmeedGamil/liquid_glass_easy 。采用 ensureLoaded 预热与独立镜片，不启用全屏 capture/View 或复杂 Morph/Blender。替代方案为继续旧库局部使用，但用户已明确选择迁移。

固定导航、玻璃按钮、开关和短确认采用 easy；卡片、表单、列表、大面板及菜单用 Flutter。AppButton 主提交实色、次操作可玻璃；无旧 Quality/主题/平台背景兼容分支。AST 门禁改为阻止旧依赖、私有 API 和自写玻璃渲染，不再禁止普通 Material/Cupertino 控件；覆盖率和其余质量门槛保持不变。增加对应门禁反例，非自动豁免。

宿主截图使用 Skia Lite，Impeller 设备使用实时背景路径；Android 视频按钮 Lite，不能据此宣称真实视频折射兼容。测试与模拟器只使用隔离数据，不创建收费 live。

## 2026-11-11：Scroll Edge 顶栏与系统返回手势

按用户要求，普通页面的胶囊 AppBar 改为 easy 5.2.0 公开的 `LiquidGlassScrollEdge`（top、soft、blur 6），内放 Flutter `NavigationToolbar` 标题、48 点返回按钮及操作按钮。背景渐淡，列表视口保持全屏，初始内容避开标题，滚动后进入模糊层；不自写 BackdropFilter、不新增依赖。首页/我的沿用全屏滚动与各自品牌/头像区，通话保留原视频及控制层。来源：https://pub.dev/documentation/liquid_glass_easy/latest/liquid_glass_easy/LiquidGlassScrollEdge-class.html 、官方 example/lib/scroll_edge_page.dart。相比预留顶栏高度，此方式让内容真正滚过顶栏背后。

项目已使用 go_router。18.1.3 的自动 app 检测引用 `material_ui.MaterialApp`，当前应用使用 Flutter SDK `MaterialApp`，自动回退到 NoTransitionPage，缺少 iOS 交互返回检测器。回归测试复现设置页边缘滑动无法 pop。各 GoRoute 显式使用 SDK `MaterialPage`，保留 pageKey/restorationId、系统平台过渡及 PopScope；不修改 pub 缓存、不增加全屏拖动监听。来源：go_router 发布包 lib/src/pages/material.dart、lib/src/builder.dart，Flutter SDK MaterialPage / CupertinoPageTransitionsBuilder 公开 API。

iOS 从左边缘右滑返回，短滑可取消；Android 使用系统返回。编辑页有未保存修改或任务进行中继续阻止直接离开，避免丢失内容；点击返回可确认保存草稿后退出。这是保留原有保护，不伪装成无条件返回。离线设备场景额外验证账号→设置→原 Tab 的返回链及 Scroll Edge 截图；不涉及收费通话。

## 2026-11-11：数字人菜单使用官方 Morph

按用户提供的官方 morph_page.dart 示例，将角色三点菜单从 PopupMenuButton 改为公开 `LiquidGlassMorph`：48 点按钮从原位置展开为仅有编辑、删除的玻璃面板，内容决定高度、右侧角锚定；接近底部向上展开，面板限制在安全区。Flutter 透明 Dialog 路由只负责覆盖卡片裁切、外部关闭及系统返回，不自己渲染玻璃。Reduce Motion 直接呈现最终形状，普通模式使用官方 plain 弹簧；不复制包实现、不加依赖、不引入全屏背景捕获。编辑继续现有路由，删除继续现有确认和控制器。此决定取代此前“菜单用 Flutter 普通弹出面板”的选择。来源：用户附件与官方 example/lib/morph_page.dart，以及 easy 5.2.0 的公开 LiquidGlassMorph / LiquidGlassMorphMotion API；经 Dart MCP 查阅发布包实现。

## 2026-11-11：精简首页入口和官方角色预填

按用户九项调整，新增角色统一放到品牌标题右侧，移除搜索、首张新增卡、推荐查看更多及卡片聊天/新增按钮。我的角色用懒加载横向列表，图片完整 contain 显示、文字移到下方；点击图片保留现有账号检查、收费确认和通话流程，菜单是独立命中区域。关闭时只有裸三点且保留 48 点触控区域，展开仍使用官方 Morph，仅编辑/红色删除文字。我的历史分割线移除，底部 Tab 去掉额外 24 点空白，保留系统安全区。

官方角色数据按当前公开目录实际响应核对（无 Cookie/Key）：https://service.vidu.cn/live/v1/keeper/avatar/roles?pager.page=0&pager.pagesz=1&avatar_types=system 。选用首个有 uri 的 profile_photos 项作为卡片和编辑图片，其 description 为卡片描述与预填简介。人设优先已有 system_prompt_override/system_prompt/persona；为空时按官方 description、attrs 中的性格、背景、身份、说话风格及 extra 行为准则/知识合并，不虚构人物资料。点击推荐创建本地 UUID 草稿，通过控制器保存并进入现有编辑页；不将网站角色 ID 当作 OpenAPI 图片资产 ID。官网 voice_library 的内部音色与当前 qwen_omni 公开音色不同，保留当前可用默认音色；图片上传、资产就绪校验沿用原流程。无依赖、数据库或原生接口变更。

替代方案为继续跳空白编辑页/使用官网原始 ID，但前者要求重复输入、后者混淆资源域，均不采用。用离线模板验证字段持久化、菜单与图片点击隔离、30 个角色横滑、图片 contain 与安全区；模拟通话不作为真实媒体证据。黄金图通过专用命令更新，人工视觉确认继续单列。

## 2026-11-11：图片叠层与紧凑菜单

按用户后续调整，取代上一版图下文字与实色底板：我的/推荐数字人统一使用 PortraitTile，按解码后的图片比例确定圆角图片边界，图片完整显示，名称/描述浮在图片底部，三点菜单在图片右上角独立响应。仅在图片内部叠渐变帮助文字阅读，无外围背景、边框或多余信息区。图片加载监听在更新/销毁时解绑；头像及图片卡复用来源选择和失败占位，删除不再需要的 Portrait.fit 参数及两套旧卡片样式。横向列表按图片实际宽度排布，保留懒加载。

Morph 菜单按当前语言、字体和字号测量最长文字，加少量内边距决定宽度；弹出方向按实际文本高度和可用安全区决定，移除固定 208 宽、176 高的估算。仍只提供编辑/红色删除，操作区域至少 48 点。不新增依赖或兼容分支。补充图片原始比例、圆角、叠层边界和中英文大字号菜单宽度回归；保留已有预填、删除确认和模拟通话测试。

## 2026-11-11：Tab 固定底部间距

按用户最终要求，Android/iOS 首页与我的 Tab 统一距屏幕底部 12 点，不依据系统底部安全区计算。删除安全区减值及平台分支，只保留固定内边距；顶部、左右及其他页面的安全区行为不变。采用真实布局，不用 Transform 位移，保证绘制、语义与触控区域一致。回归同时核对两平台 34 点安全区和零安全区，位置均为窗口高度减 12。

移动位置回归发现旧 Tab 语义覆盖层只有透传 Listener，点击可能误入下方推荐卡。改为同区域 GestureDetector 显式更新所选 Tab、阻断背景点击，保留唯一语义目标；验证切到“我的”后路由仍为首页且资料区实际可见。

经 Dart MCP 核对 easy 5.2.0 的公开 TabBar 文档及实现，独立 TabBar 会再消费 MediaQuery.padding.bottom，因此外层定位后对底部栏子树 removePadding(bottom)，避免安全区重复叠加造成胶囊裁切。此处仅调整布局环境，不修改包源码。

## 2026-11-11：恢复 Tab 组件原生拖动

用户反馈底部栏无法拖动切换，并要求删除自定义防点击穿透处理。核对官方 liquid_glass_easy 5.2.0 的 LiquidGlassTabBar 与 LiquidGlassAnimatedNavBar：Impeller 玻璃胶囊以内部 Listener 接收按下、移动、释放来完成拖动；项目此前覆盖其上的 opaque GestureDetector 只处理点击，导致库无法收到手势。本次移除该点击处理器，不增加防穿透层、不复制库的手势逻辑。无障碍层只保留语义操作与无回调的 translucent Listener，物理点击/拖动交由官方组件。底部固定 12 点及系统栏保持原样。

来源：https://pub.dev/packages/liquid_glass_easy ，通过 Dart MCP 读取官方包 liquid_glass_tab_bar.dart、liquid_glass_animated_nav_bar.dart 及 liquid_glass_nav_bar_icon_row.dart。库的宿主 Skia 降级版本只支持点击；拖动回归放在支持 Impeller 的离线设备测试，双向拖动后核对选中页、路由及零收费创建，不能用宿主 Widget 点击测试冒充拖动验证。

## 2026-11-11：取消按压覆盖及长按 Tooltip

用户要求所有按钮和数字人卡片不再出现淡白按压/长按覆盖，也不显示 Tooltip。核对 Flutter Material 和官方 liquid_glass_easy 的 LiquidGlassButton：玻璃按钮内部同样使用 InkWell，并非玻璃折射产生的白色遮罩。主题统一使用 NoSplash、透明 splash/highlight/hover 和按钮 overlayColor；现有带 foregroundColor 的 styleFrom 会自行生成覆盖色，因此四处本地按钮样式也显式使用透明 overlayColor，避免覆盖主题。保留玻璃材质、Tab 选中状态、禁用状态及既有手势。

应用 builder 使用 Flutter 官方 TooltipVisibility 关闭文字浮层；图标的用途改由 Icon.semanticLabel 表达，避免当前 SDK 隐藏 Tooltip 时同时移除其辅助语义。通话 PopupMenuButton 的 tooltip 设为空串，阻止默认提示回填。未增加手势拦截层，无依赖、原生或业务逻辑变更，保留用户设置的 Tab 底部 26 点。

来源：本机 Flutter 3.47.9 的 material/tooltip.dart、tooltip_visibility.dart、icon_button.dart、TextButton.styleFrom 与 FilledButton.styleFrom，以及通过 Dart MCP 读取的官方 liquid_glass_button.dart。补充文本/实色/玻璃/图标按钮、列表行及角色卡按下 100ms、持续 800ms 的像素一致性测试，并验证释放后回调、Tooltip 隐藏和读屏标签。

## 2026-11-11：精简历史记录列表

按用户最新要求重新设计“我的”历史记录及查看全部页面，取代 design.html 的大底板卡片。两处统一 16 点水平间距，删除历史行的实色卡片及内部额外水平内边距；行内保留 48 点头像、名称、时间、状态和进入详情箭头。时间与状态按可用宽度自然换行，名称最多两行，待核对/失败状态仍有文字提示。查看全部入口使用内容自适应的轻量文字按钮，不再固定 106 宽。

PageBody 增加 horizontal 参数，默认仍为 20，仅“我的”设为 16；全部记录使用 ListView.builder 懒加载，预览继续最多四条，详情页及删除/核对行为不变。没有添加分割线、额外业务入口或依赖。新增离线测试验证两处边距、预览数量、懒加载、详情导航和空态；增加双端完整历史列表黄金图，设计对照由独立命令生成，人工审查继续单列。

## 2026-11-11：恢复统一按压反馈，继续关闭 Tooltip

用户最新要求取代此前取消按压覆盖的决定。普通按钮、图标、列表和角色卡采用低透明度淡紫色；玻璃按钮采用更轻的淡白色；浅色主按钮使用深紫色以保持可见，危险操作使用淡红色。按下与持续长按共用同一覆盖色，释放后清除；继续使用 NoSplash，避免扩散水波纹。TooltipVisibility 保持关闭，保留图标语义标签，不新增长按动作。

复用 Flutter 官方主题及 ButtonStyle，玻璃按钮通过局部 Theme.highlightColor 配置官方 LiquidGlassButton 内部 InkWell，无复制包源码或增加手势拦截。来源：Flutter Material 主题/InkWell/ButtonStyle，以及 Dart MCP 核对的 liquid_glass_easy 5.2.0 liquid_glass_button.dart。没有新增依赖、原生或业务改动，保留 Tab 原生拖动及用户设置的底部 26 点。像素测试验证短按可见、长按一致、释放恢复与单次回调，另验证真实菜单长按不弹 Tooltip 且读屏标签保留。

## 2026-11-12：用户品牌启动图与应用图标

按用户指定的两张图片，第一张作为启动图，第二张生成 iOS 所有 AppIcon 尺寸、Android 密度图标及 adaptive icon。保留源图于 assets/branding，不使用 AI 重绘。图片边缘 #08090D 与应用底色一致，iOS storyboard 及 Flutter 使用 aspect fit/contain，避免不同比例手机裁切图片文字。移除 Flutter 默认透明占位启动图片与白色原生背景；不改变运行页面的系统栏配置。

启动时先显示 Flutter 品牌画面，再加载现有 shader 和本地 AppRuntime，成功后进入原应用并执行原有待核对通话恢复；不添加人工停留计时、不触发收费创建。失败仅显示本地化通用错误与显式重试，不打印底层错误。测试通过注入初始化 Future 验证等待、成功切换、只初始化一次及失败重试。未新增依赖、权限、Pods 或原生桥接；相比启动插件，直接使用现有 storyboard/Android 资源和 Flutter 图片即可满足。

官方来源：https://docs.flutter.dev/ui/assets/assets-and-images 、https://docs.flutter.dev/platform-integration/android/splash-screen 、https://developer.android.com/develop/ui/views/launch/splash-screen 、https://developer.apple.com/documentation/xcode/specifying-your-apps-launch-screen 。Android 12+ 系统启动页只允许背景与受遮罩的图标，不能放完整海报，因此原生阶段用新图标，Flutter 首屏显示完整海报。原图自带中文文案按用户要求保留，不将其拆为系统语言文字。

## 2026-11-12：放大品牌图标与启动画面

按用户后续要求，启动图从 contain/aspect fit 改为 cover/aspect fill，保持比例铺满手机屏幕，将底部文字落在屏幕下方，取代此前保留整张背景的决定。Flutter 底部居中，iOS 手机竖屏等高缩放、左右裁切，构图一致。使用实际海报文字边界验证三种手机尺寸，所有文字保留、底部距边约 16–32 点；无固定高度、字体缩放限制或方向锁。

图标改用用户新增的弧形边框参考图，裁去外圈 80 像素空白后生成 1024 正方形，主体线性放大约 19%，保留细边框与圆角周围背景，不把示例图外部空白一起缩小进桌面图标。iOS/Android 各尺寸同步生成；adaptive foreground 将图像置于 108dp 画布中央 72dp，避免边框被系统额外放大后裁掉，最终形状遵从启动器蒙版。Android 系统启动图标保留原安全区。没有新增依赖、桥接或业务代码；继续采用 Flutter Image.fit 与系统原生资源，来源沿用上一条官方文档。

## 2026-11-12：恢复最初构图，仅轻微放大

用户认为上一轮过大，明确要求恢复到它之前的版本再小幅放大。本轮移除新增的弧形边框，恢复最初 1_02PM 图片，裁中央 966×966 后生成各平台尺寸，主体仅比最初放大约 6%。Android adaptive 图层也恢复原始满幅图像结构，不保留边框版的额外内边距。

启动图恢复 contain/aspect fit 居中，Flutter 图片统一缩放 1.06 倍、在窗口内裁切少量左右背景；iOS 图片视图居中、宽高为窗口 1.06 倍，使用 aspect fit，实现相同构图。取消铺满与底部对齐；三种手机尺寸仍验证文字完整、缩放幅度及启动等待/切换/失败重试。没有新增依赖、方向锁、原生桥接或业务变更，替代上一轮约 19% 的图标放大和启动图 cover。

## 2026-11-12：替换为 2_25PM 启动图

按用户最新图片替换 Android/iOS 共用的 Flutter launch.jpg，并同步 iOS 原生 LaunchImage PNG，保持现有 1.06 倍 contain/aspect fit 居中比例及应用图标。新图不含底部平台说明及版权文字，布局测试的实测文字边界同步至 y=1080。Android 12+ 原生阶段继续使用系统规定的图标启动页，Flutter 初始化首屏显示新图。无依赖、业务、权限或平台桥接变更。

## 2026-11-12：提交时准备云端形象

用户发现推荐角色预填后仍不能提交。原因是官网目录仅生成本地草稿与图片地址，提交却直接复用实时通话的就绪校验，遗漏账号形象创建；实际创建入口藏在高级设置。改为提交先校验文本、凭证与账号归属，再复用现有图片下载和 OpenAPI /live/v1/avatars 创建接口。已有 ID 则查询处理状态，不重复创建，旧页面草稿再次提交时优先恢复仓储已持久化的 ID。处理中保留编辑页和草稿，提示稍后再次提交检查；就绪后返回首页，失败提示重新创建或换图。高级设置仍可显式重新创建失败形象。所有自动测试使用内存 HTTP 适配器与假凭证，不创建收费 live。

抽取领域文本校验与形象就绪校验，移除控制器已无调用者的 validate 保存参数；保持目录角色 ID 与账号资产 ID 分离。没有新增依赖、原生桥接或数据库结构。官方依据为现有 Vidu 图片资产接口及 https://platform.vidu.cn/vidu-stream/doc/s2-avatar/realtime/quick-start ，不使用浏览器 Cookie 或官网角色 ID 发起 OpenAPI 通话。

用户已将本机 Flutter 升级到 3.50.0 / Dart 3.14.0，本轮同步 harness 的实际 SDK 版本。flutter pub get 自动更新 SDK 固定的 meta 1.19.0、test_api 0.7.14，保留其他依赖版本，不新增覆盖或降低门槛；新 SDK 的黄金图差异单独验证。

新版 Gradle 会在 android/build/reports 生成问题报告，补充忽略该构建目录，避免将生成报告纳入源码指纹。当前 SDK 对旧 Material/Cupertino 导入的弃用诊断，以及 Android 所需 AGP 最低版本 9.1.1，保留为独立未通过项；本次不跨范围迁移 UI 框架或升级 Android 工具链。


## 2026-11-12 通话界面精简及本地播放静音

- 按用户截图和 design.html：高级设置、声音选择等底部面板移除标题右侧 X，保留系统返回、遮罩与拖拽关闭；通话前确认只移除 Vidu 品牌字样，保留费用、10 分钟上限与权限说明。
- 通话顶部使用 easy 公开 LiquidGlassLens，把名称、状态、时长合成一枚玻璃胶囊；删除通话更多菜单（打断、换音色、全文弹窗）及音源选择面板。编辑角色的声音选择、通话内字幕和历史正文仍有入口。
- 声音按钮通过领域端口 RtcSession.mutePlayback、CallCoordinator.togglePlayback 调用 Agora 官方 adjustPlaybackSignalVolume(0/100)，只改变本地远端混音播放。SDK 来源：[Agora Flutter API](https://api-ref.agora.io/en/video-sdk/flutter/6.x/API/class_irtcengine.html#api_irtcengine_adjustplaybacksignalvolume) 及当前官方包 agora_rtc_engine.dart 的方法说明。替代方案取消订阅会影响 audioReady，切换扬声器/听筒不等于静音，因此均不采用。麦克风状态独立，失败不更新状态，重复点击与取消后晚到结果有保护。
- 连接页以 CustomPainter 的 repaint 动画驱动粒子亮度和轻微呼吸，不重建视频或头像；减少动态效果/TickerMode 关闭时停止。取消按钮为白色 56pt 圆形、红 X 与下方说明。
- 布局矩阵用 call_muted 状态替换已删除的 route 面板，仍验证相同数量页面组合及操作可达性；黄金图由 harness golden-update 更新并检查对照。


## 2026-11-12 通话字幕与输入区毛玻璃补充

按用户新截图，顶部只保留名称与时间，移除状态文案与圆点。字幕和输入区采用 easy 公开 LiquidGlassLite（blur 10、25% 深色半透明底、边缘高光），输入框取消默认 filled 实色，保留 Flutter TextField 的输入、焦点、键盘和大字号换行。高对比度使用更深的半透明底保证可读性。范围只限这两个通话覆盖层，其他表单/卡片仍沿用现有组件决策。
来源：当前 liquid_glass_easy 官方包 LiquidGlassLite API 文档及实现；它提供背景模糊、着色与高光，无额外折射 shader，适合字幕等文字覆盖层。替代方案是每块使用完整折射 Lens；此处优先与按钮一致的毛玻璃观感和文字可读性，避免为两块文字面板增加折射成本。

## 2026-11-12：通话期间阻止自动熄屏

用户反馈无触摸后到达系统自动锁屏时间会中断通话。代码未持有屏幕唤醒状态；自动锁屏触发 AppLifecycleState.paused，现有 app_background 路径随即结束会话。使用官方 wakelock_plus 1.8.2，仅在前台创建、初始化、加入和连接阶段保持屏幕亮起；结束中、失败、待核对、后台及组件释放恢复系统休眠。临时 inactive（权限或系统覆盖）不结束通话，resumed 重新声明所需状态。串行执行原生操作，防止晚到 enable 覆盖挂断后的 disable；插件错误上报运行时诊断，后续状态变化可重试，不冒充开启成功。

官方依据：https://pub.dev/packages/wakelock_plus ，通过 Dart MCP 核对公开 toggle/enabled API、iOS SPM Package.swift（最低 iOS 13）、Android FLAG_KEEP_SCREEN_ON 及 iOS idleTimerDisabled 实现。该包无需额外权限；pub 正常解析新增其声明的七项依赖，保留既有版本。替代方案是自写 iOS/Android 原生桥接，或放开后台通话；前者重复官方能力，后者改变用户主动锁屏/后台结束及计费策略，均不采用。未增加 Pods、后台音频模式、前台服务或收费会话自动重试。

回归覆盖各通话阶段、无交互、系统覆盖/恢复、后台结束、原生失败重试及晚到操作释放；设备离线集成读取真实原生屏幕标志，验证连接与通话开启、挂断/后台关闭，并将两项证据纳入 Harness 必验。宿主推进时间不能模拟系统锁屏，真实手机超过自动锁屏时长的验收仍需单列，不以模拟媒体测试冒充真实 RTC。

为使 Android 能构建本次修复，将 AGP 从 9.1.0 升至最低要求的补丁版本 9.1.1。依据为本机 Flutter 3.50 官方 DependencyVersionChecker（errorAGPVersion=9.1.1、errorGradleVersion=9.3.1）及 Google Maven 的 9.1.1 发布 POM；保留当前 Gradle 9.3.1 和 Kotlin 配置，不使用跳过依赖校验开关。iOS 首次 SPM 更新遇到远端网络失败，使用 xcodebuild -skipPackageUpdates -onlyUsePackageVersionsFromResolvedFile 从缓存解析后构建成功，锁定的 Agora 版本未变。

## 2026-11-13：迁移 Flutter 3.50 弃用 API

用户要求提交前先修复严格分析中的弃用诊断。依据官方 [material_ui 迁移说明](https://pub.dev/packages/material_ui)、[cupertino_ui 迁移说明](https://pub.dev/packages/cupertino_ui)，以及 Dart MCP 读取的已安装包 README 和公开 API，执行 `dart fix --apply --code=migrate_design_widgets`，将应用、测试及离线设备测试导入迁移至独立的官方设计库。两个包原已由依赖图引入；现在显式声明 `material_ui: ^1.10.0` 和 `cupertino_ui: ^1.1.6`，保留锁文件中的现有版本。连接动画改读 Flutter 官方 `TickerMode.valuesOf(context).enabled`，继续尊重祖先动画开关与系统减少动态效果设置。

本机 Flutter 3.50 的 `gen_l10n_templates.dart` 仍固定生成旧版 Material/Cupertino 本地化委托。通过官方 `l10n.yaml` 的 `header-file` 配置，使用两个导入前缀解析生成器原有的委托名称，分别指向官方设计库的公开委托；生成头文件中的库文档同时让语言子文件保留有效引用。`flutter gen-l10n`、`flutter pub get` 和自动构建仍走标准生成流程，不手改生成文件、修改 SDK、添加依赖覆盖或忽略弃用诊断。重新生成后严格分析通过。替代方案包括手改生成结果、维护 SDK 模板副本或关闭弃用门禁，均不采用。后续官方生成器迁移完成后可移除这一生成配置及两个委托转接文件。

官方 `liquid_glass_easy` 当前最新版本仍为 5.2.0，按钮和对话框辅助函数内部引用旧版 Material。实际回归发现其按钮读不到现代主题的按压色，`showLiquidGlassDialog` 也要求旧类型的本地化。改为由公开 `LiquidGlassLens` 渲染按钮玻璃，官方现代 `Material`/`InkWell` 负责原有焦点、点击、按压和禁用交互；短确认仍使用公开 `LiquidGlassAlertDialog`，显式传入现有标题、正文样式，并通过现代 `showGeneralDialog` 展示，保留安全区、主题捕获、禁止遮罩关闭及缩放淡入。没有新增折射实现或私有导入。依据为 Dart MCP 读取的官方包实现、pub.dev 包元数据和 material_ui 迁移说明。官方推荐的 `MaterialUiCompatibilityBridge` 本身也已弃用，且不能完整映射项目按压主题，因此不引入全局兼容层。更新大字号测试的玻璃节点定位后，继续检查同样的文字边界；弹窗操作、长按高光、角色菜单和返回手势的原有断言全部保留。

工具状态：Dart MCP 项目根已注册，包文档与实现读取成功；连接旧 IDE 的 DTD 后未发现运行中的 App，首次连接临时 DTD 曾因进程结束被拒绝，热重载与运行时错误检查无可用目标。CLI 静态分析、宿主测试、双端构建和模拟器离线流程分别记录实际结果，不将无目标的 MCP 请求视为通过，也不触发收费通话。

## 2026-11-17：按官方国内实时目录选择 Qwen / 豆包音色

来源：Vidu 官方音色目录 https://platform.vidu.cn/vidu-stream/doc/voice-list 与实时版参数 https://platform.vidu.cn/vidu-stream/doc/s2-avatar/realtime/parameters 。核对公开页面载荷及页面供应商映射，国内目录为 ali→qwen_omni（56 个）、doubao3→doubao（293 个）；doubao2 为海外音色，async 为非实时音色。界面语言不改变 api.vidu.cn 区域。

必要性：旧选择器写死四个名称，分类按钮为占位，创建请求固定 qwen_omni，不能正确使用豆包。新增可复现的离线目录快照与生成脚本，记录日期/摘要，保留官方名称、场景、语言及原始 ID；列表惰性渲染并提供供应商与关键词筛选。官方缺少统一性别/试听元数据，不伪造性别分类或试听能力。替代方案：运行时抓官网会受网页变化、网络及鉴权边界影响；账号 voices 接口仅用于自定义音色，不能代替预置目录。本次无新增依赖或原生桥接。

Character 在既有 config JSON 增加 voiceProvider，旧记录默认为 qwen_omni；用户明确选择音色时原子更新 provider/voice，创建前校验组合，保持 persona、角色 ID、记忆分区不变。未在当前目录中的历史 Cherry/Chelsie 仅保留已保存偏好并提示可用性待确认，不擅自替换或宣称已验证。

官方要求音色与供应商匹配且会话创建后供应商不可变。豆包国内版 text_dialog 不支持、session_update 不支持修改 voice，因此界面说明文字聊天限制，保留语音与动作；应用层同样拦截文字聊天/通话换音色，不偷换为朗读、不发送无效命令。现有请求未传豆包不支持的 vad/llm。旧 Qwen 行为继续保留。

验证包含目录全部条目的请求映射、错误组合拦截、数据库重开、旧角色兼容、选择取消与搜索、供应商能力保护、布局与黄金图。Dart MCP 已连接正在运行的 iPhone 17 Pro 模拟器，热重载成功，runtime_errors 返回无错误；当前普通入口未启用 Flutter Driver 扩展，get_health 报不可用，页面交互改用独立离线集成入口验证，不为普通入口添加测试扩展。实际收费音色尚未逐个真机验证。


## 2026-11-17：按用户反馈恢复紧凑音色弹窗

用户要求音色弹窗沿用原页面风格，只保留简单列表。恢复原圆角半屏、紫色选中底色、渐变波形图标和行尾小型选择按钮；千问/豆包使用既有 AppButton 胶囊样式，取消 ChoiceChip。隐藏搜索、ID、语种、风格、计数及说明文字，官方目录和 provider/voice 原子保存、接口映射保持原实现。长列表继续惰性渲染，当前选择优先显示，支持大字号、小屏及无障碍选择状态。离线回归同步改为直接滚动选择，取消仍不修改旧音色；不触发收费 live。


## 2026-11-17：豆包头像与试听

按用户提供的 Speakers 列表将 VoiceType 精确匹配当前 293 个豆包音色，全部匹配 TrialURL 和 Avatar。将匹配项的公开地址保存为生成器输入，生成 trialUrl/avatarUrl；不手改生成文件，不保留原接口账号元数据。千问媒体待后续用户提供。紧凑列表不增加技术字段或说明，点击左侧头像试听，选择按钮仍只负责选择。

新增 audioplayers 6.8.1（锁定当前官方版本，MIT），通过 Dart MCP 阅读其 README、AudioPlayer 公开 play/UrlSource/stop/dispose/完成事件、audioplayers_darwin 6.5.0 Package.swift（原生 SPM，最低 iOS 13），并搜索源码确认音频上下文 API。来源：https://pub.dev/packages/audioplayers 、https://pub.dev/packages/audioplayers_darwin 。远端 GitHub 原文抓取被连接重置，改读 pub 官方发布包源码。必要性是无需 Key/Agora App ID 的独立媒体试听。现有 Agora 的混音需要 RTC 引擎上下文，会耦合通话资源及权限；自写原生桥接重复现有播放器能力，因此均不采用。保持 Agora 通话与 iOS SPM，不增加 Pods、后台音频模式或麦克风权限。

领域定义播放器端口，data 层包装官方插件，application 层处理单音频切换、晚到结果、失败及释放，Riverpod 暴露控制器和状态；UI 通过控制器操作，不直接调用原生播放器。播放器仅在点击试听时创建，音频使用 iOS playback / Android speech + transient focus；关闭、选择、分类切换及后台停止。自动测试离线注入假播放器/头像，原生模拟器验证使用临时合成 WAV，不读真实 Key、不创建收费 live。


## 2026-11-17：合并阿里试听音频

用户提供阿里 HTML 表格，按每行 code 精确匹配当前 voice_type，56 个千问音色全部匹配。用标准库 HTMLParser 解析 audio/src、data-src 和嵌套 source，重复相同链接去重，不猜测未匹配或多音频的地址。输入映射独立保存 ali_media.json，生成器同时合并两家媒体后生成 g.dart；阿里无头像，保留默认渐变图标，豆包头像和音频不变。复用已验证的 Riverpod 试听控制器与 audioplayers，无新依赖、桥接或权限。回归将千问从“不可试听”更新为检查实际 URL 播放及默认头像，保留无链接场景的能力保护；模拟器仍用假远程播放器及本地 WAV，不创建收费通话。

## 2026-11-17 选图后提前创建形象资产

按用户提供的图片上传文档及 [官方形象接口](https://platform.vidu.cn/vidu-stream/doc/image-upload)，选定相册照片后通过既有 `POST /live/v1/avatars` 创建资产，允许 name 为空，沿用带 MIME 前缀的 base64 image_uri。编辑资料期间后台预处理，当前图片返回的 ID 最终用于现有实时创建请求的 avatar.id；生成成功与角色文字校验仍是通话前提。本次不增加组件版或新依赖，不把“已上传”显示成“已就绪”，也不承诺实时会话零等待。

继续使用现有 Riverpod presentation 命令与仓储。仓储按角色、图片路径、来源和账号合并并发上传；通过事务校验当前图片/资产和凭证，仅合并资产字段，避免晚到响应覆盖新图、已保存的编辑或已删除角色。表单保存也保留同图后台已收到的 ID。上传中的提交等待同一请求，不重复 POST。页面关闭/后台停止前台轮询，已发出的请求仍处理晚到结果；切换账号或图片后不将结果绑定到当前角色。旧云端资产不自动删除，避免误删共享资源；本地保留原图，90 天保留期规则不变。

轮询采用三秒间隔、最多两分钟，终态停止，网络错误不自动重试；已有 ID 可以再次提交或刷新查询。POST 结果未知落为 uploadUnknown，阻止自动重发；高级设置保留查已有形象和显式重新创建。替代方案“选图后等上传完成才能编辑”会阻塞资料填写，“提交时才上传”不能提前处理图片，因此采用后台准备。离线测试使用假凭证、延迟响应、临时图片和内存数据库；模拟器请求走本地适配器，不创建真实资产或收费 live。

### 2026-11-18：角色仅在显式保存后进入首页

按用户确认的新交互，进入空白编辑页或点击推荐模板不再创建可见草稿。每次编辑使用独立仓储会话，将工作副本及提前上传状态保存在 Settings 的 characterEdit 命名空间，正式角色表只接收明确保存草稿或提交后的配置；不增加数据库迁移或依赖。表单无变化直接返回；有变化弹出沿用现有玻璃风格的“保存草稿 / 放弃修改 / 继续编辑”，恢复原字段值不算修改，选图、选音色及形象选择计入修改。编辑已有角色也使用工作副本，放弃后保留最后一次明确保存的配置。

上传仍在选图后开始，提交复用本次编辑的资产 ID。显式保存并离开时保留正在执行的请求上下文，晚到响应仅合并匹配图片、资产及账号的资产字段到已保存角色；放弃则删除编辑会话，晚到结果不得新增角色或覆盖原配置。已保存角色若被删除或换图，同样不得被旧结果恢复。会话结束后释放临时元数据，启动时清理上次中断的编辑会话；原图及云端形象不自动删除，避免误删共享资源。选择放弃不等于撤销已发送的云端请求；已有形象可通过既有列表重新选择。旧版本已保存的草稿不擅自批量删除。依据为本次用户确认、PRD CHAR-10/CHAR-11 和现有 Vidu 图片资产接口；替代方案“进入页面即保存”会污染首页，“返回即删角色”不能可靠恢复已有角色且容易与晚到响应竞争，因此不采用。

## 2026-11-18：Harness 构建副本的保守保留策略

用户指出运行目录重复保存 APK/iOS ZIP 且没有回收策略。核查现有 build 实现与本机产物后，增加独立 `gc` 预览/执行命令，并在耗时验证命令开始前自动执行。默认每平台保留最近十份，额外保护运行中、最新分类证据、发布/活动任务 pin、文本交接记录和跨报告依赖。锁内规划并复核候选；引用异常、未知状态及符号链接采用保守停止或保留。无新依赖、无原生或产品行为变化。

回收范围仅限 Harness 自己复制的 APK/ZIP；报告先标记证据过期再删除二进制，保留日志、截图、历史命令状态及摘要，验证器明确拒绝过期报告。这样可以追查旧执行结果，但不能在缺少原产物时继续宣称构建证据有效。来源为现有 `tool/harness.dart` 的产物/验证实现、Dart `FileLock` 和文件原子重命名 API；行为详见 HARNESS.md，回归在临时目录离线验证保护与失效边界。

替代方案：每次 `flutter clean` 会丢失增量缓存；整删 runs 会破坏诊断和被引用证据；只按天数或数量删除会误删发布版本。本次不采用这些方式。内容哈希 blob 去重能进一步减少相同产物，但需要另行迁移报告路径与校验协议，本次先落实可预览、可固定、可验证的保留清理。日志体积远小于构建副本，暂不自动删除，后续按实际增长评估分级策略。

### 同日调整：保留三份并回收过期运行目录

用户明确要求每平台改为最近三份，并清理无用历史。此指令取代上文的十份和永久保留全部日志策略：安装包保留三份，各命令/平台的诊断保留三轮，过期且未被引用的运行目录整体删除。诊断保留不再自动固定其中的安装包；汇总清单不充当 pin，只有仍保留的报告传播跨报告依赖。保留源码版本的最近结果，防止清掉失败后误用较早成功。目录删除前核对报告摘要并标为失效；缺失产物或已回收报告不能作为通过依据。

本轮同步删除已过时的本地探针、对照图、发布检查副本和交接记录，解除上一轮代理自动添加、已不需保留的旧调试构建 pin；保留当前任务、Skill 记录、正式文档、测试黄金图及近期证据。对已无对应进程且停留在 11 月 10 日的 running 记录，人工核对后标为中断，再纳入回收。另一次性清理旧 SDK 产生的过期 Flutter 构建目录、无用 Profile/Release 输出和重复安装包，常规自动 GC 仍限于 Harness 运行目录，不每次清空有效增量缓存。

## 2026-11-18：通话时长局部刷新

按用户要求，将 CallScreen 的每秒 setState 移入独立时间文字组件。页面经既有 Riverpod 控制器提供 Stopwatch 读取回调及运行状态，组件只在整秒值变化时刷新自己的 Text，复用原分秒格式、字色和等宽数字。业务计时仍由控制就绪时启动、结束清理时停止的 CallCoordinator Stopwatch 决定；定时器只负责界面采样，不按回调次数累加秒数，不改变创建、限时、计费或 RTC 生命周期。

时间采样与 presenceAnimationProvider 分离，关闭呼吸动画或系统减少动态效果仍正常显示时长。连接准备没有时间组件，结束中及终态取消采样，组件卸载释放定时器。已有状态变更仍按原 callProvider 更新页面，秒数变化不触发视频、背景和按钮 build。替代方案是把秒数广播到全局 CallSnapshot，但会使所有监听者每秒更新，因此采用最小范围的局部 State，无新依赖。离线回归通过可控时钟核对跨分钟、延迟采样、停止/卸载和重建范围，并保留既有黄金图与布局门槛。

## 2026-11-18：固化局部刷新与资源所有权规则

通话绿点原来在每次 build 中创建 CurvedAnimation，父控制器因此保留未移除的状态监听。改为使用已有的缓存 CurveTween 驱动链，保持透明度 0.4～1、单程 1400ms 和系统减少动态效果行为。离线回归覆盖连续二十次通话状态变化复用同一动画、呼吸效果和卸载；这与上面的计时局部刷新是两个独立修复。

按用户要求，将“最小刷新边界、资源明确所有者、同生命周期安全复用、对应解绑和释放”写入 AGENTS.md、xiaoyu-harness Skill 与 HARNESS.md 的执行审查步骤，并将已有 call_duration_test 加入必需测试清单。来源为本次重建/对象生命周期复现、Flutter 3.50 CurvedAnimation 构造/dispose、RenderAnimatedOpacity 的监听替换及 AnimationController.dispose 实现；官方 API：https://api.flutter.dev/flutter/animation/CurvedAnimation-class.html 、https://api.flutter.dev/flutter/animation/CurveTween-class.html 。

不采用“禁止所有页面重建”“缓存所有对象”或仅按关键字拦截 dispose 的方案：业务变化仍需刷新，普通 Widget 可重复构建，且资源可能由共享服务或异步生命周期持有。规则由日常审查与相关行为测试共同落实；现有静态门禁不能证明任意路径无泄漏，截图与 Skill 加载也不能代替运行证据。没有新增依赖、原生桥接或产品行为。

## 2026-11-18：已保存形象状态自动同步

用户报告编辑页已就绪但首页仍显示处理中，只有再次提交才更新。离线复现确认：首页只监听正式角色表，选图轮询随编辑页退出而停止；重新打开时新编辑会话的 published=false 又使云端进度仅写入临时副本。将用户表单的显式发布与云端资产客观进度分开：GET 状态只在图片、资产 ID、凭证均匹配时合并到已有正式角色，保留正式文本和音色；不新增角色，不发布新图片，终态不被晚到 processing 响应回退。旧编辑副本再次保存时采用同资产已有终态。

应用组合层持有一个 AvatarStatusSync，通过已有 Riverpod charactersProvider 和仓储 refresh 工作，复用页面的角色数据流，不额外订阅数据库；仅首页路由前台激活。每轮三秒、每角色/资产最多四十次，完成/失败、离开首页或后台停止，返回/恢复时立即补查并开启新窗口。无状态变化不写数据库，不为轮询 setState 或重建整页。并发引用同一账号和资产的 GET 在根仓储与编辑仓储之间共享，在途请求完成或失败即移除；查询完成后重新检查来源，避免删除、换图、换资产或账号后的旧结果覆盖。应用销毁移除路由监听、取消定时器和 Provider 订阅，已发出的 GET 可以完成但不能重新启动轮询。

依据为用户授权、PRD CHAR-10～12、已有 Vidu GET /live/v1/avatars/{id}，以及通过 Dart MCP 核对的 go_router 18.1.3 GoRouterDelegate/GoRouteInformationProvider 公开监听接口。初始化时等待非空路由配置再读取当前路由。不新增依赖、原生桥接、后台任务或收费创建；替代方案“永久后台轮询”“每张卡片独立 Timer”增加无用请求，“每次提交重新上传”则破坏资产复用，均不采用。离线测试覆盖自动完成、正式状态与未保存字段隔离、并发 GET 合并、失败有界重试、终态保护、生命周期及过期响应，设备流程额外验证首页自动核对已保存 processing 快照。

## 2026-11-18：通话时长由平台控制

按用户确认的 API 规则，单次会话最长 7200 秒，由服务到期主动关闭。移除 CallCoordinator 内写死的 10 分钟挂断计时器及其释放逻辑，不添加本地两小时计时器或时长设置；此决定取代早期 PRD 的默认 10 分钟及可选时长方案，也取代此前确认弹窗保留 10 分钟上限的描述。通话前中英文说明改为平台两小时上限。继续复用已有 type=6 平台结束事件、RTC 清理和 GET live 结束核对，不自动重建收费会话；本次不改变空闲超时和后台/锁屏结束策略。

来源为用户本次提供并确认的接口约束，以及现有实时版参数文档 https://platform.vidu.cn/vidu-stream/doc/s2-avatar/realtime/parameters 。离线回归用虚拟时间验证超过 10 分钟及到达两小时时客户端不会自行挂断，随后模拟平台结束通知验证资源释放与结束核对；不以该测试代替真实两小时云端验收。

## 2026-11-20：main 推送自动发布 Android APK

按用户要求增加 GitHub Actions 自动构建和 Releases 分发；用户当前没有 Apple 付费开发者账号，本次仅接入 Android。此要求取代此前文档中“无云端 CI”的现状描述，保留原有本地 Harness、离线测试和验收门槛。

来源：[GitHub push 事件](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#push)、[GitHub Actions Secrets](https://docs.github.com/en/actions/how-tos/security-for-github-actions/security-guides/using-secrets-in-github-actions)、[Flutter Android 发布与签名](https://docs.flutter.dev/deployment/android)、[GitHub 托管运行器](https://github.com/actions/runner-images)、[Flutter SDK 安装 Action](https://github.com/subosito/flutter-action)。第三方 Actions 固定到已查询的提交摘要，Flutter/Dart 沿用项目固定版本。

采用 macOS 15 完整检查、Linux 构建及独立发布任务：现有黄金图使用 macOS 苹方，不能因 Linux 字体不同而删除或跳过测试。缺少字体或检查失败直接停止发布。仅发布任务有 contents:write；签名 Secrets 只提供给构建步骤，签名文件不进入构建素材或仓库，Vidu 运行时凭证不进入 CI。发布先创建草稿，附件齐全后公开为预发布版本，标签和版本码按运行编号唯一生成。

未发现小遇专用正式签名，仅有通用 debug 密钥及另一项目签名；按用户“有则沿用、无则生成”的授权创建小遇专用 JKS，并保留本地私有记录。未配置签名时仅本地开发保留既有调试签名；CI 缺少 Secrets 必须失败，避免每次构建更换签名导致不能覆盖升级。此前调试签名的安装包需要卸载后安装新签名版本，文档说明本地数据影响。

替代方案：每次运行创建 debug 密钥会破坏覆盖升级；把签名文件放入公开源码不适合该仓库；直接在 Linux 上接受不同黄金图或跳过检查会降低验收门槛；每次 main 推送标为正式稳定版会混淆内测与正式发布。IPA 需要另行确定签名和分发条件，不能把未签名产物宣称为可直接安装的 iOS 安装包。

首次 GitHub 构建在字体定位步骤失败：运行器的苹方不位于原先假定的 Fonts/Font7 路径。改用系统 CoreText 的 CTFontCopyAttribute / kCTFontURLAttribute 查找真实注册路径，并遍历 AssetsV2 中的不同字体资产版本及隐藏字体文件；不下载或复制本机字体到公开仓库，不跳过黄金图。来源：[CoreText](https://developer.apple.com/documentation/coretext)、[CTFontCopyAttribute](https://developer.apple.com/documentation/coretext/ctfontcopyattribute(_:_:))。实际是否通过以新的 CI 检查为准。


按用户对 APK 打包范围的要求，将 Android 发布与完整 UI/Harness 验证拆成独立工作流。发布在 Ubuntu 执行格式、静态分析、签名准备及普通测试后构建签名 APK；macOS 保留完整生成校验、覆盖率门槛和黄金图对比，字体错误只影响 UI 验证状态。普通测试动态发现，仅将 golden_test.dart 路由到独立验证，不删除或禁用测试。替代方案：继续把 macOS 字体作为 APK 前置条件会阻塞无字体需求的构建；移除黄金图验证会丢失视觉回归检查。来源：[GitHub Actions 工作流语法](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions)。


按用户要求，Android 发布仅构建 arm64-v8a，使用 Flutter 官方 --target-platform android-arm64 --split-per-abi 参数，保留全部 Agora 扩展。附件标注架构，发布前检查 ZIP 内 lib 的架构集合恰为 arm64-v8a，防止意外恢复通用包。仅收集 app-arm64-v8a-release.apk。target-platform 限制 Flutter 编译目标，split-per-abi 同时过滤插件原生库；仅用前者仍会打入其他架构的 Agora 库。ARM64 分包版本码在基础值上加 2000，保留 Flutter 官方规则。替代方案：多架构通用包约 248 MiB，包含用户不需要的 ARM32/x86_64 原生库；裁剪 Agora 扩展另需功能验证，本次不做。来源：[Flutter Android 发布文档](https://docs.flutter.dev/deployment/android)及本机 flutter build apk --help。

按用户选择，新增 GitHub iOS 未签名 IPA 发布，macOS 15 使用 `flutter build ios --release --no-codesign` 和既有 SPM/Agora 依赖，不读取 Apple 私钥或描述文件。Flutter `build_ios.dart` 明确在 `build ipa --no-codesign` 时跳过 IPA 导出，因此用 CI 辅助脚本将真机 `Runner.app` 封装到 `Payload/Runner.app`，保留符号链接与可执行权限，并拒绝模拟器、缺少可执行文件及带主应用签名/描述文件的输入。产物及 Release 标注 unsigned，提供摘要，要求用户自行有效重签；不将构建通过等同重签安装或真实 RTC 验收。替代方案：TestFlight/Ad Hoc 需要另行提供账号、证书、描述文件及设备授权，不符合本次未签名选择；直接压缩 `.app` 根目录不是正确 IPA 布局。来源：[Flutter iOS 发布文档](https://docs.flutter.dev/deployment/ios)及本机 Flutter 3.50.0 的 `packages/flutter_tools/lib/src/commands/build_ios.dart`；无新增依赖或原生桥接。Dart MCP 包读取此前因未注册工程根目录不可用，使用本机 Flutter 与现有插件 SPM manifest 源码核对，未伪造工具或设备通过。


按用户最新要求，GitHub Actions 停止运行 UI、布局和黄金图测试，删除独立 UI 工作流及仅供 CI 使用的字体定位脚本；本地测试与完整 Harness 门槛保留。Android CI 选择 domain/application/data/presentation 和非布局 Harness 逻辑测试，不将虚拟时间业务测试误判为页面测试。此决定取代此前独立 macOS UI 工作流方案，避免把 CI 覆盖率文件误称完整 Harness 门槛通过。另修复 iOS 打包 lipo 参数顺序：输入文件必须在 -verify_arch arm64 之前，否则文件路径会被解析为架构名称。来源：GitHub Xcode 16.4 错误日志中的 lipo 使用说明及本机 xcrun lipo 检查。


按用户要求，将 Android 与 iOS 发布合并为一个 Mobile release 工作流。共享任务输出同一版本、标签和安装包文件名，逻辑检查只执行一次；Linux APK 与 macOS 未签名 IPA 并行构建，唯一发布任务依赖两端成功，收集两份安装包并生成联合 SHA256SUMS，再发布同一 Release。任一端失败不执行发布，重试同次运行复用标签。保留原 android-release.yml 路径及运行编号连续性，避免新工作流重置 Android 版本码；删除独立 iOS 工作流。替代方案：仅把两个独立发布任务放入同一 YAML 仍会创建两个 Release；复用标签但由两端分别公开会暴露暂缺另一端附件的版本。因此采用唯一汇总发布任务。来源：[GitHub Actions 工作流依赖语法](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#jobsjob_idneeds)。继续只发布 ARM64 APK、未签名 IPA，GitHub 不运行 UI 测试。
