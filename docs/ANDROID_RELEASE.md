# Android / iOS 自动发布

[返回 README](../README.md) · [开发指南](DEVELOPMENT.md)

## 发布流程

统一工作流 **Mobile release** 位于 [.github/workflows/android-release.yml](../.github/workflows/android-release.yml)，包含 Android APK 和 iOS 未签名 IPA。推送到 `main` 或在 Actions 页面手动运行都会触发：

1. Ubuntu 24.04 使用固定 Flutter 3.50.0 / Dart 3.14.0 检查格式、静态分析、CI 辅助脚本及逻辑测试，生成覆盖率数据。逻辑检查不依赖 macOS 或苹方字体。
2. 两端并行打包：Ubuntu 24.04 / JDK 17 使用仓库 Secrets 构建签名 `arm64-v8a` APK；macOS 15 使用 Swift Package Manager 构建并封装未签名 ARM64 IPA。
3. 两端都成功后，唯一的发布任务创建一个 GitHub 预发布版本，同时上传 APK、IPA 和包含两份摘要的 `SHA256SUMS.txt`。

Release 标签为 `v<pubspec版本>-build.<运行编号>`，固定对应本次源码提交。Flutter 基础版本码为 `1000 + GITHUB_RUN_NUMBER`，ARM64 分包另加 ABI 偏移 `2000`，最终为 `3000 + GITHUB_RUN_NUMBER`；同一次运行重试沿用标签并覆盖对应附件。新提交会取消同分支尚未完成的旧构建。

逻辑检查、Android 和 iOS 构建全部成功后才对用户公开 Release，任何一端失败都不会创建本次的完整发布。失败或取消的上传可能留下未公开草稿，不会把不完整版本作为可下载发布。检查日志和构建产物在 Actions 中保留 14 天，Release 附件独立保留。

## 验证范围

按用户要求，GitHub Actions 不运行 UI、布局、黄金图或设备测试，也不查找系统字体。共享逻辑测试覆盖 domain、application、data、presentation 及非布局 Harness 测试；使用 WidgetTester 虚拟时间但不构建页面的业务计时测试仍属于逻辑检查。UI 测试和完整 `dart run tool/harness.dart check` 保留在本地。CI 覆盖率文件仅供查看，不代表完整 Harness 的 80/60 门槛或 UI/设备验收通过。

## 一次性签名配置

在仓库的 **Settings → Secrets and variables → Actions → Repository secrets** 配置：

| Secret | 内容 |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | 小遇 JKS 签名文件的单行 Base64 |
| `ANDROID_STORE_PASSWORD` | JKS 存储密码 |
| `ANDROID_KEY_ALIAS` | 小遇密钥别名 |
| `ANDROID_KEY_PASSWORD` | 对应私钥密码 |

缺失或格式错误会使构建失败，不发布使用临时调试签名的 APK。固定签名用于后续覆盖升级，请妥善备份并沿用同一套密钥。

本次生成的专用签名保存在开发机 `~/.android/xiaoyu-release.jks`，对应的私有配置记录位于 `~/.android/xiaoyu-release-signing.json`。两者不进入仓库。记录文件用于配置上述四个 Secrets，密码和密钥值不应打印到日志。

签名配置由 [prepare_android_signing.py](../tool/ci/prepare_android_signing.py) 写入临时目录和被忽略的 `android/key.properties`，仅签名 APK；不会作为应用素材打包。任务结束时清理这两个临时文件。Vidu API Key 仍由用户在 App 中填写，不注入 CI 或安装包。

## 本地构建

开发机通过被忽略的 `android/key.properties` 指向专用签名；无此文件时保留原有本地调试签名兼容行为。

```sh
flutter pub get
flutter build apk --release --target-platform android-arm64 --split-per-abi
```

产物位于 `build/app/outputs/flutter-apk/app-arm64-v8a-release.apk`，发布附件名带 `-arm64-v8a` 后缀。CI 检查 APK 原生库目录仅包含该架构；保留全部 Agora 扩展，不支持 ARM32 或 x86_64 设备。正式分发必须确认已使用固定签名；自动发布流程强制要求四个 Secrets，并执行签名校验。

## 用户下载

在 [GitHub Releases](https://github.com/hsuehly/xiaoyu/releases) 选择最近的 Android 预发布版本，下载 `.apk`。支持 `arm64-v8a` 的 Android 8.0 及以上设备可安装，需要允许对应下载来源安装应用。

此前使用调试签名的版本无法被新正式签名覆盖，需要先卸载；卸载会删除应用本地角色和历史。后续同一正式签名的版本可正常覆盖升级。

APK 构建、签名和离线检查不证明真实 RTC、云端计费或设备视觉效果已经验收。当前为内测分发；[iOS 未签名 IPA](IOS_RELEASE.md) 在同一工作流构建并附于同一 Release，下载后需要自行重签安装。
